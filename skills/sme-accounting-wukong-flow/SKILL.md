---
name: sme-accounting-wukong-flow
description: End-to-end bookkeeping and accounting decision skill for small and medium-sized enterprises using a strict, gate-based workflow from environment setup through data intake, preprocessing, transaction classification, voucher generation, period-end processing, reconciliation, reporting, tax mapping, and close. Use when Codex must execute or supervise Chinese SME accounting work, evaluate whether a transaction can be posted, control accounting risk, standardize voucher decisions, reconcile bank and ledger balances, or operate the Wukong accounting assistant system under explicit accounting rules.
---

# SME Accounting Wukong Flow

## Overview

Use this skill to convert raw accounting evidence into controlled bookkeeping actions.
Enforce hard accounting gates: if evidence is insufficient, confidence is low, risk is high, or balances cannot be explained, stop posting and move into exception handling.

## Core Principles

Always apply these principles:

- Do not post uncertain transactions.
- Do not judge without evidence.
- Always flag risk when risk exists.
- Keep every decision traceable.
- Require business chains to close logically.

## Workflow

Execute in this exact order and do not skip steps:

1. Initialize environment.
2. Collect source data.
3. Preprocess and standardize data.
4. Identify business nature and confidence.
5. Normalize counterparties.
6. Compare accounting treatments and choose the best plan.
7. Generate vouchers.
8. Run period-end processing.
9. Reconcile bank and ledger balances.
10. Handle exceptions.
11. Generate financial reports.
12. Map tax data and close the period.

Do not continue to the next step until the current step passes validation.

## Operating Model

For every task, structure work as:

- Input
- Process
- Output
- Action Guide
- Constraints

When presenting progress or results, keep this structure explicit so another agent or reviewer can audit the decision path.

## Decision Gates

### 1. Environment Initialization

Verify before any posting:

- Keep each entity physically isolated.
- Use standard PRC enterprise accounting subjects for first-level subjects.
- Refine expense detail subjects; do not use vague “other” expense buckets.
- Bind counterparties to receivable/payable and other current accounts.
- Split bank subjects by real bank account.

If the chart of accounts or auxiliary setup is incomplete, stop work.

### 2. Data Intake and Preprocessing

Accept inputs such as bank transactions, bank receipts, purchase/sales invoices, payroll and social insurance data, and fixed asset lists.
Normalize each record into at least:

- date
- amount
- counterparty
- summary
- source

If a payer/payee is an intermediary account such as Alipay, WeChat, or reserve funds, do not treat it as the final counterparty. Read the note or receipt details and restore the real business counterparty.

### 3. Business Identification

Classify each transaction into exactly one of:

- sales receipt
- purchase payment
- expense payment
- current account movement
- shareholder funds
- tax
- payroll
- uncertain

Output:

- classification
- confidence score
- evidence basis

If confidence is below the usable threshold, do not generate a voucher. Route it to exceptions.

### 4. Counterparty Normalization

Normalize names before using or creating auxiliary ledgers:

- match against historical names by similarity
- infer nature from transaction behavior and frequency
- do not bulk-create new counterparties before the business nature is clear

### 5. Accounting Period Attribution

Apply accrual accounting:

- recognize revenue by performance or business completion
- match costs with related revenue
- recognize expenses in the actual occurrence period
- treat invoices as evidence, not as the sole booking basis

If bank date and business date differ, prefer the business date.
Mark cross-period matters and propose adjusting entries.

### 6. Accounting Decision Comparison

Generate multiple treatments for each transaction and score them.
Use this priority order:

1. invoice or formal evidence
2. historical transaction pattern
3. counterparty nature
4. summary text

Choose the highest-quality reasonable treatment.
If no treatment is sufficiently reasonable, do not post.

### 7. Amount Reasonableness and Risk Control

Check for anomalies such as:

- single amount far above history
- abnormal expense-to-revenue ratio
- sudden revenue or cost spikes/drops
- sustained abnormal losses or profits

When triggered:

- mark risk level
- reduce automation priority
- require explanation before close

### 8. Voucher Generation

Require:

- debit and credit must balance exactly
- summary must reflect business substance
- treatment must respect risk isolation rules

Apply these hard rules:

- shareholder funds without capital contribution evidence -> book to other payables
- revenue without invoice -> allow only with explicit risk flag
- non-operating personal expenditure -> book to other receivables - individual

### 9. Period-End Processing

Run at period end:

- profit and loss carry-forward
- payroll accrual
- depreciation accrual
- income tax estimation

Also validate business-chain consistency:

- sales should have cost recognition or inventory reduction
- purchases should enter inventory or expense
- payroll should tie to employee or social insurance evidence

If the chain breaks, mark exception and forbid close.

### 10. Bank Reconciliation

Use:

`bank balance = book balance + reconciliation items`

Possible reconciliation items:

- outstanding items
- in-transit funds
- third-party platform balances

Treat bank balance as a strong validation anchor, not absolute truth.
Every difference must be explainable. If not explainable, do not close.

### 11. Exception Handling

Classify exceptions as:

- low risk: auto-handle allowed
- medium risk: confirmation required
- high risk: no auto-processing

For every exception, output:

- recommended treatment
- alternative treatment
- risk explanation

### 12. Reporting, Tax Mapping, and Close

Before reporting or close, verify:

- balance sheet balances
- profit logic is coherent
- cross-period items have adjustment suggestions
- tax declaration base data is generated but still reviewable

After close:

- do not edit directly
- reverse by red-entry method
- post the corrected voucher
- rerun all validations

## Enhanced Auto-Decision Rules

Apply these rules before deciding whether to post automatically, hold for review, or escalate.

### 1. Direction-First Rule

Always evaluate money direction before trusting summary text.

- If bank flow is incoming, first consider:
  - customer repayment
  - current-account return
  - deposit return
  - refund
- If bank flow is outgoing, first consider:
  - purchase payment
  - expense payment
  - payroll / tax / social security
  - transfer to intermediary funds

Do not let keywords such as “采购”, “货款”, or “用品” override cash direction by themselves.

Special handling:

- Incoming flow with procurement-like text may still be customer payment for the other party's purchase from the company.
- Outgoing flow with sales-like text may still be refund, commission, or current-account movement.

### 2. Evidence Layering Rule

Assign evidence into three layers and decide automation scope accordingly.

Layer A — direct evidence:

- invoice
- receipt or remittance advice
- payroll or social security statement
- order number
- stock-in or stock-out record
- known supplier or customer mapping

Layer B — semi-direct evidence:

- stable historical counterparty pattern
- merchant name extracted from Alipay, WeChat, or bank note
- prior confirmed treatment for the same pattern

Layer C — weak evidence:

- raw summary text only
- intermediary account name only
- natural-person counterparty without mapping
- generic wording such as “货款”, “用品”, or “消费”

Decision threshold:

- A plus matching direction -> auto-post allowed
- B only -> allow suggestion, usually hold unless pattern is stable and low-risk
- C only -> do not auto-post

### 3. Intermediary Account Penetration Rule

Never treat intermediary accounts as final counterparties.

Applicable names include:

- 支付宝（中国）网络技术有限公司客户备付金
- 微信支付
- 待报解预算收入
- 备付金
- platform settlement or clearing accounts

Required actions:

1. Parse note or remark for the real merchant or business clue.
2. Determine whether the flow is:
   - transfer to intermediary funds
   - final merchant purchase
   - tax or social security collection
   - unidentified platform clearing
3. Store both:
   - channel counterparty
   - penetrated real counterparty

If the real counterparty cannot be restored, hold the transaction.

### 4. Alipay and WeChat Two-Step Rule

For Alipay or WeChat related flows, evaluate in two steps.

Step 1: determine whether this is fund transfer or final consumption.

- If note indicates top-up, reserve, wallet, or generic merchant placeholder, prefer:
  - Dr Other Monetary Funds
  - Cr Bank Deposits
- If note identifies a concrete merchant or order, continue to Step 2.

Step 2: determine business nature.

- procurement goods -> accounts payable, inventory, or prepayment path
- office supplies, tools, or small consumables -> expense path
- fixed-asset-like or fit-out items -> long-term asset or deferred expense review
- still unclear -> hold

Do not expense Alipay or WeChat flows directly unless merchant and purpose are both sufficiently clear.

### 5. Natural-Person Counterparty Mapping Rule

If bank counterparty is a natural person, do not assume the natural person is the final supplier or customer.

Check in this order:

1. existing private-person-to-entity mapping table
2. same-date order or procurement records
3. historical confirmed voucher mapping
4. note, order number, or platform record

Classification:

- mapped to real supplier or customer -> use the mapped entity for accounting subject and auxiliary item
- repeated but still unmapped -> medium or high risk, hold
- one-off unmapped natural person -> high risk, hold

Do not auto-create a new supplier or customer from a natural person unless business evidence supports it.

### 6. Same-Day Merge Rule

Allow merging multiple bank rows into one voucher only when all conditions hold:

- same date
- same economic substance
- same final counterparty after penetration or mapping
- same accounting treatment
- explicit traceability from voucher back to all source rows

Typical merge cases:

- same supplier paid in multiple instalments on one day
- same merchant charged through multiple small deductions
- same platform merchant split across multiple payments

Record all source bank row IDs in the voucher digest or attachment note.

### 7. Procurement Payment Decision Rule

For outgoing flows marked as “货款” or equivalent, choose among three paths.

Path A — payable settlement

Use when goods are already received or payable basis exists.

- Dr Accounts Payable
- Cr Bank Deposits

Path B — prepayment

Use when payment occurs before receipt, invoice, or stock-in evidence.

- Dr Prepayments
- Cr Bank Deposits

Path C — hold

Use when supplier identity, purpose, or inventory relation is unclear.

Additional requirement:

- if later stock-in evidence appears, generate period-end or same-period conversion:
  - Dr Inventory or Expense
  - Cr Accounts Payable or Prepayments

### 8. Incoming Procurement-Word Rule

If an incoming bank flow contains procurement-like wording such as “采购服装”:

- do not classify as purchase automatically
- evaluate whether it means the other party purchased from the company
- if the company is the seller, prefer:
  - Dr Bank Deposits
  - Cr Accounts Receivable or revenue-related path depending on evidence stage
- if it is truly a supplier refund or current-account return, require supporting evidence

Incoming cash direction has priority over procurement wording.

### 9. Social Security Split Rule

For social security deductions, do not book a single undifferentiated expense by default.

Required inputs:

- social security declaration detail
- employer versus employee burden split
- period attribution

Preferred treatment:

- employer burden -> Dr payroll-related cost, expense, or accrued payroll liability path
- employee burden paid on behalf -> Dr Other Receivables or payroll clearing
- Cr Bank Deposits

If split detail is missing:

- hold or book to temporary clearing only when policy allows and traceability is preserved

### 10. Inventory Chain Completion Rule

When supporting records show goods and quantities, complete the business chain.

Bank payment alone does not finish the chain.
After confirming goods received:

- Dr Inventory
- Cr Accounts Payable or Prepayments

If quantity, SKU, or stock-in basis is missing, do not auto-generate the inventory entry.

### 11. Confidence Upgrade and Downgrade Factors

Upgrade confidence when:

- direction, merchant, purpose, and historical pattern all agree
- supplier or customer mapping exists
- order number or stock reference exists
- the same treatment was already confirmed in prior months

Downgrade confidence when:

- intermediary account is not penetrated
- natural person is not mapped
- direction and summary conflict
- summary is too generic
- no supporting document exists
- amount suggests asset-like purchase but period benefit is unknown

### 12. Output Requirements for Every Auto Decision

For each transaction, output:

- final classification
- confidence score
- evidence layer used
- whether counterparty was penetrated or mapped
- chosen treatment
- rejected alternatives
- source-row traceability
- reason if held

## Wukong System Operations

When actual bookkeeping actions must be executed in the accounting assistant system, open and follow:

- `agent-harness/cli_anything/wukong/skills/SKILL.md:1`

Use that reference for live command syntax, authentication, account-set switching, subject queries, certificate posting, ledger checks, and report retrieval.

Before any live operation in Wukong:

- confirm the correct account set
- prefer `--json` output for machine handling
- inspect subjects and voucher word before posting
- verify the next voucher number and posting date
- avoid destructive actions unless clearly required

After posting in Wukong:

- retrieve the created certificate or list results for verification
- run ledger or report checks tied to the same period
- compare system output with this skill's accounting gates

## Output Contract

For each batch or transaction, produce a concise auditable result containing:

- posting decision: post / hold / escalate
- business classification
- confidence and evidence
- chosen accounting treatment and rejected alternatives
- voucher lines or proposed voucher lines
- risk level and reason
- reconciliation impact
- next required action

## Validation Checklist

Do not consider the work complete unless all applicable checks pass:

- all vouchers balance
- bank balance differences are explained
- receivable and payable balances are traceable
- revenue and cost are matched
- expense structure is reasonable
- abnormal fluctuations are flagged
- high-risk items are not auto-posted
- every transaction is either processed or held

## References

Read these only when needed:

- `references/sme-accounting-standard.md:1` for the full source standard extracted from the user material
- `agent-harness/cli_anything/wukong/skills/SKILL.md:1` for concrete Wukong CLI operations
