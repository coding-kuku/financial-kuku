# 悟空财务 —— 原系统 Bug 修复记录

本文档记录在离线部署改造过程中发现并修复的原有系统 bug。

---

## Bug 1：结转损益凭证 `voucher_id` 初始化为 NULL，导致生成凭证报 500、删除结转凭证失败

### 现象

1. `/#/fm/settleAccounts` 点击"生成凭证"，前端显示「网络错误，请稍候再试」，但凭证实际已生成。
2. 在凭证查询页面删除结转凭证，同样报「网络错误」，且凭证实际**未被删除**（普通凭证可正常删除）。

### 根因分析

#### 第一层：事务隔离导致结转损益模板 `voucher_id` 落库为 NULL

账套初始化链路：

```
FinanceAccountSetServiceImpl.saveAndUpdate()  // @Transactional 外层事务开始
  └─ initMethod(accountId)                    // 独立 JDBC 连接，commit 后返回，在外层事务快照之外
  └─ AccountSet.setAccountSet()
  └─ commonService.init()                     // 仍在外层 Spring 事务中
       └─ statementService.init()             // FinanceStatementServiceImpl.init()
```

`initMethod` 使用原始 JDBC 连接执行 `init.sql`（插入 记/收/借/付 凭证字），在外层 Spring 事务开启**之后**单独提交。

`statementService.init()` 在同一外层 Spring 事务中运行。MySQL InnoDB 默认 **REPEATABLE_READ** 隔离级别下，外层事务只能看到事务开始时的快照，无法看到 `initMethod` 之后提交的新行。

因此，`statementType = 2`（结转损益）在初始化时查询当前账套凭证字返回空，`voucher_id` 被静默写入 `NULL`。

#### 第二层：空 `voucher_id` 在两条链路上各自引发问题

**生成结转凭证（报 500，但实际已生成）**

`incomeStatement()` 将 `statement.getVoucherId()`（NULL）设置到 `FinanceCertificateBO` 上，凭证写入成功后，`@OperateLog` AOP 在后处理阶段尝试序列化 operation object 时遭遇空引用，抛出异常，返回 HTTP 500。数据已落库，只是响应码是 500。

**删除结转凭证（彻底失败）**

`FinanceCertificateServiceImpl.deleteByIds()` 构建操作日志时：

```java
FinanceVoucher voucher = financeVoucherService.getById(certificate.getVoucherId()); // voucherId 为 NULL，返回 null
operationLog.setOperationObject(... voucher.getVoucherName() ...);                   // NullPointerException
```

NPE 导致事务回滚，`removeByIds(ids)` 未执行，凭证未被删除。

### 修复方案

#### 1. `init.sql` 新增"转"凭证字

**文件**：`finance/finance-web/src/main/resources/init.sql`

新建账套初始化时追加：

```sql
INSERT INTO `wk_finance_voucher` (...) VALUES ({autoId}, '转', '转账凭证', '0', NULL, {userId}, '{createTime}', {accountId});
```

结转损益本应使用"转账凭证"，而非默认的"记账凭证"。

#### 2. `FinanceStatementServiceImpl.init()` 使用 `REQUIRES_NEW` 事务，并显式绑定"转"凭证字

**文件**：`finance/finance-web/src/main/java/com/kakarote/finance/service/impl/FinanceStatementServiceImpl.java`

**事务修复**：`init()` 加 `@Transactional(propagation = Propagation.REQUIRES_NEW)`。

`statementService.init()` 是通过 `ApplicationContextHolder.getBean()` 经 Spring AOP 代理调用的，`REQUIRES_NEW` 会暂停外层事务、开启新快照，新快照在 `initMethod` 提交之后建立，因此可以看到刚插入的"转"凭证字。这符合两阶段初始化的语义：`initMethod` 和 `statementService.init()` 本来就不是同一原子操作。

**逻辑修复**：`statementType = 2` 初始化时，不再查默认凭证字，改为按名称显式查找"转"凭证字。查不到则直接抛错，不允许写入 NULL。

新增辅助方法：

```java
private static final String TRANSFER_VOUCHER_NAME = "转";

private Long getTransferVoucherId() {
    FinanceVoucher financeVoucher = financeVoucherService.lambdaQuery()
            .eq(FinanceVoucher::getAccountId, AccountSet.getAccountSetId())
            .eq(FinanceVoucher::getVoucherName, TRANSFER_VOUCHER_NAME)
            .one();
    if (financeVoucher == null) {
        throw new CrmException(SystemCodeEnum.SYSTEM_ERROR);
    }
    return financeVoucher.getVoucherId();
}
```

#### 3. `incomeStatement()` 入口添加前置校验

在生成结转凭证链路的入口校验 `voucherId` 非空，防止历史脏数据再次触发 500：

```java
private void ensureTransferStatementVoucher(FinanceStatement statement) {
    if (statement != null && Integer.valueOf(2).equals(statement.getStatementType())
            && statement.getVoucherId() == null) {
        throw new CrmException(SystemCodeEnum.SYSTEM_ERROR);
    }
}
```

### 影响范围

- 只影响新建账套的初始化流程，历史账套数据不修改。
- 历史账套若已存在 `voucher_id = NULL` 的结转损益模板，需人工为其补填"转"凭证字，之后方可正常生成/删除结转凭证。
- 历史已生成的空 `voucher_id` 结转凭证，删除时仍会失败（历史数据问题，不在本次修复范围内）。

### 变更文件

| 文件 | 改动说明 |
|------|---------|
| `finance/finance-web/src/main/resources/init.sql` | 新增"转"凭证字初始化行 |
| `finance/finance-web/src/main/java/com/kakarote/finance/service/impl/FinanceStatementServiceImpl.java` | `init()` 加 `REQUIRES_NEW`；改用"转"凭证字显式绑定；入口加前置校验 |

---

## 注

以上 bug 均存在于 `opensource-baseline` 分支的原始代码中，不是离线部署改造引入的。
