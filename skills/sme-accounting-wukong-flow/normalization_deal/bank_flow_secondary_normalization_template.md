# Bank Flow Secondary Normalization Template

Use this file as the text reference for:

- `normalization_deal/bank_flow_secondary_normalization_template.xlsx`

This template is the required intermediate layer when the user provides only a raw bank statement.
Do not post directly from the raw bank file.

## Purpose

Convert raw bank rows into a stable intermediate structure before:

- business classification
- post / hold / escalate decisioning
- voucher preparation
- system posting
- reporting

## Fixed Flow

1. Import the raw bank rows into `01_raw_import`.
2. Convert each valid bank row into a standardized row in `02_normalized_txn`.
3. Place every standardized row into exactly one decision state in `03_decision_queue`.
4. Place only directly postable rows into `04_post_ready`.

## Workbook Rules

- Row 1 is the system field-name row.
- Row 2 is the description row.
- Row 3 is the example row.
- Real data starts from row 4.
- Do not rename fields.
- Do not delete source traceability fields.

## Required Sheets

### 00_readme

Human-readable instructions only.
Do not place transaction data here.

### 01_raw_import

Purpose:

- preserve imported raw bank rows
- preserve source traceability

Required behavior:

- one imported bank row per Excel row
- preserve original file name
- preserve original sheet name
- preserve original row number
- preserve original date/time text
- preserve original income/expense values
- preserve original balance
- preserve original counterparty, account, bank, summary, note, and flow ID when available
- preserve a raw row snapshot when practical

Fields:

- `source_file`
- `source_sheet`
- `source_row`
- `raw_date`
- `raw_time`
- `raw_income`
- `raw_expense`
- `raw_balance`
- `raw_counterparty`
- `raw_counterparty_account`
- `raw_counterparty_bank`
- `raw_summary`
- `raw_note`
- `raw_flow_id`
- `raw_txn_text`

Do not perform accounting judgment in this sheet.

### 02_normalized_txn

Purpose:

- convert raw bank rows into canonical transaction rows

Every valid bank row must be normalized into one row here, unless it is explicitly excluded as a non-transaction row.

Fields:

- `norm_id`
- `source_file`
- `source_sheet`
- `source_row`
- `txn_date`
- `txn_time`
- `direction`
- `amount`
- `balance_after`
- `counterparty_name_raw`
- `counterparty_name_norm`
- `counterparty_type`
- `counterparty_account`
- `counterparty_bank`
- `raw_summary`
- `raw_note`
- `flow_id`
- `channel_name`
- `final_counterparty`
- `biz_hint`
- `candidate_type`
- `period_month`
- `merge_group`
- `confidence`
- `risk_level`
- `decision_status`
- `hold_reason`
- `min_missing_info`
- `suggested_dr`
- `suggested_cr`
- `voucher_digest`
- `evidence_basis`
- `user_confirmation`
- `final_status`

Normalization rules:

- convert split income/expense columns into `direction + amount`
- parse standard date and time when possible
- preserve both raw and normalized counterparty names
- identify counterparty type as one of:
  - `company`
  - `person`
  - `platform`
  - `tax`
  - `social_security`
  - `unknown`
- preserve raw summary and raw note even when they are weak evidence
- keep full source traceability

Do not silently drop difficult rows.

### 03_decision_queue

Purpose:

- make downstream accounting actions explicit

Every normalized row must appear here in exactly one state:

- `post`
- `hold`
- `escalate`

Fields:

- `norm_id`
- `txn_date`
- `counterparty_name_norm`
- `direction`
- `amount`
- `candidate_type`
- `decision_status`
- `priority`
- `suggested_dr`
- `suggested_cr`
- `voucher_digest`
- `hold_reason`
- `min_missing_info`
- `next_action`

Rules:

- `post`: minimum sufficient facts already support a defensible treatment
- `hold`: the row is potentially postable but still lacks minimum required facts
- `escalate`: risk is materially high or the treatment is too unstable for normal processing

For every `hold` row, both of these are mandatory:

- `hold_reason`
- `min_missing_info`

### 04_post_ready

Purpose:

- collect only the rows that are ready for voucher creation or system posting

Fields:

- `norm_id`
- `voucher_date`
- `voucher_word`
- `voucher_num`
- `digest`
- `dr_subject`
- `cr_subject`
- `amount`
- `merge_group`
- `source_trace`
- `post_status`
- `certificate_id`

Only place a row here when:

- `decision_status = post`
- debit and credit path is already determined
- summary is usable
- source trace is complete

Do not place `hold` or `escalate` rows here.

## Minimum Completeness Check

The normalization step is complete only when every imported bank row is accounted for in one of these ways:

- normalized and marked `post`
- normalized and marked `hold`
- normalized and marked `escalate`
- excluded as a non-transaction row with explicit reason

Before continuing to voucher generation or live posting, output:

- total imported rows
- total valid transaction rows
- total post rows
- total hold rows
- total escalate rows
- excluded non-transaction rows and why they were excluded
