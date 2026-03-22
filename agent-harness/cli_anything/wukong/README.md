# cli-anything-wukong

Command-line interface for **Wukong Accounting (悟空财务)** — a Spring Boot accounting system.

## Required Dependency

The Wukong Accounting server must be running before using this CLI.

```bash
# From the project root
java -jar finance/finance-web/target/finance-web-0.0.1-SNAPSHOT.jar
```

The server requires MySQL 8, Redis 6+, and listens on port 44316 by default.

## Installation

```bash
cd agent-harness
pip install -e .
```

## Verify Installation

```bash
which cli-anything-wukong
cli-anything-wukong --help
cli-anything-wukong status
```

## Basic Usage

```bash
# Interactive REPL (default when no subcommand given)
cli-anything-wukong

# Login
cli-anything-wukong auth login -u admin -p 123456

# List account sets and switch to one
cli-anything-wukong account list
cli-anything-wukong account switch 1

# List subjects (account codes)
cli-anything-wukong subject list

# List journal entries
cli-anything-wukong certificate list --start 2024-01-01 --end 2024-12-31

# Financial reports (JSON output for agents)
cli-anything-wukong --json report balance-sheet --period month --date 2024-06-30

# Custom server URL
cli-anything-wukong --url http://192.168.1.100:44316 status
```

## Command Groups

| Command | Description |
|---------|-------------|
| `auth login` | Login with username/password |
| `auth logout` | Logout |
| `auth whoami` | Show current user |
| `account list` | List account sets (账套) |
| `account switch <id>` | Switch active account set |
| `account create` | Create new account set |
| `account init` | Initialize default subjects and voucher words |
| `subject list` | List subjects / account codes (科目) |
| `subject add` | Add a subject |
| `subject delete` | Delete subjects |
| `voucher list` | List voucher words (凭证字) |
| `voucher add <name>` | Add a voucher word |
| `certificate list` | List journal entries (凭证) |
| `certificate get <id>` | Get certificate detail |
| `certificate add` | Add a journal entry |
| `certificate update` | Edit an existing journal entry |
| `certificate delete` | Delete certificates |
| `certificate review` | Approve/unapprove certificates |
| `certificate next-num` | Get next certificate number |
| `adjuvant list` | List auxiliary accounting categories (辅助核算) |
| `adjuvant add` | Add an auxiliary accounting category |
| `adjuvant delete` | Delete an auxiliary accounting category |
| `statement status` | Query period closing status (结账状态) |
| `statement close` | Close the current accounting period (结账) |
| `statement reopen` | Reopen a closed period (反结账) |
| `ledger detail` | Detail ledger (明细账) |
| `ledger general` | General ledger (总账) |
| `ledger balance` | Subject balance table (科目余额表) |
| `ledger multi-column` | Multi-column ledger (多栏账) |
| `report balance-sheet` | Balance sheet (资产负债表) |
| `report income` | Income statement (利润表) |
| `report cash-flow` | Cash flow statement (现金流量表) |
| `status` | Server health check |

## JSON Output Mode

All commands support `--json` for machine-readable output:

```bash
cli-anything-wukong --json auth whoami
cli-anything-wukong --json account list
cli-anything-wukong --json certificate list --start 2024-01-01 --end 2024-06-30
```

## Session Storage

Session (token, active account) is stored in:
```
~/.cli-anything-wukong/session.json
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `WUKONG_URL` | Override server URL (default: http://localhost:44316) |

## Running Tests

```bash
cd agent-harness
# Unit tests (no server needed)
pytest cli_anything/wukong/tests/test_core.py -v

# E2E tests (server must be running with admin/123456)
pytest cli_anything/wukong/tests/test_full_e2e.py -v -s

# Force-installed command tests
CLI_ANYTHING_FORCE_INSTALLED=1 pytest cli_anything/wukong/tests/ -v -s
```
