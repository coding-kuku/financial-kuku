---
name: sme-accounting-wukong-flow
description: End-to-end bookkeeping and accounting decision skill for small and medium-sized enterprises using the V2 structured workflow for inputs, preprocessing, classification, voucher generation, reconciliation, reporting, tax mapping, and Wukong system operations.
---

# SME Accounting Wukong Flow

## Overview

Use this skill to convert raw accounting evidence into controlled bookkeeping actions.
Enforce hard accounting gates: if evidence is insufficient, confidence is low, risk is high, or balances cannot be explained, stop posting and move into exception handling.

## Core Principles

- do not post uncertain transactions
- do not judge without evidence
- always flag risk when risk exists
- keep every decision traceable
- require business chains to close logically

## Input Requirements

### 1. Required Input Types

For any bookkeeping task, require at least:

- bank transaction data
- invoice support for each transaction, including sales invoices, purchase invoices, or other invoice evidence matching the flow when applicable

Also require the following when applicable:

- payroll data when the bank flows involve payroll-related transactions and the nature cannot be determined clearly from the existing evidence
- social security data when the bank flows involve social-security-related transactions and the nature cannot be determined clearly from the existing evidence
- other supporting data for any bank flow whose business nature cannot be determined clearly from the existing evidence

### 2. Accepted Input Types

Accept inputs such as:

- bank transactions
- bank receipts
- purchase invoices
- sales invoices
- payroll data
- social insurance data
- fixed asset lists
- inventory or stock movement records
- ledger totals or historical ledger balances
- user statements or user-confirmed business facts

### 3. Input Submission Requirements

Each task should also clearly provide:

- entity name
- target period or date scope
- source traceability sufficient to link each decision back to the original evidence

When live bookkeeping actions must be executed in Wukong, also provide:

- the correct account set

### 4. Minimum Required Fields

Normalize each record into at least:

- date
- amount
- counterparty
- summary
- source

When working from raw bank-statement data, also keep full source traceability back to the original file, sheet, and row.

### 5. Input Sufficiency

Do not hold transactions by category alone.
Decide based on whether the minimum information required for a defensible accounting treatment is available.

Minimum sufficient facts must support all of:

- money direction is clear
- period attribution is usable
- business nature is identifiable
- counterparty role is identifiable
- subject path is reasonably determined
- risk can be stated explicitly in the output

If the minimum sufficient facts are available, post.
If the minimum sufficient facts are not available, hold.
If a batch contains both clear and unclear transactions, post the clear subset first and hold only the unclear subset.

Avoid both failure modes:

- over-posting uncertain flows
- over-holding flows that are already determinable

### 6. Missing Input Handling

When a transaction cannot be posted, ask only for the minimum additional information required to make it postable.
Do not ask for broad document sets unless they are actually necessary.
Use the smallest fact set that resolves the accounting decision.

Typical minimum missing information by transaction type:

- payroll:
  - employee identity
  - payroll month
  - whether the bank amount is net pay
  - whether payroll accrual already exists
- social security:
  - contribution month
  - employer burden
  - employee burden
  - whether housing fund or tax is included
- natural-person counterparty:
  - person identity
  - relationship to the company
  - business nature of the payment
  - whether the person is acting on behalf of an entity
- incoming flow of unclear nature:
  - whether it is revenue, refund, current-account return, or shareholder funds
  - related customer or supplier if any
  - whether performance or delivery has occurred if revenue is claimed
- refund or return flow:
  - which original payment or transaction it relates to
  - whether the original nature was purchase, expense, deposit, or current account

### 7. User-Confirmed Facts

Do not require formal documents if the user has already provided enough concrete business facts to determine the treatment with acceptable risk.

Treat explicit user confirmation as usable evidence when it clearly states:

- who the counterparty is
- what the money is for
- which period it belongs to
- whether it is income, expense, payroll, social security, refund, current account, or shareholder funds
- any key split needed for posting, such as employer versus employee burden

When relying on user-confirmed facts:

- record that the treatment is based on user confirmation
- keep the transaction traceable to the bank row
- still hold the transaction if the user statement remains materially ambiguous

Do not use blanket rules such as:

- all payroll must be held
- all social security must be held
- all natural-person flows must be held
- all unclear incoming flows must be held

These categories may be posted when the user-supplied facts are sufficient.

## Workflow

Execute in this exact order and do not skip steps.
Do not continue to the next step until the current step passes validation.

For every task, structure work as:

- Input
- Process
- Output
- Action Guide
- Constraints

### Step 1. Task Setup Confirmation

Before any bookkeeping work, confirm:

- entity name
- target period or date scope
- whether the task is to rebuild from raw evidence or reproduce an existing ledger
- source materials available for the task
- source traceability sufficient to link each decision back to the original evidence
- the correct account set when live Wukong operations are required

If required source evidence is missing, traceability is insufficient, or the task mode is unclear, stop and request clarification or missing materials before continuing.

### Step 2. Environment Initialization and Pre-Posting Preparation

Verify before any posting:

- keep each entity physically isolated
- use standard PRC enterprise accounting subjects for first-level subjects
- refine expense detail subjects and do not use vague "other" expense buckets
- bind counterparties to receivable, payable, and other current accounts
- split bank subjects by real bank account

If the chart of accounts or auxiliary setup is incomplete, stop work.

### Step 3. Data Intake and Preprocessing

Accept source data and standardize each record.

If a payer or payee is an intermediary account such as Alipay, WeChat, or reserve funds, do not treat it as the final counterparty.
Read the note or receipt details and restore the real business counterparty.

### Step 4. Bank Flow Secondary Normalization

When the user provides only raw bank-statement data, do not classify business nature or post directly from the raw file.
First normalize the raw bank rows with:

- `normalization_deal/bank_flow_secondary_normalization_template.md`

Use that file as the required intermediate standard before posting decisions, voucher preparation, or system posting.

Minimum requirements:

- preserve raw bank rows in `01_raw_import`
- standardize each valid bank row into `02_normalized_txn`
- place every normalized row into exactly one decision state in `03_decision_queue`
- use only these decision states:
  - `post`
  - `hold`
  - `escalate`
- place only directly postable rows into `04_post_ready`
- keep full source traceability from normalized rows back to the original file, sheet, and row
- for every held row, state:
  - hold reason
  - minimum missing information

Do not post directly from the raw bank-statement sheet.
Do not continue to voucher generation until the normalization structure is complete.

### Step 5. Source Conflict Handling

When ledger totals, bank flows, invoices, payroll sheets, social security sheets, or user statements conflict, do not silently blend them into one posting result.

Handle conflicts in this order:

1. raw source evidence
2. user-confirmed facts
3. historical ledger balances
4. derived or previously posted summaries

Required actions:

- identify the exact conflicting fields
- state which source is being treated as authoritative for the current decision
- separate:
  - postable items
  - held items
  - disputed items
- do not close the period while disputed items remain unresolved

If the task goal is to reproduce an existing ledger rather than rebuild from raw evidence, state that mode explicitly before following the old ledger treatment.

### Step 6. Business Identification

First determine the primary business nature of each transaction.
Use the following as common primary classes, and refine further when needed.
Do not force every transaction into a single fixed label if the substance requires split treatment, secondary tagging, or temporary pending classification.

Common primary classes include:

- sales and customer receipts
- procurement and supplier payments
- expense payments
- payroll and employee-related payments
- tax and social-security-related payments
- current account movements
- shareholder or financing-related funds
- asset-related expenditure
- refunds, reversals, and returns
- transfers between own accounts or intermediary funds
- uncertain

For each classification, output:

- primary classification
- secondary tag when needed
- confidence score
- evidence basis

If confidence is below the usable threshold, do not generate a voucher.
Route the transaction to exceptions.

### Step 7. Counterparty Normalization

Normalize names before using or creating auxiliary ledgers:

- match against historical names by similarity
- infer nature from transaction behavior and frequency
- do not bulk-create new counterparties before the business nature is clear

### Step 8. Accounting Period Attribution

Apply accrual accounting:

- recognize revenue by performance or business completion
- match costs with related revenue
- recognize expenses in the actual occurrence period
- treat invoices as evidence, not as the sole booking basis

If bank date and business date differ, prefer the business date.
Mark cross-period matters and propose adjusting entries.

### Step 9. Accounting Decision Comparison

Generate multiple treatments for each transaction and score them.
Use this priority order:

1. invoice or formal evidence
2. historical transaction pattern
3. counterparty nature
4. summary text

Choose the highest-quality reasonable treatment.
If no treatment is sufficiently reasonable, do not post.

### Step 10. Amount Reasonableness and Risk Control

Check for anomalies such as:

- single amount far above history
- abnormal expense-to-revenue ratio
- sudden revenue or cost spikes or drops
- sustained abnormal losses or profits

When triggered:

- mark risk level
- reduce automation priority
- require explanation before close

### Step 11. Voucher Generation

Require:

- debit and credit must balance exactly
- summary must reflect business substance
- treatment must respect risk isolation rules

Apply these hard rules:

- shareholder funds without capital contribution evidence -> book to other payables
- revenue without invoice -> allow only with explicit risk flag
- non-operating personal expenditure -> book to other receivables - individual

### Step 12. Exception Handling and Batch Split

Classify exceptions as:

- low risk: auto-handle allowed
- medium risk: confirmation required
- high risk: no auto-processing

For every exception, output:

- recommended treatment
- alternative treatment
- risk explanation

A batch is considered properly processed only when every source transaction is in exactly one of:

- posted
- held with explicit reason and minimum missing information
- escalated with explicit risk reason

Do not leave any transaction in an implicit or silent state.

### Step 13. Period-End Processing

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

### Step 14. Bank Reconciliation

Use:

`bank balance = book balance + reconciliation items`

Possible reconciliation items:

- outstanding items
- in-transit funds
- third-party platform balances

Treat bank balance as a strong validation anchor, not absolute truth.
Every difference must be explainable.
If not explainable, do not close.

### Step 15. Reporting, Tax Mapping, and Close

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

### Step 16. Accountant Review Report

Before close, first generate an accountant-facing markdown review report from the standard md template, then generate the docx report from that md report.

Execution order:

1. generate the markdown report
2. generate the docx report from the markdown report

The md template path must use the path defined in `Deliverables and Output`.
Do not maintain a separate content template for docx.

## Decision Rules

### 1. General Decision Rules

#### Direction-First Rule

Always evaluate money direction before trusting summary text.

- if bank flow is incoming, first consider:
  - customer repayment
  - current-account return
  - deposit return
  - refund
- if bank flow is outgoing, first consider:
  - purchase payment
  - expense payment
  - payroll, tax, or social security
  - transfer to intermediary funds

Do not let keywords such as "采购", "货款", or "用品" override cash direction by themselves.

Special handling:

- incoming flow with procurement-like text may still be customer payment for the other party's purchase from the company
- outgoing flow with sales-like text may still be refund, commission, or current-account movement

#### Evidence Layering Rule

Assign evidence into three layers and decide automation scope accordingly.

Layer A - direct evidence:

- invoice
- receipt or remittance advice
- payroll or social security statement
- order number
- stock-in or stock-out record
- known supplier or customer mapping

Layer B - semi-direct evidence:

- stable historical counterparty pattern
- merchant name extracted from Alipay, WeChat, or bank note
- prior confirmed treatment for the same pattern

Layer C - weak evidence:

- raw summary text only
- intermediary account name only
- natural-person counterparty without mapping
- generic wording such as "货款", "用品", or "消费"

Decision threshold:

- A plus matching direction -> auto-post allowed
- B only -> allow suggestion, usually hold unless pattern is stable and low-risk
- C only -> do not auto-post

#### Confidence Upgrade and Downgrade Factors

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

#### Minimum-Sufficient Posting Rule

Do not hold transactions by category alone.
Decide based on whether the minimum information required for a defensible accounting treatment is available.

If the minimum sufficient facts are available, post.
If the minimum sufficient facts are not available, hold.
If a batch contains both clear and unclear transactions, post the clear subset first and hold only the unclear subset.

Minimum sufficient facts must support all of:

- money direction is clear
- period attribution is usable
- business nature is identifiable
- counterparty role is identifiable
- subject path is reasonably determined
- risk can be stated explicitly in the output

Avoid both failure modes:

- over-posting uncertain flows
- over-holding flows that are already determinable

### 2. Counterparty and Penetration Rules

#### Intermediary Account Penetration Rule

Never treat intermediary accounts as final counterparties.

Applicable names include:

- 支付宝（中国）网络技术有限公司客户备付金
- 微信支付
- 待报解预算收入
- 备付金
- platform settlement or clearing accounts

Required actions:

1. parse note or remark for the real merchant or business clue
2. determine whether the flow is:
   - transfer to intermediary funds
   - final merchant purchase
   - tax or social security collection
   - unidentified platform clearing
3. store both:
   - channel counterparty
   - penetrated real counterparty

If the real counterparty cannot be restored, hold the transaction.

#### Alipay and WeChat Two-Step Rule

For Alipay or WeChat related flows, evaluate in two steps.

Step 1: determine whether this is fund transfer or final consumption.

- if note indicates top-up, reserve, wallet, or generic merchant placeholder, prefer:
  - Dr Other Monetary Funds
  - Cr Bank Deposits
- if note identifies a concrete merchant or order, continue to Step 2

Step 2: determine business nature.

- procurement goods -> accounts payable, inventory, or prepayment path
- office supplies, tools, or small consumables -> expense path
- fixed-asset-like or fit-out items -> long-term asset or deferred expense review
- still unclear -> hold

Do not expense Alipay or WeChat flows directly unless merchant and purpose are both sufficiently clear.

#### Natural-Person Counterparty Mapping Rule

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

### 3. Transaction-Specific Treatment Rules

#### Procurement Payment Decision Rule

For outgoing flows marked as "货款" or equivalent, choose among three paths.

Path A - payable settlement

Use when goods are already received or payable basis exists.

- Dr Accounts Payable
- Cr Bank Deposits

Path B - prepayment

Use when payment occurs before receipt, invoice, or stock-in evidence.

- Dr Prepayments
- Cr Bank Deposits

Path C - hold

Use when supplier identity, purpose, or inventory relation is unclear.

Additional requirement:

- if later stock-in evidence appears, generate period-end or same-period conversion:
  - Dr Inventory or Expense
  - Cr Accounts Payable or Prepayments

#### Incoming Procurement-Word Rule

If an incoming bank flow contains procurement-like wording such as "采购服装":

- do not classify as purchase automatically
- evaluate whether it means the other party purchased from the company
- if the company is the seller, prefer:
  - Dr Bank Deposits
  - Cr Accounts Receivable or revenue-related path depending on evidence stage
- if it is truly a supplier refund or current-account return, require supporting evidence

Incoming cash direction has priority over procurement wording.

#### Social Security Split Rule

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

#### Inventory Chain Completion Rule

When supporting records show goods and quantities, complete the business chain.

Bank payment alone does not finish the chain.
After confirming goods received:

- Dr Inventory
- Cr Accounts Payable or Prepayments

If quantity, SKU, or stock-in basis is missing, do not auto-generate the inventory entry.

### 4. Voucher and Posting Control Rules

#### Same-Day Merge Rule

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

#### Voucher Generation Rules

Require:

- debit and credit must balance exactly
- summary must reflect business substance
- treatment must respect risk isolation rules

Apply these hard rules:

- shareholder funds without capital contribution evidence -> book to other payables
- revenue without invoice -> allow only with explicit risk flag
- non-operating personal expenditure -> book to other receivables - individual

### 5. Hold and Escalation Rules

#### Output Requirements for Every Decision

For each transaction, output:

- posting decision: post, hold, or escalate
- final classification
- confidence score
- evidence layer used
- whether counterparty was penetrated or mapped
- chosen treatment
- rejected alternatives
- voucher lines or proposed voucher lines
- source-row traceability
- risk level and reason
- reconciliation impact
- next required action
- reason if held

#### Minimum Missing-Information Rule

When a transaction cannot be posted, ask only for the minimum additional information required to make it postable.
Do not ask for broad document sets unless they are actually necessary.
Use the smallest fact set that resolves the accounting decision.

Typical minimum missing information by transaction type:

- payroll:
  - employee identity
  - payroll month
  - whether the bank amount is net pay
  - whether payroll accrual already exists
- social security:
  - contribution month
  - employer burden
  - employee burden
  - whether housing fund or tax is included
- natural-person counterparty:
  - person identity
  - relationship to the company
  - business nature of the payment
  - whether the person is acting on behalf of an entity
- incoming flow of unclear nature:
  - whether it is revenue, refund, current-account return, or shareholder funds
  - related customer or supplier if any
  - whether performance or delivery has occurred if revenue is claimed
- refund or return flow:
  - which original payment or transaction it relates to
  - whether the original nature was purchase, expense, deposit, or current account

#### Held-Item Output Rule

For every held transaction, output all of:

- hold reason
- minimum missing information
- posting becomes possible if the missing information is supplied
- preferred treatment after confirmation
- alternative treatment when relevant
- risk if posted without clarification

Keep held-item explanations short and operational.
The goal is to help the user unblock posting, not to produce generic caution text.

#### Partial-Batch Completion Rule

A batch is considered properly processed only when every source transaction is in exactly one of:

- posted
- held with explicit reason and minimum missing information
- escalated with explicit risk reason

Do not leave any transaction in an implicit or silent state.

At the end of each batch, output:

- posted transactions summary
- held transactions summary
- escalated transactions summary
- missing information checklist for held items
- next actions if the user wants the held subset posted

#### Preferred Response Pattern For Unclear Transactions

When reporting unclear transactions to the user, use this structure:

- current decision: post, hold, or escalate
- why it cannot yet be posted
- minimum information needed
- what will be posted immediately once that information is confirmed
- what accounting treatment is expected after confirmation

Example pattern:

- current decision: hold
- why: incoming cash is clear, but business nature is not
- minimum information needed: confirm whether this is customer payment, supplier refund, or shareholder transfer
- once confirmed: the transaction can be posted immediately
- expected treatment:
  - customer payment -> bank deposits against receivable or revenue path
  - supplier refund -> bank deposits against prepayments or payables
  - shareholder transfer -> bank deposits against other payables or equity-related path under policy

### 6. Source Conflict Priority Rules

When ledger totals, bank flows, invoices, payroll sheets, social security sheets, or user statements conflict, do not silently blend them into one posting result.

Handle conflicts in this order:

1. raw source evidence
2. user-confirmed facts
3. historical ledger balances
4. derived or previously posted summaries

Required actions:

- identify the exact conflicting fields
- state which source is being treated as authoritative for the current decision
- separate:
  - postable items
  - held items
  - disputed items
- do not close the period while disputed items remain unresolved

If the task goal is to reproduce an existing ledger rather than rebuild from raw evidence, state that mode explicitly before following the old ledger treatment.

## Deliverables and Output

### 1. Standard Deliverables

For each monthly bookkeeping task, generate these deliverables in addition to vouchers and exception decisions:

- machine-readable workpaper json
- posting proposal csv
- accountant review report md
- accountant review report docx generated from the md report

### 2. Naming Convention

Use stable English filenames so downstream steps can reference them directly.

Required md template path:

- `normalization_deal/accounting_review_report_min_template.md`

Default naming convention for a monthly period `YYYYMM`:

- `jietu/YYYYMM_skill_workpaper.json`
- `jietu/YYYYMM_posting_proposals_skill.csv`
- `jietu/YYYYMM_accounting_review_report.md`
- `output/doc/YYYYMM_accounting_review_report.docx`

Do not invent ad hoc filenames unless the user explicitly asks for a different naming scheme.

### 3. Decision Output Contract

For each batch or transaction, produce a concise auditable result containing:

- posting decision: post, hold, or escalate
- business classification
- confidence and evidence
- chosen accounting treatment and rejected alternatives
- voucher lines or proposed voucher lines
- risk level and reason
- reconciliation impact
- next required action

### 4. Held-Item Output

For every held transaction, output:

- hold reason
- minimum missing information
- posting becomes possible if the missing information is supplied
- preferred treatment after confirmation
- alternative treatment when relevant
- risk if posted without clarification

### 5. Batch Output

At the end of each batch, output:

- posted transactions summary
- held transactions summary
- escalated transactions summary
- missing information checklist for held items
- next actions if the user wants the held subset posted

### 6. Accountant Review Report Structure

The markdown report must contain these sections:

1. review conclusion
2. posting summary
3. posted item list
4. held item list
5. follow-up recommendations

Minimum content requirements:

- period
- entity name
- count and total amount of suggested postings
- count and reason summary of held items
- whether close is recommended
- key source conflicts, if any

The md template path must use the path defined in `Naming Convention`.
Do not maintain a separate content template for docx.

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

## Validation Checklist

Do not consider the work complete unless all applicable checks pass:

- all vouchers balance
- bank balance differences are explained
- receivable and payable balances are traceable
- revenue and cost are matched
- expense structure is reasonable
- abnormal fluctuations are flagged
- high-risk items are not auto-posted
- every transaction is either posted, held, or escalated

## References

Read these only when needed:

- `references/sme-accounting-standard.md:1` for the full source standard extracted from the user material
- `agent-harness/cli_anything/wukong/skills/SKILL.md:1` for concrete Wukong CLI operations
