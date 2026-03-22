# Test Plan — cli-anything-wukong

## Test Inventory Plan

| File | Tests Planned |
|------|--------------|
| `test_core.py` | 37 unit tests |
| `test_full_e2e.py` | 24 E2E + subprocess tests |

---

## Unit Test Plan (`test_core.py`)

Unit tests use synthetic data, no running server required. All tests mock `WukongClient.post()`.

### `session.py` (6 tests)
- `test_load_session_defaults` — fresh session returns default base_url, null token
- `test_save_and_load_session` — roundtrip session write/read
- `test_set_token` — updates token in session file
- `test_set_account_id` — updates account_id in session file
- `test_set_base_url` — updates base_url in session file
- `test_clear_session` — sets token and account_id to None

### `wukong_backend.py` (6 tests)
- `test_client_post_success` — 200 response returns data field
- `test_client_post_auth_error_401` — HTTP 401 raises WukongAuthError
- `test_client_post_api_error` — business code non-200 raises WukongAPIError
- `test_client_post_connection_error` — connection refused raises WukongConnectionError
- `test_client_post_no_auth_header` — auth=False omits AUTH-TOKEN
- `test_client_post_raw_response` — raw_response=True returns full dict

### `auth.py` (3 tests)
- `test_login_success` — returns token string
- `test_login_bad_credentials` — propagates WukongAPIError
- `test_whoami` — returns user dict

### `account.py` (3 tests)
- `test_list_accounts` — returns list
- `test_switch_account` — calls switchAccountSet with correct params
- `test_create_account` — calls saveAccountSet with correct body

### `subject.py` (4 tests)
- `test_list_subjects_flat` — returns list with correct params
- `test_list_subjects_tree` — is_tree=1 passed correctly
- `test_add_subject` — posts correct body
- `test_delete_subjects` — posts ids list

### `certificate.py` (6 tests)
- `test_list_certificates` — pagination and filters passed correctly
- `test_get_certificate` — fetches by ID
- `test_add_certificate` — posts body with details array
- `test_review_certificates` — posts status flag
- `test_update_certificate` — posts update with int IDs
- `test_update_certificate_with_num` — optional certificateNum included

### `adjuvant.py` (4 tests)
- `test_list_adjuvants` — returns list
- `test_add_adjuvant` — posts name and label
- `test_add_adjuvant_default_label` — defaults to label=7
- `test_delete_adjuvant` — posts adjuvantId

### `statement.py` (3 tests)
- `test_query_statement` — returns status dict
- `test_close_period` — posts type=1
- `test_reopen_period` — posts type=2

### `ledger.py` (2 tests)
- `test_query_detail_account` — correct endpoint and body
- `test_query_subject_balance` — optional filters handled

---

## E2E Test Plan (`test_full_e2e.py`)

E2E tests require the Wukong server running at `http://localhost:44316` with admin/123456.

### Server Connectivity Tests (2 tests)
- `test_server_reachable` — `client.health_check()` returns True
- `test_login_and_whoami` — login returns token, whoami returns userId

### Account Set Workflow (3 tests)
- `test_list_accounts` — returns non-empty list
- `test_switch_account` — switch succeeds without error
- `test_get_account_by_id` — returns account details

### Subject Workflow (3 tests)
- `test_list_subjects` — returns subjects list
- `test_add_and_delete_subject` — add a test subject, verify it appears, delete it
- `test_list_subjects_tree` — tree structure returned

### Voucher Word Workflow (2 tests)
- `test_list_voucher_words` — returns list with at least one word
- `test_add_and_delete_voucher_word` — roundtrip add/delete

### Certificate Workflow (3 tests)
- `test_list_certificates` — returns paginated result
- `test_certificate_next_num` — returns a number
- `test_add_review_delete_certificate` — full lifecycle (add → review → delete)

### Report Tests (3 tests)
- `test_balance_sheet` — returns non-empty list
- `test_income_statement` — returns non-empty list
- `test_balance_check` — returns dict with balance status

### CLI Subprocess Tests — TestCLISubprocess (4 tests)
- `test_help` — `--help` exits 0
- `test_status_json` — `--json status` returns valid JSON with server_reachable
- `test_auth_login_json` — `--json auth login` returns token
- `test_account_list_json` — `--json account list` returns JSON array

### Certificate Update Workflow — TestCertificateUpdate (1 test)
- `test_add_and_update_certificate` — add a cert in a past month, update date and content, verify change, delete

### Adjuvant Workflow — TestAdjuvantWorkflow (2 tests)
- `test_list_adjuvants` — returns list of adjuvant categories
- `test_add_and_delete_adjuvant` — roundtrip add/delete

### Statement Workflow — TestStatementWorkflow (1 test)
- `test_query_statement_status` — returns dict with settleTime and statements list

---

## Realistic Workflow Scenarios

### Scenario 1: Month-end Close
**Simulates**: A bookkeeper closing January 2024
1. Login as admin
2. Switch to account set
3. Add several journal entries (debit/credit pairs)
4. Review (approve) all pending certificates
5. Query subject balance table for the month
6. Generate income statement for the month
7. Verify balance sheet balances

### Scenario 2: Account Code Setup
**Simulates**: Setting up chart of accounts for a new company
1. Create new account set
2. Switch to it
3. Initialize default finance data
4. List subjects — verify defaults loaded
5. Add a custom sub-account (e.g. 1002.01 — petty cash)
6. Verify it appears in the subject list

### Scenario 3: Audit Trail
**Simulates**: Auditor reviewing Q1 journal entries
1. Login
2. List certificates for Q1 with status=unreviewed
3. For each, get the full detail (subject codes, amounts)
4. Review (approve) them
5. Query detail ledger for key subjects
6. Export subject balance table (JSON)

---

## Test Results

Run: `CLI_ANYTHING_FORCE_INSTALLED=1 pytest cli_anything/wukong/tests/ -v`
Date: 2026-03-22 | Python 3.12.9 | pytest 8.4.2 | Platform: macOS-15.7.3-arm64

```
============================= test session starts ==============================
cli_anything/wukong/tests/test_core.py::TestSession::test_load_session_defaults PASSED
cli_anything/wukong/tests/test_core.py::TestSession::test_save_and_load_session PASSED
cli_anything/wukong/tests/test_core.py::TestSession::test_set_token PASSED
cli_anything/wukong/tests/test_core.py::TestSession::test_set_account_id PASSED
cli_anything/wukong/tests/test_core.py::TestSession::test_set_base_url PASSED
cli_anything/wukong/tests/test_core.py::TestSession::test_clear_session PASSED
cli_anything/wukong/tests/test_core.py::TestWukongClient::test_post_success PASSED
cli_anything/wukong/tests/test_core.py::TestWukongClient::test_post_auth_error_401 PASSED
cli_anything/wukong/tests/test_core.py::TestWukongClient::test_post_api_error_business_code PASSED
cli_anything/wukong/tests/test_core.py::TestWukongClient::test_post_connection_error PASSED
cli_anything/wukong/tests/test_core.py::TestWukongClient::test_post_no_auth_header PASSED
cli_anything/wukong/tests/test_core.py::TestWukongClient::test_post_raw_response PASSED
cli_anything/wukong/tests/test_core.py::TestAuth::test_login_success PASSED
cli_anything/wukong/tests/test_core.py::TestAuth::test_login_bad_credentials PASSED
cli_anything/wukong/tests/test_core.py::TestAuth::test_whoami PASSED
cli_anything/wukong/tests/test_core.py::TestAccount::test_list_accounts PASSED
cli_anything/wukong/tests/test_core.py::TestAccount::test_switch_account PASSED
cli_anything/wukong/tests/test_core.py::TestAccount::test_create_account PASSED
cli_anything/wukong/tests/test_core.py::TestSubject::test_list_subjects_flat PASSED
cli_anything/wukong/tests/test_core.py::TestSubject::test_list_subjects_tree PASSED
cli_anything/wukong/tests/test_core.py::TestSubject::test_add_subject PASSED
cli_anything/wukong/tests/test_core.py::TestSubject::test_delete_subjects PASSED
cli_anything/wukong/tests/test_core.py::TestCertificate::test_list_certificates_pagination PASSED
cli_anything/wukong/tests/test_core.py::TestCertificate::test_get_certificate PASSED
cli_anything/wukong/tests/test_core.py::TestCertificate::test_add_certificate PASSED
cli_anything/wukong/tests/test_core.py::TestCertificate::test_review_certificates PASSED
cli_anything/wukong/tests/test_core.py::TestLedger::test_query_detail_account PASSED
cli_anything/wukong/tests/test_core.py::TestLedger::test_query_subject_balance_optional_filters PASSED
cli_anything/wukong/tests/test_core.py::TestCertificateUpdate::test_update_certificate PASSED
cli_anything/wukong/tests/test_core.py::TestCertificateUpdate::test_update_certificate_with_num PASSED
cli_anything/wukong/tests/test_core.py::TestAdjuvant::test_list_adjuvants PASSED
cli_anything/wukong/tests/test_core.py::TestAdjuvant::test_add_adjuvant PASSED
cli_anything/wukong/tests/test_core.py::TestAdjuvant::test_add_adjuvant_default_label PASSED
cli_anything/wukong/tests/test_core.py::TestAdjuvant::test_delete_adjuvant PASSED
cli_anything/wukong/tests/test_core.py::TestStatement::test_query_statement PASSED
cli_anything/wukong/tests/test_core.py::TestStatement::test_close_period PASSED
cli_anything/wukong/tests/test_core.py::TestStatement::test_reopen_period PASSED
cli_anything/wukong/tests/test_full_e2e.py::TestServerConnectivity::test_server_reachable PASSED
cli_anything/wukong/tests/test_full_e2e.py::TestServerConnectivity::test_login_and_whoami PASSED
cli_anything/wukong/tests/test_full_e2e.py::TestAccountSetWorkflow::test_list_accounts PASSED
cli_anything/wukong/tests/test_full_e2e.py::TestAccountSetWorkflow::test_switch_account PASSED
cli_anything/wukong/tests/test_full_e2e.py::TestAccountSetWorkflow::test_get_account_by_id PASSED
cli_anything/wukong/tests/test_full_e2e.py::TestSubjectWorkflow::test_list_subjects PASSED
cli_anything/wukong/tests/test_full_e2e.py::TestSubjectWorkflow::test_list_subjects_tree PASSED
cli_anything/wukong/tests/test_full_e2e.py::TestSubjectWorkflow::test_add_and_delete_subject PASSED
cli_anything/wukong/tests/test_full_e2e.py::TestVoucherWordWorkflow::test_list_voucher_words PASSED
cli_anything/wukong/tests/test_full_e2e.py::TestVoucherWordWorkflow::test_add_and_delete_voucher_word PASSED
cli_anything/wukong/tests/test_full_e2e.py::TestCertificateWorkflow::test_list_certificates PASSED
cli_anything/wukong/tests/test_full_e2e.py::TestCertificateWorkflow::test_certificate_next_num PASSED
cli_anything/wukong/tests/test_full_e2e.py::TestCertificateWorkflow::test_add_review_delete_certificate PASSED
cli_anything/wukong/tests/test_full_e2e.py::TestReports::test_balance_sheet PASSED
cli_anything/wukong/tests/test_full_e2e.py::TestReports::test_income_statement PASSED
cli_anything/wukong/tests/test_full_e2e.py::TestReports::test_balance_check PASSED
cli_anything/wukong/tests/test_full_e2e.py::TestCLISubprocess::test_help PASSED
cli_anything/wukong/tests/test_full_e2e.py::TestCLISubprocess::test_status_json PASSED
cli_anything/wukong/tests/test_full_e2e.py::TestCLISubprocess::test_auth_login_json PASSED
cli_anything/wukong/tests/test_full_e2e.py::TestCLISubprocess::test_account_list_json PASSED
cli_anything/wukong/tests/test_full_e2e.py::TestCertificateUpdate::test_add_and_update_certificate PASSED
cli_anything/wukong/tests/test_full_e2e.py::TestAdjuvantWorkflow::test_list_adjuvants PASSED
cli_anything/wukong/tests/test_full_e2e.py::TestAdjuvantWorkflow::test_add_and_delete_adjuvant PASSED
cli_anything/wukong/tests/test_full_e2e.py::TestStatementWorkflow::test_query_statement_status PASSED
============================== 61 passed in 0.93s ==============================
```

**Result: 61/61 passed (100%)**

### API Discoveries (documented during test development)

| Area | Discovery |
|------|-----------|
| Account setup | `addAccount` creates with `status=0`; must call `saveAccountSet` to activate (`status=1`) |
| Account list | `getAccountSetList` only returns `status=1` accounts; `queryPageList` returns all |
| Subject fields | API uses `number` (not `subjectNumber`) and `type` (not `subjectType`) |
| Certificate details | Field is `certificateDetails` (not `details`); credit field is `creditBalance` (not `ownerBalance`) |
| Certificate delete | Cannot delete reviewed certificates; must un-review (`status=0`) first |
| Certificate next-num | `queryNumByTime` requires date in `yyyyMM` format, not `YYYY-MM-DD` |
| Report periods | `balanceSheetReport` and `incomeStatementReport` require `fromPeriod`/`toPeriod` in `yyyyMM` format |
| Snowflake IDs | API returns IDs as JSON strings; must `int()` before sending back as `List<Long>` |
| `initFinanceData` | **Destructive** — deletes all rows from every finance table including `wk_finance_account_set` |
| Certificate update | `creditBalance` is the correct credit field (not `ownerBalance`); update to current calendar month returns 500 (server bug) |
| Adjuvant labels | 1=客户, 2=供应商, 3=职员, 4=项目, 5=部门, 6=存货, 7=自定义; `deleteById` takes `adjuvantId` as a query param |
| Statement close | `/financeStatement/statement` with `type=1` closes, `type=2` reopens; `queryStatement` returns `settleTime` and `statements` list |
