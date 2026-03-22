"""E2E and subprocess tests for cli-anything-wukong.

Requires the Wukong Accounting server running at http://localhost:44316
with default credentials: admin / 123456

Run:
    pytest cli_anything/wukong/tests/test_full_e2e.py -v -s

Force-installed command (CI):
    CLI_ANYTHING_FORCE_INSTALLED=1 pytest cli_anything/wukong/tests/test_full_e2e.py -v -s
"""

import json
import os
import subprocess
import sys

import pytest
import requests

from cli_anything.wukong.utils.wukong_backend import (
    WukongClient,
    WukongConnectionError,
    WukongAPIError,
)
from cli_anything.wukong.core import (
    auth as _auth,
    account as _account,
    subject as _subject,
    voucher_word as _voucher,
    certificate as _cert,
    ledger as _ledger,
    report as _report,
)

# ── Config ─────────────────────────────────────────────────────────────

WUKONG_URL = os.environ.get("WUKONG_URL", "http://localhost:44316")
ADMIN_USER = os.environ.get("WUKONG_USER", "admin")
ADMIN_PASS = os.environ.get("WUKONG_PASS", "123456")


def _resolve_cli(name):
    """Resolve installed CLI command; falls back to python -m for dev.

    Set env CLI_ANYTHING_FORCE_INSTALLED=1 to require the installed command.
    """
    import shutil
    force = os.environ.get("CLI_ANYTHING_FORCE_INSTALLED", "").strip() == "1"
    path = shutil.which(name)
    if path:
        print(f"\n[_resolve_cli] Using installed command: {path}")
        return [path]
    if force:
        raise RuntimeError(f"{name} not found in PATH. Install with: pip install -e .")
    module = "cli_anything.wukong.wukong_cli"
    print(f"\n[_resolve_cli] Falling back to: {sys.executable} -m {module}")
    return [sys.executable, "-m", module]


# ── Fixtures ──────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def live_client():
    """Authenticated WukongClient for the live server."""
    client = WukongClient(base_url=WUKONG_URL)
    try:
        token = _auth.login(client, ADMIN_USER, ADMIN_PASS)
    except WukongConnectionError:
        pytest.skip(f"Wukong server not reachable at {WUKONG_URL}")
    except WukongAPIError as e:
        pytest.fail(f"Login failed: {e}")
    client.token = token
    return client


@pytest.fixture(scope="session")
def active_account_id(live_client):
    """Ensure at least one active account set exists and return its ID.

    Setup flow:
    1. Check getAccountSetList for active (status=1) accounts
    2. If none, check queryPageList for unconfigured accounts and activate one
    3. If still none, create a new account set and activate it
    """
    accounts = _account.list_accounts(live_client)
    if not accounts:
        # Look for unconfigured accounts (status=0) via admin endpoint
        all_accounts = _account.list_all_accounts(live_client)
        if all_accounts:
            acc = all_accounts[0]
            account_id = int(acc["accountId"])
        else:
            # Create a fresh account set
            account_id = _account.create_account(live_client, "CLI测试公司")
        # Activate: switch → discover currency → saveAccountSet (sets status=1)
        _account.configure_account(live_client, account_id, start_time="2026-01-01")
        accounts = _account.list_accounts(live_client)
        if not accounts:
            pytest.fail("Could not create or activate an account set")

    acc = accounts[0]
    account_id = int(acc.get("accountSetId") or acc.get("accountId"))
    _account.switch_account(live_client, account_id)

    # Ensure at least one voucher word exists
    words = _voucher.list_voucher_words(live_client)
    if not words:
        for name in ["记", "收", "付", "借"]:
            try:
                _voucher.add_voucher_word(live_client, name)
            except Exception:
                pass

    return account_id


# ── Server connectivity ────────────────────────────────────────────────

class TestServerConnectivity:
    def test_server_reachable(self):
        """Server must be running — no graceful degradation."""
        client = WukongClient(base_url=WUKONG_URL)
        up = client.health_check()
        if not up:
            pytest.fail(
                f"Wukong server is NOT reachable at {WUKONG_URL}.\n"
                f"Start it with: java -jar finance/finance-web/target/finance-web-0.0.1-SNAPSHOT.jar"
            )
        assert up is True
        print(f"\n  Server: {WUKONG_URL} — reachable")

    def test_login_and_whoami(self, live_client):
        """Login must succeed and whoami must return the user."""
        assert live_client.token is not None
        user = _auth.whoami(live_client)
        assert user.get("userId") is not None
        print(f"\n  Logged in as: {user.get('username')} (ID={user.get('userId')})")


# ── Account set workflow ───────────────────────────────────────────────

class TestAccountSetWorkflow:
    def test_list_accounts(self, live_client, active_account_id):
        accounts = _account.list_accounts(live_client)
        assert isinstance(accounts, list)
        assert len(accounts) >= 1
        print(f"\n  Account sets: {len(accounts)}")
        for a in accounts:
            name = a.get("accountName") or a.get("name") or a.get("companyName")
            aid = a.get("accountSetId") or a.get("accountId")
            print(f"    [{aid}] {name}")

    def test_switch_account(self, live_client, active_account_id):
        # Should not raise
        _account.switch_account(live_client, active_account_id)
        print(f"\n  Switched to account set: {active_account_id}")

    def test_get_account_by_id(self, live_client, active_account_id):
        acc = _account.get_account(live_client, active_account_id)
        assert acc is not None
        assert isinstance(acc, dict)
        print(f"\n  Account: {acc}")


# ── Subject workflow ───────────────────────────────────────────────────

class TestSubjectWorkflow:
    def test_list_subjects(self, live_client, active_account_id):
        subjects = _subject.list_subjects(live_client)
        assert isinstance(subjects, list)
        print(f"\n  Subjects: {len(subjects)}")
        for s in subjects[:5]:
            print(f"    [{s.get('subjectId')}] {s.get('subjectNumber')} {s.get('subjectName')}")

    def test_list_subjects_tree(self, live_client, active_account_id):
        subjects = _subject.list_subjects(live_client, is_tree=1)
        assert isinstance(subjects, list)
        print(f"\n  Subject tree root nodes: {len(subjects)}")

    def test_add_and_delete_subject(self, live_client, active_account_id):
        """Add a test subject, verify it appears, then delete it.

        Note: The API uses "number" (not "subjectNumber") and "type" (not "subjectType")
        in both the request BO and response VO.
        """
        import uuid
        # Use a unique name to avoid conflicts from prior test runs
        test_code = f"9{uuid.uuid4().hex[:3].upper()}"
        test_name = f"CLI-Test-{test_code}"

        # First clean up any orphaned test subjects from previous runs
        subjects_before = _subject.list_subjects(live_client)
        stale = [s for s in subjects_before if str(s.get("subjectName", "")).startswith("CLI-Test-")]
        if stale:
            _subject.delete_subjects(live_client, [s["subjectId"] for s in stale])
            print(f"\n  Cleaned up {len(stale)} stale test subject(s)")

        _subject.add_subject(live_client, test_code, test_name, subject_type=1)

        # Verify it appears — field is "number" in the response VO
        subjects = _subject.list_subjects(live_client)
        found = next((s for s in subjects if s.get("number") == test_code), None)
        assert found is not None, f"Subject {test_code} not found after creation"
        print(f"\n  Created subject: [{found.get('subjectId')}] {test_code} {test_name}")

        # Clean up
        _subject.delete_subjects(live_client, [found["subjectId"]])
        subjects_after = _subject.list_subjects(live_client)
        still_there = any(s.get("number") == test_code for s in subjects_after)
        assert not still_there, f"Subject {test_code} still present after deletion"
        print(f"  Deleted subject: {test_code}")


# ── Voucher word workflow ──────────────────────────────────────────────

class TestVoucherWordWorkflow:
    def test_list_voucher_words(self, live_client, active_account_id):
        words = _voucher.list_voucher_words(live_client)
        assert isinstance(words, list)
        print(f"\n  Voucher words: {[w.get('voucherName') for w in words]}")

    def test_add_and_delete_voucher_word(self, live_client, active_account_id):
        test_name = "测试字"
        _voucher.add_voucher_word(live_client, test_name)

        words = _voucher.list_voucher_words(live_client)
        found = next((w for w in words if w.get("voucherName") == test_name), None)
        assert found is not None, f"Voucher word '{test_name}' not found after creation"
        print(f"\n  Created voucher word: [{found.get('voucherId')}] {test_name}")

        _voucher.delete_voucher_word(live_client, found["voucherId"])
        words_after = _voucher.list_voucher_words(live_client)
        still_there = any(w.get("voucherName") == test_name for w in words_after)
        assert not still_there
        print(f"  Deleted voucher word: {test_name}")


# ── Certificate workflow ───────────────────────────────────────────────

class TestCertificateWorkflow:
    def test_list_certificates(self, live_client, active_account_id):
        result = _cert.list_certificates(live_client, page_no=1, page_size=10)
        assert isinstance(result, dict)
        records = result.get("records") or result.get("list") or []
        total = result.get("total", 0)
        print(f"\n  Certificates total: {total}, fetched: {len(records)}")

    def test_certificate_next_num(self, live_client, active_account_id):
        words = _voucher.list_voucher_words(live_client)
        if not words:
            pytest.skip("No voucher words available")
        voucher_id = words[0]["voucherId"]
        result = _cert.get_next_certificate_num(live_client, voucher_id, "2026-03-01")
        assert result is not None
        print(f"\n  Next certificate num: {result}")

    def test_add_review_delete_certificate(self, live_client, active_account_id):
        """Full certificate lifecycle: add → list → review → delete."""
        words = _voucher.list_voucher_words(live_client)
        subjects = _subject.list_subjects(live_client)
        if not words:
            pytest.skip("No voucher words available")
        if len(subjects) < 2:
            pytest.skip("Need at least 2 subjects for a balanced entry")

        # Find two subjects for debit/credit
        s1, s2 = subjects[0], subjects[1]
        voucher_id = words[0]["voucherId"]

        details = [
            {
                "subjectId": s1["subjectId"],
                "digestContent": "CLI test entry - debit",
                "debtorBalance": 500.0,
                "creditBalance": 0.0,
            },
            {
                "subjectId": s2["subjectId"],
                "digestContent": "CLI test entry - credit",
                "debtorBalance": 0.0,
                "creditBalance": 500.0,
            },
        ]

        # Add
        result = _cert.add_certificate(live_client, voucher_id, "2026-03-01", details)
        cert_id = result.get("certificateId") if isinstance(result, dict) else None
        print(f"\n  Created certificate: ID={cert_id}")
        assert cert_id is not None, f"Certificate creation returned: {result}"

        # Get
        fetched = _cert.get_certificate(live_client, cert_id)
        assert fetched.get("certificateId") == cert_id
        print(f"  Fetched certificate: {fetched.get('certificateId')}")

        # Review (approve)
        _cert.review_certificates(live_client, [cert_id], 1)
        print(f"  Reviewed certificate: {cert_id}")

        # Un-review before delete (reviewed certificates cannot be deleted)
        _cert.review_certificates(live_client, [cert_id], 0)

        # Delete
        _cert.delete_certificates(live_client, [cert_id])
        print(f"  Deleted certificate: {cert_id}")


# ── Report tests ───────────────────────────────────────────────────────

class TestReports:
    def test_balance_sheet(self, live_client, active_account_id):
        # Use current month within the account set's active period (started 2026-01)
        rows = _report.balance_sheet(live_client, 1, "2026-03-31")
        assert isinstance(rows, list)
        print(f"\n  Balance sheet rows: {len(rows)}")
        if rows:
            print(f"  Sample row keys: {list(rows[0].keys())}")

    def test_income_statement(self, live_client, active_account_id):
        rows = _report.income_statement(live_client, 1, "2026-03-31")
        assert isinstance(rows, list)
        print(f"\n  Income statement rows: {len(rows)}")

    def test_balance_check(self, live_client, active_account_id):
        # Use the account start period (202601) — current month has a known
        # server-side bug when unreviewed certificate totals trigger the
        # CashFlowStatementReportHolder path.
        result = _report.balance_sheet_check(live_client, 1, "2026-01-31")
        assert isinstance(result, dict)
        print(f"\n  Balance check result: {result}")


# ── CLI subprocess tests ───────────────────────────────────────────────

class TestCLISubprocess:
    CLI_BASE = _resolve_cli("cli-anything-wukong")

    def _run(self, args: list, check: bool = True, input_text: str = None) -> subprocess.CompletedProcess:
        env = os.environ.copy()
        env["WUKONG_URL"] = WUKONG_URL
        return subprocess.run(
            self.CLI_BASE + args,
            capture_output=True,
            text=True,
            check=check,
            env=env,
        )

    def test_help(self):
        result = self._run(["--help"])
        assert result.returncode == 0
        assert "wukong" in result.stdout.lower() or "accounting" in result.stdout.lower()
        print(f"\n  --help output length: {len(result.stdout)} chars")

    def test_status_json(self):
        result = self._run(["--json", "status"])
        assert result.returncode == 0
        data = json.loads(result.stdout)
        assert "server_url" in data
        assert "server_reachable" in data
        assert "authenticated" in data
        print(f"\n  Status: {data}")

    def test_auth_login_json(self):
        result = self._run(["--json", "auth", "login", "-u", ADMIN_USER, "-p", ADMIN_PASS])
        assert result.returncode == 0, f"Login failed: {result.stderr}"
        data = json.loads(result.stdout)
        assert "token" in data
        assert len(data["token"]) > 0
        print(f"\n  Login token: {data['token'][:8]}...")

    def test_account_list_json(self):
        # Login first
        self._run(["auth", "login", "-u", ADMIN_USER, "-p", ADMIN_PASS])

        result = self._run(["--json", "account", "list"])
        assert result.returncode == 0, f"Account list failed: {result.stderr}"
        data = json.loads(result.stdout)
        assert isinstance(data, list)
        print(f"\n  Account sets: {len(data)}")
        for a in data:
            print(f"    {a}")
