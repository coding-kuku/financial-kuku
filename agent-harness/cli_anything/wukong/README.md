# cli-anything-finclaw

Command-line interface for **FinClaw (财务虾)** — a Spring Boot accounting system.

## Required Dependency

The FinClaw server must be running before using this CLI.

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
which cli-anything-finclaw
cli-anything-finclaw --help
cli-anything-finclaw status
```

## Date Format Convention

| Format | Example | Used for |
|--------|---------|---------|
| `YYYY-MM` | `2024-06` | Period inputs: `ledger --start/--end`, `report --date`, `certificate list --start/--end` |
| `YYYY-MM-DD` | `2024-06-01` | Full dates: `certificate add/update --date`, `statement close/reopen --date` |

## Basic Usage

```bash
# Interactive REPL (default when no subcommand given)
cli-anything-finclaw

# Login
cli-anything-finclaw auth login -u admin -p 123456

# List account sets and switch to one
cli-anything-finclaw account list
cli-anything-finclaw account switch 1

# List subjects (account codes)
cli-anything-finclaw subject list

# List journal entries (--start/--end use YYYY-MM format)
cli-anything-finclaw certificate list --start 2024-01 --end 2024-12

# Financial reports (JSON output for agents)
cli-anything-finclaw --json report balance-sheet --period month --date 2024-06

# Custom server URL
cli-anything-finclaw --url http://192.168.1.100:44316 status
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
| `subject list` | List subjects / account codes (科目) |
| `subject add` | Add a subject (`--code`, `--name`, `--type` 1–5, `--direction` 1=借方/2=贷方 all required) |
| `subject delete` | Delete subjects |
| `voucher list` | List voucher words (凭证字) |
| `voucher add <name>` | Add a voucher word |
| `voucher delete <id>` | Delete a voucher word |
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
cli-anything-finclaw --json auth whoami
cli-anything-finclaw --json account list
cli-anything-finclaw --json certificate list --start 2024-01 --end 2024-06
```

## Session Storage

Session (token, active account) is stored in:
```
~/.cli-anything-finclaw/session.json
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `FINCLAW_URL` | Override server URL (default: http://localhost:44316) |

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
