# financial-kuku

悟空财务（Wukong Accounting）的本地开发仓库，包含后端 Java 服务、前端 Vue、以及补充的 CLI Agent 接口。

## 修复原则

**如果 Web 上可以跑通、CLI 上不能跑通，改 CLI 的代码，不改后端。**

后端接口是 Web 和 CLI 共用的，改后端风险更大。CLI 应当复现 Web 端的数据获取策略（如额外调用辅助接口、解析 JSON 字段等）。

## 系统架构

这是一个双接口财务系统：

- **Web UI**：给人类用，Vue 前端 + Spring Boot 后端（`finance/`）
- **CLI**：给 Agent 用，Python CLI 封装同一套后端 REST API（`agent-harness/`）

Agent 使用说明（Skill）在：
```
agent-harness/cli_anything/wukong/skills/SKILL.md
```

CLI 安装：
```bash
pip install -e agent-harness/
```

CLI 运行（使用项目内虚拟环境）：
```bash
.venv-wukong/bin/cli-anything-wukong <command>
```

后端服务监听端口 `44316`。

## 构建方式

### 后端构建（必须用 Java 17）

系统默认 Java 可能是 25，Lombok 在 Java 25 下注解处理失效会导致大量编译错误。**必须显式指定 Java 17**：

```bash
JAVA_HOME=/opt/homebrew/Cellar/openjdk@17/17.0.18/libexec/openjdk.jdk/Contents/Home \
  mvn package -pl finance/finance-web -am -DskipTests
```

构建产物：`finance/finance-web/target/finance-web-0.0.1-SNAPSHOT.jar`

启动服务：
```bash
JAVA_HOME=/opt/homebrew/Cellar/openjdk@17/17.0.18/libexec/openjdk.jdk/Contents/Home
$JAVA_HOME/bin/java -jar finance/finance-web/target/finance-web-0.0.1-SNAPSHOT.jar --server.port=44316
```

> **注意**：不要用 `mvn clean`，会删除 target 目录。直接用 `mvn package` 增量构建即可。

### 前端构建

Node 版本需兼容（本机 Node 22，需加 legacy openssl 选项）：

```bash
cd ux
HUSKY=0 NODE_OPTIONS=--openssl-legacy-provider npm run build
```

构建产物在 `ux/dist/`，需手动复制到后端 JAR 的 `static/` 路径（参见下方"修改 JAR 内容"）。

### 修改 JAR 内容（代码改动后）

后端代码改完后，直接用上面的 Maven 命令重新构建即可，**不需要手动 patch JAR**。

## 目录结构

```
finance/          # Java Spring Boot 后端（含 Web 前端构建产物）
ux/               # Vue 前端源码
agent-harness/    # Python CLI + Agent Skill
  cli_anything/wukong/
    wukong_cli.py          # CLI 命令入口
    core/                  # 各模块请求封装
    skills/SKILL.md        # Agent Skill 文档
output/doc/       # 分析报告、问题定位文档
```

## 已知问题（output/doc/定位问题）

以下是通过 Agent 测试发现的已知 Bug，修改前请先阅读：

在文件：output/doc/定位问题 中。