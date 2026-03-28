# SME Accounting Full Standard

Source: user-provided "中小型企业智能会计作业系统 / 全流程业务与决策执行规范（V3.0 Ultimate）".

## System Goal

Use standardized inputs, business semantic recognition, and hard constraints to complete bookkeeping aligned with PRC enterprise accounting standards.

Required outcomes:

- automatic accounting treatment
- automatic risk identification and grading
- reasonable and logically closed output

Mandatory principles:

- 不确定不入账
- 无依据不判断
- 有风险必提示
- 所有处理可追溯

## Mandatory Linear Order

环境初始化 → 数据采集 → 数据预处理 → 业务识别 → 决策判断 → 凭证生成 → 期末处理 → 对账校验 → 异常处理 → 报表生成 → 税务映射 → 结账

Do not advance when any step fails validation.

## Environment Initialization and Base Configuration

- Keep account-set data physically isolated by entity.
- Use standard first-level subjects.
- Do not use vague “other” for expense details; refine them.
- Bind current-account subjects to concrete counterparties.
- Split bank accounts by actual bank account number.
- Do not start posting until the base structure is complete.

## Data Collection and Penetrating Preprocessing

Input sources include:

- bank transactions
- bank receipts
- purchase and sales invoices
- payroll and social insurance data
- fixed asset lists

Normalize into:

- date
- amount
- counterparty name
- summary
- source

Penetrating recognition rule:

When the named counterparty is Alipay, WeChat, reserve fund, or another intermediary account:

- do not use it directly as the transaction entity
- parse receipt notes and restore the real counterparty

## Business Recognition and Confidence Filtering

Classify every transaction as one of:

- 销售回款
- 采购付款
- 费用支出
- 往来款
- 股东资金
- 税费
- 工资
- 不确定

Output confidence and basis.
If confidence is below threshold:

- do not generate voucher
- move into exception handling

## Counterparty Recognition and Unification

- match historical counterparties by name similarity
- infer attributes from transaction frequency and behavior
- do not batch-create new counterparties before business clarity exists

## Accounting Period Rules

Apply accrual basis:

- revenue by performance/completion time
- cost matched with revenue
- expense by actual occurrence period
- invoice is supporting evidence, not sole basis

If bank-flow time differs from business time, prefer business time.
Mark cross-period matters and propose adjustments.

## Accounting Decision Mechanism

Create multiple treatments and score them.
Priority weights:

- 发票依据
- 历史交易
- 主体性质
- 摘要信息

Select the optimal treatment.
If no treatment meets reasonableness requirements:

- do not post
- enter exception handling

## Amount Rationality and Abnormal Fluctuation Control

Trigger anomalies when:

- single amount is far above history
- expense/revenue ratio is abnormal
- revenue or cost sharply rises/falls
- long-term abnormal loss or profit appears

When triggered:

- mark risk level
- lower auto-processing priority

## Voucher Generation and Risk Isolation

- debit/credit must balance absolutely
- summary must reflect business substance

Hard isolation rules:

- shareholder funds without capital-increase evidence -> other payables
- revenue without invoice -> risk flag required
- non-operating expenditure -> other receivables (individual)

## Period-End Processing and Business-Chain Checks

Automatic tasks:

- carry-forward profit and loss
- accrue payroll
- accrue depreciation
- estimate income tax

Inventory and cost logic:

- paid but not invoiced -> provisional estimate or prepayment
- revenue and cost must match

Business-chain validation:

- sales require cost or inventory reduction
- purchases must enter inventory or expense
- payroll must match employees or social insurance

If the chain breaks:

- mark exception
- forbid close

## Bank Reconciliation and Adjustment

`银行余额 = 账面余额 + 调节项`

Adjustment items include:

- outstanding items
- in-transit funds
- third-party platform balances

Rules:

- bank balance is a validation benchmark, not the only truth
- every difference must be explainable
- if not explainable, do not close

## Exception Handling

Exception levels:

- low risk: auto process
- medium risk: confirmation required
- high risk: no auto process

For every exception provide:

- suggested treatment
- alternative treatment
- risk explanation

## Financial Statements and Tax Mapping

Required before report generation:

- balance sheet balances
- profit logic is coherent

Cross-period adjustment:

- identify cross-period invoices or revenue
- suggest prior-year profit and loss adjustment where appropriate

Tax mapping:

- generate tax declaration base tables automatically
- always allow review

## Close and Correction Rules

After close, do not modify directly.
Use red-entry reversal:

1. reverse original voucher
2. record correct voucher
3. rerun full validation flow

## Final Execution Principles

Always enforce:

- 不确定不入账
- 无依据不判断
- 有风险必提示
- 差异必须可解释
- 业务必须成链

## Added Module: Task Execution and Acceptance

### 12 Required Tasks

1. 环境初始化
2. 数据采集
3. 数据预处理
4. 业务识别
5. 往来主体归一
6. 会计决策判断
7. 凭证生成
8. 期末处理
9. 银行对账
10. 异常处理
11. 报表生成
12. 税务映射与结账

### Unified Execution Template

Every task must include:

- Input
- Process
- Output
- Action Guide
- Constraints

### Example Constraints

#### Data Preprocessing

- Input: raw bank flows and documents
- Output: normalized transaction data
- Action Guide: extract fields and penetrate third-party accounts
- Constraints: do not retain intermediary accounts as the final entity

#### Accounting Decision

- Input: transaction data + invoices + counterparty
- Output: optimal treatment plan
- Action Guide: generate multiple plans and score them
- Constraints: if no high-confidence plan exists, do not post

#### Bank Reconciliation

- Input: ledger balance + bank flow
- Output: reconciliation statement
- Action Guide: explain all differences
- Constraints: if a difference cannot be explained, do not close

## Final Acceptance Criteria

The system must satisfy all of the following:

### 1. Technical Correctness

- all vouchers balance
- report cross-checks hold

### 2. Data Consistency

- bank balance = ledger balance + reconciliation items
- current-account balances are traceable

### 3. Business Rationality

- revenue matches cost
- expense structure is reasonable
- no unexplained abnormal fluctuation

### 4. Risk Control

- all exceptions are flagged
- high-risk items are not auto-processed

### 5. Completeness

- every transaction is processed or suspended
- no data omission
