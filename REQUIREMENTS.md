# 悟空财务 —— 本地离线部署改造需求文档

## 背景

悟空财务（Wukong Accounting）是基于 Spring Boot 2.7.x + MyBatis-Plus 的开源财务系统。原始版本在认证层依赖悟空 ID（`id.72crm.com`），本地部署后仍需连接外部 OAuth2 服务，且前端 JavaScript 中硬编码了跳转地址，导致系统无法完全离线运行。

## 核心需求

**目标：去除对悟空 ID 认证服务的所有依赖，使系统可以 100% 本地离线部署和运行。**

业务功能（凭证录入、科目管理、期末结转、科目余额表、总账、明细账等）代码均已在仓库中，不需要改动。

---

## 改造范围与实现方案

### 1. 移除 `provider-1.0.1.jar` 依赖

**问题**：该 JAR 包含 `OAuthController`（处理 OAuth2 回调、颁发 token）、`UserAspect`（用户拦截）、`UserCacheUtil`（用户名缓存）等认证相关组件，并在启动时连接 `id.72crm.com`。

**实现**：
- 从 `finance/finance-web/pom.xml` 和 `common/common-web/pom.xml` 中删除 `provider-1.0.1.jar` 的 `<dependency>` 声明
- 同时从 `MANIFEST.MF` 的 `Class-Path` 中移除该 JAR 引用

**文件**：
- `finance/finance-web/pom.xml`
- `common/common-web/pom.xml`

---

### 2. 实现本地登录控制器（替换 OAuthController）

**问题**：原有登录流程为：前端 → 重定向到 `id.72crm.com` → OAuth2 授权码 → POST `/adminUser/authorization` → 颁发 token。需替换为本地用户名密码登录。

**认证机制**：系统内置的 `ParamAspect` 拦截所有 Controller 方法，读取请求头 `AUTH-TOKEN`，检查 `redis.exists(token + "_token")`，然后 `redis.get(token)` 取出 `UserInfo` 设入 ThreadLocal。登录接口只需按此格式写入 Redis 即可与现有拦截器兼容。

**实现**：新建 `LoginController.java`，提供以下接口：

| 接口 | 方法 | 说明 |
|------|------|------|
| `POST /login` | 用户名密码登录 | 查 `wk_admin_user` 表，验证 `sha256(password+salt)`，生成 UUID token 写入 Redis，返回 token |
| `POST /adminUser/logout` | 退出登录 | 删除 Redis 中的 token |
| `POST /adminUser/queryLoginUser` | 获取当前用户信息 | 从 ThreadLocal 读取 UserInfo 返回 |
| `POST /adminUser/authorization` | OAuth2 回调（存根） | 返回错误，本地模式不支持 |

密码哈希算法：`DigestUtil.sha256Hex(password + salt)`（Hutool）

Token 在 Redis 的存储格式（与 ParamAspect 兼容）：
```
redis.setex(token,          expireSeconds, userInfo)
redis.setex(token + "_token", expireSeconds, "1")
```

**文件**：`finance/finance-web/src/main/java/com/kakarote/finance/controller/LoginController.java`（新建）

---

### 3. 本地用户表与用户实体

**问题**：原系统没有本地用户表，用户信息全部来自悟空 ID 服务。

**实现**：
- 新建数据库表 `wk_admin_user`（见 `DB/wk_open_finance.sql`）
- 新建 MyBatis-Plus PO 实体 `LocalUser.java`
- 新建 `LocalUserMapper.java`（继承 `BaseMapper<LocalUser>`，无需 XML）

默认账号：`admin` / `123456`（哈希值 `sha256('123456wukong')`）

**文件**：
- `finance/finance-web/src/main/java/com/kakarote/finance/entity/PO/LocalUser.java`（新建）
- `finance/finance-web/src/main/java/com/kakarote/finance/mapper/LocalUserMapper.java`（新建）
- `DB/wk_open_finance.sql`（追加 `wk_admin_user` 表 DDL 和初始数据）

---

### 4. 替换 UserCacheUtil（用户名缓存工具）

**问题**：`provider-1.0.1.jar` 中的 `UserCacheUtil.getUserName(Long userId)` 被 3 个 ServiceImpl 引用，用于在凭证列表/日志中显示用户姓名。移除 JAR 后此类不存在。

**实现**：新建 `LocalUserCacheUtil.java`，使用 `@PostConstruct` + 静态 `ME` 字段模式实现静态方法调用，查询 `wk_admin_user` 表，并在 Redis 中缓存（TTL 1小时，键前缀 `LOCAL:USER:REALNAME:`）。

替换了以下文件中的调用（`import` 和方法调用全部替换）：
- `FinanceCertificateServiceImpl.java`（4处）
- `FinanceAccountSetServiceImpl.java`（2处）
- `AdminFileServiceImpl.java`（2处）

**文件**：`finance/finance-web/src/main/java/com/kakarote/finance/utils/LocalUserCacheUtil.java`（新建）

---

### 5. 修改 APPLICATION_ID.txt

**问题**：前端读取此文件内容作为 OAuth2 的 `client_id`，值为悟空平台注册的应用 ID。本地模式下不使用 OAuth2。

**实现**：将内容改为 `local`，前端在获取到非有效数字 ID 时会走本地模式（或直接被登录页重定向逻辑接管）。

**文件**：`finance/finance-web/src/main/resources/static/APPLICATION_ID.txt`

---

### 6. 修改前端预编译 JS（绕过 OAuth2 重定向）

**问题**：前端已编译为静态 JS（`app.f057b301.js`），其中硬编码了 `https://id.72crm.com/index.html` 作为未登录时的跳转目标，共 4 处。

**实现**：用 `sed` 直接替换编译后的 JS 文件，将所有 `https://id.72crm.com/index.html` 替换为 `/local-login.html`。

```bash
sed -i '' 's|https://id\.72crm\.com/index\.html|/local-login.html|g' \
  finance/finance-web/src/main/resources/static/static/js/app.f057b301.js
```

**文件**：`finance/finance-web/src/main/resources/static/static/js/app.f057b301.js`（已修改）

---

### 7. 新建本地登录页面

**问题**：需要一个简单的用户名密码登录页面，替代原来跳转到悟空 ID 的登录表单。

**实现**：新建静态 HTML 文件 `local-login.html`，功能：
- 表单提交到 `POST /login`
- 成功后将 token 存入 `localStorage['AUTH-TOKEN']`（JSON 格式）和 Cookie `AUTH-TOKEN`
- 自动重定向到 `/`（前端 SPA 入口）
- 支持回车提交、错误提示、加载状态

**文件**：`finance/finance-web/src/main/resources/static/local-login.html`（新建）

---

### 8. 清理 application.yml 中的悟空 ID 配置

**实现**：
- 删除 `wukong.ids.auth` 配置块（appId、clientId、clientSecret、requestUri、redirectUri）
- 将 Elasticsearch 地址从内网 IP `192.168.1.210:9200` 改为 `127.0.0.1:9200`，并移除认证信息（本地无密码 ES）

**文件**：`finance/finance-web/src/main/resources/application.yml`

---

## 本地部署步骤

### 前置依赖

| 服务 | 版本要求 | 本地端口 |
|------|---------|---------|
| MySQL | 8.x | 3306 |
| Redis | 6.x+ | 6379（密码 `123456`） |
| Elasticsearch | 8.5.x | 9200（可选，不影响核心财务功能） |
| Java | 17（LTS） | — |
| Maven | 3.6+ | — |

### 数据库初始化

```sql
CREATE DATABASE wk_open_finance CHARACTER SET utf8mb4;
USE wk_open_finance;
-- 执行 DB/wk_open_finance.sql
```

### 修改连接配置（如有需要）

编辑 `finance/finance-web/src/main/resources/application.yml`：

```yaml
spring:
  datasource:
    url: jdbc:mysql://127.0.0.1:3306/wk_open_finance?...
    username: root
    password: your_password
  redis:
    host: 127.0.0.1
    port: 6379
    password: 123456
```

### 构建

```bash
# 在项目根目录执行
mvn clean package -pl finance/finance-web -am -Dmaven.test.skip=true
```

### 启动

```bash
java -jar finance/finance-web/target/finance-web-0.0.1-SNAPSHOT.jar
```

访问 `http://localhost:44316`，使用账号 `admin` / `123456` 登录。

---

## 改造后的登录流程

```
用户访问 http://localhost:44316
    ↓ (未登录，前端检测到无 token)
    ↓ 重定向到 /local-login.html  （原来是跳到 id.72crm.com）
用户输入 admin / 123456
    ↓ POST /login
    ↓ 后端查 wk_admin_user，验证密码哈希
    ↓ 生成 UUID token，写入 Redis
    ↓ 返回 token
前端将 token 存入 localStorage['AUTH-TOKEN'] 和 Cookie
    ↓ 重定向到 /
前端后续所有 API 请求携带 AUTH-TOKEN 请求头
    ↓ ParamAspect 拦截，从 Redis 读取 UserInfo
    ↓ 正常进入业务逻辑
```

---

## 未改动的内容

- 所有财务业务逻辑（凭证、科目、期末结转、报表等）
- MyBatis-Plus 数据访问层
- `AccountSetAspect`（账套拦截器）
- `ParamAspect`（认证拦截器，无需修改，与新 Redis token 格式兼容）
- `wk_common_web-1.0.6.jar`（保留，提供 UserInfo、Redis 等基础类）
- `AdminServiceImpl`（原本已是本地空实现，无远程调用）
