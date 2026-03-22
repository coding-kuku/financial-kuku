---
name: "cli-anything-wukong"
description: "CLI for Wukong Accounting (悟空财务) — manage journal entries, subjects, account sets, and financial reports via REST API"
---

# cli-anything-wukong

Command-line interface for **Wukong Accounting (悟空财务)**, a Chinese double-entry bookkeeping system.

## Prerequisites

1. Wukong Accounting server running on port 44316 (or custom URL)
2. CLI installed: `pip install -e agent-harness/`

## Installation

```bash
cd /path/to/Wukong_Accounting/agent-harness
pip install -e .
cli-anything-wukong --help
```

## Quick Start

```bash
cli-anything-wukong auth login -u admin -p 123456
cli-anything-wukong account list
cli-anything-wukong account switch 1
cli-anything-wukong subject list
```

## Command Groups

### auth — Authentication
```bash
cli-anything-wukong auth login -u <user> -p <pass>   # Login, saves token
cli-anything-wukong auth logout                        # Logout
cli-anything-wukong auth whoami                        # Current user info
```

### account — Account Set Management (账套)
```bash
cli-anything-wukong account list                       # All accessible account sets
cli-anything-wukong account switch <id>                # Switch active account set
cli-anything-wukong account create --name "My Co" --company "My Co Ltd" --start 2024-01
cli-anything-wukong account init                       # Initialize default subjects/voucher words
```

### subject — Account Codes (科目)
```bash
cli-anything-wukong subject list                       # All subjects
cli-anything-wukong subject list --type 1              # Assets only (1=资产 2=负债 3=权益 4=成本 5=损益)
cli-anything-wukong subject list --tree                # Tree structure
cli-anything-wukong subject add --code 1001 --name "库存现金" --type 1
cli-anything-wukong subject delete <id1> <id2>
```

### voucher — Voucher Words (凭证字)
```bash
cli-anything-wukong voucher list
cli-anything-wukong voucher add "记"
cli-anything-wukong voucher delete <id>
```

### certificate — Journal Entries (凭证)
```bash
cli-anything-wukong certificate list --start 2024-01-01 --end 2024-12-31
cli-anything-wukong certificate list --voucher-id 1 --status 0   # unreviewed
cli-anything-wukong certificate get <id>
cli-anything-wukong certificate next-num --voucher-id 1 --date 2024-06-01
cli-anything-wukong certificate add \
  --voucher-id 1 --date 2024-06-01 \
  --detail '[{"subjectId":101,"digestContent":"memo","debtorBalance":1000,"ownerBalance":0},
             {"subjectId":201,"digestContent":"memo","debtorBalance":0,"ownerBalance":1000}]'
cli-anything-wukong certificate review <id1> <id2> --approve
cli-anything-wukong certificate delete <id1> <id2>
```

### ledger — Account Books (账簿)
```bash
cli-anything-wukong ledger detail --subject-id 123 --start 2024-01-01 --end 2024-06-30
cli-anything-wukong ledger general --subject-id 123 --start 2024-01-01 --end 2024-12-31
cli-anything-wukong ledger balance --start 2024-01-01 --end 2024-12-31 --level 1
cli-anything-wukong ledger multi-column --subject-id 123 --start 2024-01-01 --end 2024-06-30
```

### report — Financial Reports (报表)
```bash
cli-anything-wukong report balance-sheet --period month --date 2024-06-30
cli-anything-wukong report balance-sheet --period quarter --date 2024-09-30 --check
cli-anything-wukong report income --period month --date 2024-06-30
cli-anything-wukong report cash-flow --period year --date 2024-12-31
```

Period options: `month`, `quarter`, `year`

### status
```bash
cli-anything-wukong status                             # Server + session info
cli-anything-wukong --url http://HOST:44316 status     # Custom server URL
```

## JSON Output (Agent Use)

Add `--json` before any subcommand for machine-readable output:

```bash
cli-anything-wukong --json auth login -u admin -p 123456
# {"token": "abc123...", "username": "admin"}

cli-anything-wukong --json account list
# [{"accountSetId": 1, "accountName": "Default", ...}]

cli-anything-wukong --json certificate list --start 2024-01-01 --end 2024-12-31
# {"total": 42, "records": [...]}

cli-anything-wukong --json report balance-sheet --period month --date 2024-06-30
# {"rows": [...]}

cli-anything-wukong --json status
# {"server_url": "...", "server_reachable": true, "authenticated": true, ...}
```

## Error Handling

- **WukongConnectionError**: Server unreachable — start the Java server
- **WukongAuthError**: Token expired — run `auth login` again
- **WukongAPIError**: Business error — check the error code and message

All errors exit with code 1. JSON mode errors go to stderr.

## Session Storage

```
~/.cli-anything-wukong/session.json   # token, active account ID, base URL
~/.cli-anything-wukong/history        # REPL command history
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `WUKONG_URL` | Override server URL |
| `CLI_ANYTHING_FORCE_INSTALLED` | Set to 1 to require installed command in tests |
