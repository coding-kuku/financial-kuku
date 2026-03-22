# 悟空财务本地服务启动文档

本文档记录当前这套本地离线部署环境的关键启动信息，方便后续直接启动、登录和排查问题。

## 1. 当前环境

### Java

本机目前同时有两套 Java：

- **Java 8（Zulu）**
  - 路径：`/Users/czj/.local/java/zulu8.92.0.21-ca-jdk8.0.482-macosx_aarch64`
  - 已写入 `~/.zshrc`
- **Java 17（Homebrew）**
  - 路径：`/opt/homebrew/Cellar/openjdk@17/17.0.18/libexec/openjdk.jdk/Contents/Home`

> 本项目本次构建使用的是 **Java 17**。

如果当前终端还没加载环境变量，先执行：

```bash
source ~/.zshrc
```

### Maven

- 版本：`Apache Maven 3.9.14`
- 安装位置：`/opt/homebrew/Cellar/maven/3.9.14`

### MySQL

- 通过 Homebrew 安装
- 已启动：`brew services start mysql`
- 数据库名：`wk_open_finance`
- 用户：`root`
- 密码：`password`

### Redis

- 通过 Homebrew 安装
- 已启动
- 地址：`127.0.0.1:6379`
- 密码：`123456`
- DB：`12`

### Elasticsearch

- 已安装
- 当前应用可先不依赖它完成基础登录和试用
- 若后续字段搜索相关页面报错，再启动并补充配置

---

## 2. 代码与配置关键点

### 应用端口

`finance/finance-web/src/main/resources/application.yml`

```yaml
server:
  port: 44316
```

所以访问地址是：

```text
http://localhost:44316
```

### 数据库配置

当前配置：

```yaml
spring:
  datasource:
    url: jdbc:mysql://127.0.0.1:3306/wk_open_finance?characterEncoding=utf8&useSSL=false&zeroDateTimeBehavior=convertToNull&tinyInt1isBit=false&serverTimezone=Asia/Shanghai&useAffectedRows=true&allowPublicKeyRetrieval=true&sessionVariables=sql_mode='STRICT_TRANS_TABLES,NO_ZERO_IN_DATE,NO_ZERO_DATE,ERROR_FOR_DIVISION_BY_ZERO,NO_ENGINE_SUBSTITUTION'
    username: root
    password: password
```

> `sessionVariables=sql_mode=...` 已写入 URL，固定排除 `ONLY_FULL_GROUP_BY`，无需再手动执行 `SET GLOBAL sql_mode`。

### Redis 配置

当前配置：

```yaml
spring:
  redis:
    host: 127.0.0.1
    port: 6379
    password: 123456
    database: 12
```

JetCache 远程缓存配置：

```yaml
jetcache:
  remote:
    default:
      uri: redis://123456@127.0.0.1:6379/
```

---

## 3. 数据初始化

数据库初始化 SQL：

```text
DB/wk_open_finance.sql
```

当前已经执行完成，包含：
- 全部业务表结构
- 新增的本地登录用户表 `wk_admin_user`
- 默认管理员账号
- 默认本地账套、账套用户绑定、系统参数初始化数据

默认管理员账号：

- 用户名：`admin`
- 密码：`123456`

默认初始化账套数据：

- 默认账套：`本地测试账套`
- 默认期间：`2026年第03期`
- 默认管理员已绑定到该账套，且为默认账套用户
- 已初始化 `wk_finance_parameter`，避免首页/报表页出现 `Invalid date` 或登录后反复刷新

---

## 4. 构建命令

项目已验证可成功构建，推荐使用 **Java 17**：

```bash
JAVA_HOME=/opt/homebrew/Cellar/openjdk@17/17.0.18/libexec/openjdk.jdk/Contents/Home \
mvn clean package -pl finance/finance-web -am -Dmaven.test.skip=true
```

构建成功后产物位置：

- 可执行 JAR：
  ```text
  finance/finance-web/target/finance-web-0.0.1-SNAPSHOT.jar
  ```
- 打包压缩包：
  ```text
  finance/finance-web/target/finance-web.tar.gz
  ```

---

## 5. 启动命令

### 方式一：直接启动后端

```bash
JAVA_HOME=/opt/homebrew/Cellar/openjdk@17/17.0.18/libexec/openjdk.jdk/Contents/Home \
java -jar finance/finance-web/target/finance-web-0.0.1-SNAPSHOT.jar
```

### 方式二：后台启动

```bash
JAVA_HOME=/opt/homebrew/Cellar/openjdk@17/17.0.18/libexec/openjdk.jdk/Contents/Home \
nohup java -jar finance/finance-web/target/finance-web-0.0.1-SNAPSHOT.jar >/tmp/wukong-finance.log 2>&1 &
```

当前会话实际使用的是后台启动方式。

---

## 6. 服务启动命令

### 启动 MySQL

```bash
brew services start mysql
```

### 启动 Redis

如果仅用 Homebrew 默认方式启动：

```bash
brew services start redis
```

但当前为了匹配项目配置中的密码，实际 Redis 是按如下方式重启过的：

```bash
printf 'port 6379
bind 127.0.0.1
requirepass 123456
protected-mode yes
daemonize no
' > /tmp/redis-wukong.conf

brew services stop redis
redis-server /tmp/redis-wukong.conf >/tmp/redis-wukong.log 2>&1 &
```

验证 Redis：

```bash
redis-cli -a 123456 -h 127.0.0.1 -p 6379 ping
```

返回：

```text
PONG
```

---

## 7. 页面访问

启动成功后访问：

```text
http://localhost:44316
```

登录页已改为本地页面，不再跳转悟空 ID。

登录账号：

- 用户名：`admin`
- 密码：`123456`

---

## 8. 日志与排查

### 应用日志

```text
/tmp/wukong-finance.log
```

查看最近日志：

```bash
tail -80 /tmp/wukong-finance.log
```

### Redis 日志

```text
/tmp/redis-wukong.log
```

### 常见检查

#### 检查应用端口是否已监听

```bash
nc -z 127.0.0.1 44316 && echo ok
```

#### 检查 MySQL

```bash
mysql -h127.0.0.1 -uroot -ppassword -e "SHOW DATABASES LIKE 'wk_open_finance';"
```

#### 检查 MySQL `sql_mode`

`ONLY_FULL_GROUP_BY` 兼容问题已通过在 JDBC URL 中写入 `sessionVariables=sql_mode=...` 固定解决，**无需手动执行 `SET GLOBAL sql_mode`**。

如果需要确认当前连接的 sql_mode，可查询：

```bash
mysql -h127.0.0.1 -uroot -ppassword -e "SELECT @@SESSION.sql_mode;"
```

预期输出中不应包含 `ONLY_FULL_GROUP_BY`。

#### 检查 Redis

```bash
redis-cli -a 123456 -h 127.0.0.1 -p 6379 ping
```

---

## 9. 当前已完成的关键改造

**基础离线化（第一轮）**
- 已移除对悟空 ID 的依赖，移除 `provider-1.0.1.jar`
- 已新增本地登录接口（`/login`、`/adminUser/logout`、`/adminUser/queryLoginUser` 等）
- 已新增本地登录页 `local-login.html`
- 已新增本地用户表 `wk_admin_user`，默认账号 `admin/123456`
- 已新增本地 `UserStrategy` 实现 `LocalUserStrategy`，用于将登录用户绑定到 `UserUtil` 的 ThreadLocal 上下文
- 已将前端预编译 JS 中的 `id.72crm.com` 跳转替换为 `/local-login.html`

**认证与账套上下文修复**
- `ParamAspect`：修复空 UserInfo 绕过 null 检查的 bug，增加登录接口豁免
- `LocalUserStrategy`：在单机离线模式下为 `UserUtil.setUser/getUser/removeUser` 提供本地 ThreadLocal 存储实现
- `AccountSetAspect`：增加 Redis 兜底恢复用户信息，修复账套为空时的错误处理

**SQL 兼容性修复**
- MySQL JDBC URL 加入 `sessionVariables=sql_mode=...`，固定排除 `ONLY_FULL_GROUP_BY`
- `FinanceAccountSetMapper.xml`：修复 `GROUP BY` 聚合违规（`is_founder`、`is_default`、`GROUP BY` 列补全）
- `FinanceCertificateMapper.xml`：修复两处明细账/余额表查询的 `GROUP BY` 违规

**报表兼容性修复**
- `FinanceReportRequestBO`：新增自定义 JSON 反序列化，兼容旧前端发送的字符串型 `type`（`"MONTH"→1`、`"QUARTER"→2`）
- `FinanceCashFlowStatementReportImpl` / `FinanceIncomeStatementReportServiceImpl`：平衡校验增加 null 守卫

**账套与科目修复**
- `FinanceAccountSetServiceImpl`：`companyCode` 空值回退，`saveBatch` 逐条写入
- `FinanceAccountUserServiceImpl`：`financeAuth()` 改用 `adminRoleService.auth()`，对齐前端权限树
- `FinanceSubjectServiceImpl`：科目复制和最小值查找的 null/空集合守卫

**前端 chunk 修复**
- `index.html`：webpack chunk hash map 补全 `chunk-5f4fcffe`（核算项目明细账）和 `chunk-0927bf12`（核算项目余额表）两个缺失条目，修复点击无响应问题
- `chunk-392f2abc`、`chunk-fe0f7034`：报表请求 `type:"MONTH"` 改为 `type:1`
- `chunk-71c3c0d5`：账套管理操作改为显示错误提示

**API 参数兼容**
- `FinanceCurrencyController.queryListByAccountId`：`accountId` 改为可选，缺省从账套上下文读取
- `FinanceCertificateController.queryLabelName`：`adjuvantId` 改为可选，防止前端 watcher `immediate:true` 触发时报 500
- `AdminFileServiceImpl`：文件下载 domain 补全前导 `/`

---

## 10. 临时公网访问（Cloudflare Tunnel）

如果本机服务运行在 `127.0.0.1:44316`，且当前机器没有公网 IP，可直接使用 Cloudflare 的 quick tunnel 临时暴露到公网。

### 安装

当前本机已通过 Homebrew 安装：

```bash
brew install cloudflared
```

如果 PATH 未生效，也可直接使用绝对路径：

```bash
/opt/homebrew/opt/cloudflared/bin/cloudflared
```

### 启动临时公网隧道

```bash
cloudflared tunnel --url http://127.0.0.1:44316
```

或：

```bash
/opt/homebrew/opt/cloudflared/bin/cloudflared tunnel --url http://127.0.0.1:44316
```

启动后终端会返回一个 `https://*.trycloudflare.com` 的临时公网地址，外部可直接通过该地址访问本机服务。

本次实际生成过的示例地址：

```text
https://explicit-holly-expand-actors.trycloudflare.com
```

> 该地址仅作示例，quick tunnel 每次启动后生成的域名通常都会变化。

### 说明

- 该方式**不需要公网机**
- 适合临时演示、临时调试、短时间对外访问
- 只要本地 `cloudflared` 进程还在运行，公网地址通常就可继续使用
- 但 quick tunnel **没有稳定性保证，也没有固定有效时长承诺**
- 如果本机休眠、断网、终端结束或进程退出，公网访问会中断

### HTTPS 场景

如果本地服务本身是 HTTPS，可改为：

```bash
cloudflared tunnel --url https://127.0.0.1:44316
```

---

## 11. 备注

- 当前启动日志中有 Elasticsearch warning，但**不影响基础登录和主要试用流程**
- 如果后续涉及搜索、字段检索等功能异常，再补充启动 Elasticsearch 并完善其配置
