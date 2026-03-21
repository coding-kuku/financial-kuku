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
    url: jdbc:mysql://127.0.0.1:3306/wk_open_finance?characterEncoding=utf8&useSSL=false&zeroDateTimeBehavior=convertToNull&tinyInt1isBit=false&serverTimezone=Asia/Shanghai&useAffectedRows=true&allowPublicKeyRetrieval=true
    username: root
    password: password
```

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

本项目里有历史 SQL 与 MySQL 8 的 `ONLY_FULL_GROUP_BY` 不兼容。
如果登录后出现账套查询异常、跳到 `#/noAuth`、或部分列表接口报 SQL 分组错误，先执行：

```bash
mysql -h127.0.0.1 -uroot -ppassword -e "SET GLOBAL sql_mode=(SELECT REPLACE(@@sql_mode,'ONLY_FULL_GROUP_BY',''));"
```

执行后重启应用，让新的数据库连接生效。

#### 检查 Redis

```bash
redis-cli -a 123456 -h 127.0.0.1 -p 6379 ping
```

---

## 9. 当前已完成的关键改造

- 已移除对悟空 ID 的依赖
- 已移除 `provider-1.0.1.jar`
- 已新增本地登录接口
- 已新增本地登录页 `local-login.html`
- 已新增本地用户表 `wk_admin_user`
- 已将前端预编译 JS 中的 `id.72crm.com` 跳转替换为 `/local-login.html`
- 已支持完全离线登录和本地部署

---

## 10. 备注

- 当前启动日志中有 Elasticsearch warning，但**不影响基础登录和主要试用流程**
- 如果后续涉及搜索、字段检索等功能异常，再补充启动 Elasticsearch 并完善其配置
