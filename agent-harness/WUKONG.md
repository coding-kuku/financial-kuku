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

## CLI Command Groups

| Group | Description |
|-------|-------------|
| `auth` | Login, logout, whoami |
| `account` | Account set management (账套) |
| `subject` | Subject / account code management (科目) |
| `voucher` | Voucher word management (凭证字) |
| `certificate` | Journal entry management (凭证) |
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

# Initialize default data (subjects, voucher words)
cli-anything-wukong account init
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
    {"subjectId": 1001, "digestContent": "收到货款", "debtorBalance": 1000, "ownerBalance": 0},
    {"subjectId": 6001, "digestContent": "收到货款", "debtorBalance": 0, "ownerBalance": 1000}
  ]'

# Review the certificate
cli-anything-wukong certificate review 42 --approve
```

### Financial Reports

```bash
# Monthly balance sheet
cli-anything-wukong report balance-sheet --period month --date 2024-06-30 --check

# Income statement Q2
cli-anything-wukong report income --period quarter --date 2024-06-30

# JSON output for agent consumption
cli-anything-wukong --json report balance-sheet --period month --date 2024-06-30
```

### Account Books

```bash
# Detail ledger for subject 1001 (cash)
cli-anything-wukong ledger detail --subject-id 123 --start 2024-01-01 --end 2024-12-31

# Subject balance table
cli-anything-wukong ledger balance --start 2024-01-01 --end 2024-12-31 --level 1
```

## Required Dependency

The Wukong Accounting server must be running. Build and start:

```bash
mvn clean package -pl finance/finance-web -am -Dmaven.test.skip=true
java -jar finance/finance-web/target/finance-web-0.0.1-SNAPSHOT.jar
```

The server requires MySQL 8, Redis 6+, and optionally Elasticsearch 8.5.

Default admin credentials: `admin` / `123456`
