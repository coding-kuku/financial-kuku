# financial-kuku

悟空财务（Wukong Accounting）的本地开发仓库，包含后端 Java 服务、前端 Vue、以及补充的 CLI Agent 接口。

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

### 1. `ledger balance` 时间参数格式不一致
CLI 定义 `--start/--end` 为 `YYYY-MM-DD`，但后端 `/financeCertificate/queryDetailBalanceAccount` 按会计期间 `yyyyMM` 解析，传入日期格式会 500。
- CLI 参数：`wukong_cli.py:793-796`，`core/ledger.py:76-81`
- 后端：`FinanceCertificateServiceImpl.java:632-667`

### 2. `report balance-sheet --check` 把辅助核算编号当数字解析导致 500
辅助核算科目的 `number` 字段会拼入卡片编号如 `1122_C0002`，过滤逻辑剥掉下划线后执行 `new BigDecimal("1122C0002")` 抛异常。
- `FinanceBalanceSheetReportServiceImpl.java:516-593`
- `FinanceCertificateServiceImpl.java:1152-1216`（关键行 1174-1178）
- `RuleUtils.java:72-106`

### 3. 父科目直接记账的余额被漏算
只要科目有子科目，报表和余额汇总就只走"汇总子科目"分支，父科目本身的直营余额被丢弃。
- `FinanceBalanceSheetReportServiceImpl.java:301-370`、`404-475`
- `FinanceCertificateServiceImpl.java:2968-3132`（关键分支 2972-2975）

### 4. 凭证录入新增二级科目——"编码重复"误报
前端 `SubjectUpdateDialog.vue` 推导父科目 `category` 时只取第一个，导致非首类别父科目下新建子科目时 `category` 传错；后端校验"类别/类型不一致"时却抛 `FINANCE_SUBJECT_NUMBER_ERROR`（编码重复），造成双重误导。
- 前端：`SubjectUpdateDialog.vue:639-701`
- 后端：`FinanceSubjectServiceImpl.java:115-130`；正确错误码应为 `FinanceCodeEnum.java:41`

### 5. `account create` 命令不可用
CLI 命令定义了 4 个参数但底层方法只接受 2 个，直接抛 `TypeError`。
- `wukong_cli.py:356-375`，`core/account.py:32-52`

### 6. `account switch` 切换后后续查询仍落在原账套
CLI 本地 session 更新，但后端账套上下文不同步，切换结果不可信。
- `core/account.py:27-30`，`FinanceAccountSetServiceImpl.java:443-455`

### 7. `certificate update` 返回 500（TooManyResultsException）
更新前的判重查询 `queryByTime` 没有限制 `account_id`，同月同凭证字有多张时 `selectOne()` 抛异常。
- `FinanceCertificateServiceImpl.java:152-185`（判重 SQL：`FinanceCertificateMapper.xml:1446-1456`）

### 8. `account init` 文案与实际行为不一致（高风险）
帮助文案写"初始化默认数据"，实际调用 `/financeAccountSet/initFinanceData` 会**全表清空**所有财务数据。
- `wukong_cli.py:377-388`，`core/account.py:79-85`
- 后端：`FinanceAccountSetServiceImpl.java:476-486`

### 9. `certificate add/update` 帮助文案贷方字段名错误
文案写 `ownerBalance`，实际 CLI 只识别 `creditBalance`，按文案操作会导致贷方金额为 0 的校验错误。
- `wukong_cli.py:667-672`、`757-762`

### 10. `certificate get` 返回的 `checkStatus` 不可信
详情接口 `checkStatus` 与列表筛选实际状态不同步，不能作为审核状态判断依据。
- 后端详情：`FinanceCertificateServiceImpl.java:382-427`

### 11. `ledger general` 对有数据的科目返回空数组
后端 `/financeCertificate/queryDetailUpAccount` 存在可用性问题，明细账有数据但总账返回空。
- `FinanceCertificateServiceImpl.java:487-536`，SQL：`FinanceCertificateMapper.xml:508-620`

### 12. ~~Skill 文档 `adjuvant add --label` 示例错误~~ ✓ 已修复
WUKONG.md 示例已改为整数（`--label 4`），并附上枚举说明。

### 13. `certificate next-num` 返回值不可信
CLI 把日期规范成 `yyyyMM` 传给后端，但后端 SQL 用 `DATE_FORMAT` 解析纯期间字符串不稳定，始终返回 `1`。
- `core/certificate.py:216-237`，SQL：`FinanceCertificateMapper.xml:1446-1456`

### 14. `certificate get` 返回字段不完整
详情接口只返回基础 PO，缺少 `voucherName`、`voucherNum`、明细行 `subjectName` 等展示字段，与列表接口不一致。
- `FinanceCertificateServiceImpl.java:382-427`（对比列表补全逻辑 `240-287`）

### 15. 凭证字新增接口允许重名
同一账套下可创建同名凭证字，无唯一校验。

### 16. `report cash-flow --check` 返回 500
现金流量表校验直接复用资产负债表校验链路，后者存在 Bug 时一并 500。
- `FinanceCashFlowStatementReportImpl.java:274-286`
