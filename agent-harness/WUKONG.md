# Wukong Accounting — CLI Harness SOP

## Software Overview

**Wukong Accounting (悟空财务)** is an open-source Chinese accounting system built on Spring Boot 2.7 + MyBatis-Plus. It provides double-entry bookkeeping with:

- Journal entry management (凭证)
- Subject/account code tree (科目)
- Account set management (账套)
- Financial reports: Balance Sheet, Income Statement, Cash Flow Statement
- Account books: Detail Ledger, General Ledger, Subject Balance Table

The system runs as a REST API server on port 44316. All CLI operations call this server via HTTP.

## Architecture Analysis

### Backend Engine

The real software is the Wukong Java server (`finance-web-0.0.1-SNAPSHOT.jar`). The CLI is a command-line client — it calls the server's REST API. There is no client-side reimplementation of any business logic.

### Authentication

- `POST /login` — username + SHA256(password+salt) → returns UUID token
- Token stored in `AUTH-TOKEN` header for all subsequent requests
- Session state stored locally in `~/.cli-anything-wukong/session.json`

### Account Set Context

The server is multi-tenancy capable with "account sets" (账套). Each account set is an isolated accounting entity (a company's books). The `POST /financeAccountSet/switchAccountSet?accountId=N` endpoint switches the server-side session to a specific account set.

The CLI tracks the active account set ID locally and calls `switchAccountSet` on login and `account switch`.

### API Pattern

All endpoints use `POST`. Response format:
```json
{"code": 200, "data": {...}, "msg": "success"}
```

Authentication failure returns code 401 or 302. Business errors return non-200 codes.

## Date Format Convention

| Format | Example | Used for |
|--------|---------|---------|
| `YYYY-MM` | `2024-06` | Period ranges: `ledger --start/--end`, `report --date`, `certificate list --start/--end` |
| `YYYY-MM-DD` | `2024-06-01` | Full dates: `certificate add/update --date`, `statement close/reopen --date` |

The CLI validates and converts `YYYY-MM` to `yyyyMM` internally before sending to the API.

## CLI Command Groups

| Group | Description |
|-------|-------------|
| `auth` | Login, logout, whoami |
| `account` | Account set management (账套) |
| `subject` | Subject / account code management (科目) |
| `voucher` | Voucher word management (凭证字) |
| `certificate` | Journal entry management (凭证) — list, get, add, update, delete, review |
| `adjuvant` | Auxiliary accounting categories (辅助核算) — list, add, delete |
| `statement` | Period closing (结账) — status, close, reopen |
| `ledger` | Account book queries (账簿) |
| `report` | Financial reports (报表) |
| `status` | Server health check |

## Workflow Examples

### First-time Setup

```bash
# Check server is running
cli-anything-wukong status

# Login
cli-anything-wukong auth login -u admin -p 123456

# List account sets
cli-anything-wukong account list

# Switch to account set 1
cli-anything-wukong account switch 1

```

### Journal Entry Workflow

```bash
# List voucher words to get ID
cli-anything-wukong voucher list

# List subjects to get IDs
cli-anything-wukong subject list

# Add a journal entry (debit cash 1000, credit revenue 1000)
cli-anything-wukong certificate add \
  --voucher-id 1 \
  --date 2024-06-01 \
  --detail '[
    {"subjectId": 1001, "digestContent": "收到货款", "debtorBalance": 1000, "creditBalance": 0},
    {"subjectId": 6001, "digestContent": "收到货款", "debtorBalance": 0, "creditBalance": 1000}
  ]'

# Update an existing journal entry
cli-anything-wukong certificate update \
  --id 42 \
  --voucher-id 1 \
  --date 2024-06-15 \
  --detail '[
    {"subjectId": 1001, "digestContent": "收到货款(修正)", "debtorBalance": 1200, "creditBalance": 0},
    {"subjectId": 6001, "digestContent": "收到货款(修正)", "debtorBalance": 0, "creditBalance": 1200}
  ]'

# Review the certificate
cli-anything-wukong certificate review 42 --approve
```

### Auxiliary Accounting (辅助核算)

```bash
# List all auxiliary accounting categories
cli-anything-wukong adjuvant list

# Add a custom category (label 4 = project)
# Label values: 1=客户 2=供应商 3=职员 4=项目 5=部门 6=存货 7=自定义
cli-anything-wukong adjuvant add --name "研发项目A" --label 4

# Delete by ID
cli-anything-wukong adjuvant delete 123
```

### Period Closing (结账)

```bash
# Check current period status
cli-anything-wukong statement status

# Close the current accounting period
cli-anything-wukong statement close --date 2024-01-31

# Reopen a period if corrections are needed
cli-anything-wukong statement reopen --date 2024-01-31
```

### Financial Reports

```bash
# Monthly balance sheet
cli-anything-wukong report balance-sheet --period month --date 2024-06 --check

# Income statement Q2
cli-anything-wukong report income --period quarter --date 2024-06

# JSON output for agent consumption
cli-anything-wukong --json report balance-sheet --period month --date 2024-06
```

### Account Books

```bash
# Detail ledger for subject 1001 (cash)
cli-anything-wukong ledger detail --subject-id 123 --start 2024-01 --end 2024-12

# Subject balance table
cli-anything-wukong ledger balance --start 2024-01 --end 2024-12 --level 1
```

## Required Dependency

The Wukong Accounting server must be running. Build and start:

```bash
mvn clean package -pl finance/finance-web -am -Dmaven.test.skip=true
java -jar finance/finance-web/target/finance-web-0.0.1-SNAPSHOT.jar
```

The server requires MySQL 8, Redis 6+, and optionally Elasticsearch 8.5.

Default admin credentials: `admin` / `123456`
