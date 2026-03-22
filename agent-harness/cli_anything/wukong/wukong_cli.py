"""cli-anything-wukong — CLI harness for Wukong Accounting (悟空财务).

Usage:
    cli-anything-wukong                          # enter REPL
    cli-anything-wukong --url http://HOST:PORT   # custom server URL
    cli-anything-wukong --json auth login -u admin -p 123456
    cli-anything-wukong account list
    cli-anything-wukong subject list
    cli-anything-wukong certificate list --start 202401 --end 202412
    cli-anything-wukong report balance-sheet --period month --date 2024-06-30
"""

import json
import re
import shlex
import sys
from typing import Optional

import click

from cli_anything.wukong.core import (
    session as _session,
    auth as _auth,
    account as _account,
    subject as _subject,
    voucher_word as _voucher,
    certificate as _cert,
    ledger as _ledger,
    report as _report,
    adjuvant as _adjuvant,
    statement as _statement,
)
from cli_anything.wukong.utils.wukong_backend import (
    WukongClient,
    WukongError,
    WukongAuthError,
    WukongConnectionError,
)
from cli_anything.wukong.utils.repl_skin import ReplSkin

_VERSION = "1.0.0"
_skin = ReplSkin("wukong", version=_VERSION)

# ── Period type mapping ────────────────────────────────────────────────

_PERIOD_MAP = {"month": 1, "quarter": 2, "year": 3}

# ── Context helpers ────────────────────────────────────────────────────


def _get_client(ctx: click.Context) -> WukongClient:
    """Build client from context (url + token from session).

    URL priority: --url flag > WUKONG_URL env var > session file > default.
    """
    url = ctx.obj.get("url") or _session.get_base_url()
    token = _session.get_token()
    return WukongClient(base_url=url, token=token)


def _out(ctx: click.Context, data, text: str = ""):
    """Output data as JSON or human-readable text."""
    if ctx.obj.get("json"):
        click.echo(json.dumps(data, ensure_ascii=False, indent=2, default=str))
    else:
        click.echo(text or str(data))


def _err(ctx: click.Context, message: str, data: dict = None):
    """Output error."""
    if ctx.obj.get("json"):
        click.echo(json.dumps({"error": message, **(data or {})}, ensure_ascii=False), err=True)
    else:
        _skin.error(message)


def _handle_error(ctx: click.Context, exc: WukongError):
    _err(ctx, str(exc))
    sys.exit(1)


# ── Root CLI group ─────────────────────────────────────────────────────


@click.group(invoke_without_command=True, context_settings={"help_option_names": ["-h", "--help"]})
@click.option("--url", default=None, help="Wukong server URL (default: http://localhost:44316)")
@click.option("--json", "use_json", is_flag=True, default=False, help="Output as JSON")
@click.version_option(_VERSION, "--version", "-V")
@click.pass_context
def cli(ctx: click.Context, url: Optional[str], use_json: bool):
    """cli-anything-wukong — command-line interface for Wukong Accounting (悟空财务).

    Run without a subcommand to enter the interactive REPL.

    The Wukong server must be running at the configured URL.
    Default server: http://localhost:44316
    """
    ctx.ensure_object(dict)
    ctx.obj["url"] = url
    ctx.obj["json"] = use_json

    if ctx.invoked_subcommand is None:
        ctx.invoke(repl)


# ── REPL ───────────────────────────────────────────────────────────────


@cli.command(hidden=True)
@click.pass_context
def repl(ctx: click.Context):
    """Start the interactive REPL."""
    _skin.print_banner()

    commands_help = {
        "auth login":        "Login with username and password",
        "auth logout":       "Logout (clear session)",
        "auth whoami":       "Show current user",
        "account list":      "List account sets (账套)",
        "account switch":    "Switch active account set",
        "account create":    "Create a new account set",
        "subject list":      "List subjects / account codes (科目)",
        "subject add":       "Add a subject",
        "voucher list":      "List voucher words (凭证字)",
        "certificate list":  "List journal entries (凭证)",
        "certificate add":   "Add a journal entry",
        "certificate get":   "Get a certificate by ID",
        "certificate review":"Review/approve certificates",
        "certificate update":"Update an existing certificate",
        "adjuvant list":     "List auxiliary accounting categories (辅助核算)",
        "adjuvant add":      "Add an auxiliary accounting category",
        "adjuvant delete":   "Delete an auxiliary accounting category",
        "statement status":  "Query period closing status (结账状态)",
        "statement close":   "Close the accounting period (结账)",
        "statement reopen":  "Reopen a closed period (反结账)",
        "ledger detail":     "Detail ledger (明细账)",
        "ledger general":    "General ledger (总账)",
        "ledger balance":    "Subject balance table (科目余额表)",
        "report balance-sheet": "Balance sheet (资产负债表)",
        "report income":     "Income statement (利润表)",
        "report cash-flow":  "Cash flow statement (现金流量表)",
        "status":            "Check server connection",
        "help":              "Show this help",
        "quit / exit":       "Exit the REPL",
    }

    pt_session = _skin.create_prompt_session()
    sess = _session.load_session()

    while True:
        try:
            token = sess.get("token")
            account_id = sess.get("account_id")
            context = f"account:{account_id}" if account_id else ("logged-in" if token else "not-logged-in")
            line = _skin.get_input(pt_session, context=context)
        except (EOFError, KeyboardInterrupt):
            _skin.print_goodbye()
            break

        if not line:
            continue
        if line in ("quit", "exit", "q"):
            _skin.print_goodbye()
            break
        if line == "help":
            _skin.help(commands_help)
            continue

        try:
            args = shlex.split(line)
        except ValueError as e:
            _skin.error(f"Parse error: {e}")
            continue

        try:
            standalone = cli.make_context(
                "cli-anything-wukong",
                args,
                parent=ctx,
                obj=ctx.obj.copy(),
            )
            with standalone:
                cli.invoke(standalone)
        except SystemExit:
            pass
        except click.ClickException as e:
            _skin.error(e.format_message())
        except WukongConnectionError as e:
            _skin.error(str(e))
        except WukongAuthError as e:
            _skin.error(str(e))
        except WukongError as e:
            _skin.error(str(e))
        except Exception as e:
            _skin.error(f"Unexpected error: {e}")

        sess = _session.load_session()


# ── status ─────────────────────────────────────────────────────────────


@cli.command()
@click.pass_context
def status(ctx: click.Context):
    """Check server connection and session status."""
    sess = _session.load_session()
    base_url = ctx.obj.get("url") or sess.get("base_url", "http://localhost:44316")
    client = WukongClient(base_url=base_url)
    up = client.health_check()

    token = sess.get("token")
    account_id = sess.get("account_id")

    if ctx.obj.get("json"):
        _out(ctx, {
            "server_url": base_url,
            "server_reachable": up,
            "authenticated": bool(token),
            "token": token,
            "active_account_id": account_id,
        })
    else:
        _skin.status("Server URL", base_url)
        _skin.status("Server", "reachable" if up else "UNREACHABLE")
        _skin.status("Authenticated", "yes" if token else "no")
        if account_id:
            _skin.status("Active account", str(account_id))


# ── auth group ─────────────────────────────────────────────────────────


@cli.group()
def auth():
    """Authentication commands (login, logout, whoami)."""


@auth.command("login")
@click.option("-u", "--username", required=True, help="Username")
@click.option("-p", "--password", required=True, help="Password")
@click.pass_context
def auth_login(ctx: click.Context, username: str, password: str):
    """Login and save auth token to session."""
    client = _get_client(ctx)
    try:
        token = _auth.login(client, username, password)
    except WukongError as e:
        _handle_error(ctx, e)
        return
    _session.set_token(token)
    if ctx.obj.get("url"):
        _session.set_base_url(ctx.obj["url"])
    if ctx.obj.get("json"):
        _out(ctx, {"token": token, "username": username})
    else:
        _skin.success(f"Logged in as {username}")
        _skin.info("Token saved. Run: cli-anything-wukong account list")


@auth.command("logout")
@click.pass_context
def auth_logout(ctx: click.Context):
    """Logout and clear local session."""
    client = _get_client(ctx)
    try:
        _auth.logout(client)
    except WukongError:
        pass
    _session.clear_session()
    if ctx.obj.get("json"):
        _out(ctx, {"logged_out": True})
    else:
        _skin.success("Logged out")


@auth.command("whoami")
@click.pass_context
def auth_whoami(ctx: click.Context):
    """Show current logged-in user."""
    client = _get_client(ctx)
    try:
        user = _auth.whoami(client)
    except WukongError as e:
        _handle_error(ctx, e)
        return
    if ctx.obj.get("json"):
        _out(ctx, user)
    else:
        if user.get("userId"):
            _skin.status("User ID", str(user.get("userId")))
            _skin.status("Username", user.get("username", ""))
            _skin.status("Nickname", user.get("nickname", ""))
            _skin.status("Admin", str(user.get("isAdmin", False)))
        else:
            _skin.warning("Not logged in")


# ── account group ──────────────────────────────────────────────────────


@cli.group()
def account():
    """Account set (账套) management."""


@account.command("list")
@click.pass_context
def account_list(ctx: click.Context):
    """List all accessible account sets."""
    client = _get_client(ctx)
    try:
        accounts = _account.list_accounts(client)
    except WukongError as e:
        _handle_error(ctx, e)
        return
    if ctx.obj.get("json"):
        _out(ctx, accounts)
    else:
        if not accounts:
            _skin.warning("No account sets found")
            return
        active_id = _session.get_account_id()
        headers = ["ID", "Name", "Company", "Start Date", "Active"]
        rows = []
        for a in accounts:
            aid = a.get("accountSetId") or a.get("accountId")
            rows.append([
                str(aid or ""),
                a.get("accountName") or a.get("name", ""),
                a.get("companyName", ""),
                a.get("startDate") or a.get("enableDate", ""),
                "*" if str(aid) == str(active_id) else "",
            ])
        _skin.table(headers, rows)


@account.command("switch")
@click.argument("account_id", type=int)
@click.pass_context
def account_switch(ctx: click.Context, account_id: int):
    """Switch active account set by ID."""
    client = _get_client(ctx)
    try:
        _account.switch_account(client, account_id)
    except WukongError as e:
        _handle_error(ctx, e)
        return
    _session.set_account_id(account_id)
    if ctx.obj.get("json"):
        _out(ctx, {"account_id": account_id, "switched": True})
    else:
        _skin.success(f"Switched to account set {account_id}")


@account.command("create")
@click.option("--name", required=True, help="Account set name")
@click.option("--company", required=True, help="Company name")
@click.option("--start", required=True, help="Start date (YYYY-MM)")
@click.option("--currency", default="CNY", show_default=True, help="Currency code")
@click.pass_context
def account_create(ctx: click.Context, name: str, company: str, start: str, currency: str):
    """Create a new account set."""
    if not re.fullmatch(r"\d{4}-(0[1-9]|1[0-2])", start):
        _err(ctx, f"--start must be in YYYY-MM format (e.g. 2024-01), got: {start!r}")
        sys.exit(1)
    client = _get_client(ctx)
    try:
        _account.create_account(client, name, company, start, currency)
    except WukongError as e:
        _handle_error(ctx, e)
        return
    if ctx.obj.get("json"):
        _out(ctx, {"created": True, "name": name})
    else:
        _skin.success(f"Created account set: {name}")


@account.command("init")
@click.pass_context
def account_init(ctx: click.Context):
    """Initialize default data (subjects, voucher words) for active account set."""
    client = _get_client(ctx)
    try:
        _account.init_finance_data(client)
    except WukongError as e:
        _handle_error(ctx, e)
        return
    if ctx.obj.get("json"):
        _out(ctx, {"initialized": True})
    else:
        _skin.success("Finance data initialized")


# ── subject group ──────────────────────────────────────────────────────


_SUBJECT_TYPE_NAMES = {
    1: "资产(Assets)",
    2: "负债(Liabilities)",
    3: "权益(Equity)",
    4: "成本(Cost)",
    5: "损益(P&L)",
}


@cli.group()
def subject():
    """Subject / account code (科目) management."""


@subject.command("list")
@click.option("--type", "subject_type", type=int, default=None,
              help="Type: 1=资产 2=负债 3=权益 4=成本 5=损益")
@click.option("--tree", is_flag=True, default=False, help="Return as tree structure")
@click.pass_context
def subject_list(ctx: click.Context, subject_type: Optional[int], tree: bool):
    """List subjects (account codes)."""
    client = _get_client(ctx)
    try:
        subjects = _subject.list_subjects(client, subject_type=subject_type, is_tree=1 if tree else 0)
    except WukongError as e:
        _handle_error(ctx, e)
        return
    if ctx.obj.get("json"):
        _out(ctx, subjects)
    else:
        if not subjects:
            _skin.warning("No subjects found")
            return
        headers = ["ID", "Code", "Name", "Type", "Level", "Enabled"]
        rows = _flatten_subjects(subjects)
        _skin.table(headers, rows)


def _flatten_subjects(subjects: list, indent: int = 0) -> list:
    rows = []
    for s in subjects:
        type_id = s.get("subjectType") or s.get("type")
        rows.append([
            str(s.get("subjectId", "")),
            ("  " * indent) + str(s.get("subjectNumber", "")),
            s.get("subjectName", ""),
            _SUBJECT_TYPE_NAMES.get(type_id, str(type_id or "")),
            str(s.get("grade") or s.get("level", "")),
            "yes" if s.get("status") == 1 else "no",
        ])
        children = s.get("children") or []
        rows.extend(_flatten_subjects(children, indent + 1))
    return rows


@subject.command("add")
@click.option("--code", required=True, help="Account code (e.g. 1001)")
@click.option("--name", required=True, help="Account name (e.g. 库存现金)")
@click.option("--type", "subject_type", required=True, type=int,
              help="1=资产 2=负债 3=权益 4=成本 5=损益")
@click.option("--direction", "balance_direction", required=True, type=int,
              help="Balance direction: 1=借方(debit) 2=贷方(credit)")
@click.option("--parent-id", type=int, default=None, help="Parent subject ID")
@click.pass_context
def subject_add(ctx: click.Context, code: str, name: str, subject_type: int,
                balance_direction: int, parent_id: Optional[int]):
    """Add a new subject (account code).

    --direction is required: 1=借方(debit), 2=贷方(credit).
    --type must be 1–5: 1=资产 2=负债 3=权益 4=成本 5=损益.
    """
    if subject_type not in (1, 2, 3, 4, 5):
        _err(ctx, f"--type must be 1–5 (got {subject_type}): 1=资产 2=负债 3=权益 4=成本 5=损益")
        sys.exit(1)
    if balance_direction not in (1, 2):
        _err(ctx, f"--direction must be 1 (借方/debit) or 2 (贷方/credit) (got {balance_direction})")
        sys.exit(1)
    client = _get_client(ctx)
    try:
        _subject.add_subject(client, code, name, subject_type, balance_direction, parent_id=parent_id)
    except WukongError as e:
        _handle_error(ctx, e)
        return
    if ctx.obj.get("json"):
        _out(ctx, {"created": True, "code": code, "name": name})
    else:
        _skin.success(f"Added subject: {code} {name}")


@subject.command("delete")
@click.argument("subject_ids", nargs=-1, type=int, required=True)
@click.pass_context
def subject_delete(ctx: click.Context, subject_ids: tuple):
    """Delete subjects by ID."""
    client = _get_client(ctx)
    try:
        _subject.delete_subjects(client, list(subject_ids))
    except WukongError as e:
        _handle_error(ctx, e)
        return
    if ctx.obj.get("json"):
        _out(ctx, {"deleted": list(subject_ids)})
    else:
        _skin.success(f"Deleted {len(subject_ids)} subject(s)")


# ── voucher group ──────────────────────────────────────────────────────


@cli.group()
def voucher():
    """Voucher word (凭证字) management."""


@voucher.command("list")
@click.pass_context
def voucher_list(ctx: click.Context):
    """List all voucher words (e.g. 记, 付, 收)."""
    client = _get_client(ctx)
    try:
        words = _voucher.list_voucher_words(client)
    except WukongError as e:
        _handle_error(ctx, e)
        return
    if ctx.obj.get("json"):
        _out(ctx, words)
    else:
        if not words:
            _skin.warning("No voucher words found")
            return
        headers = ["ID", "Name", "Sort"]
        rows = [[str(w.get("voucherId", "")), w.get("voucherName", ""), str(w.get("sort", ""))] for w in words]
        _skin.table(headers, rows)


@voucher.command("add")
@click.argument("name")
@click.pass_context
def voucher_add(ctx: click.Context, name: str):
    """Add a voucher word (e.g. '记')."""
    if not name.strip():
        _err(ctx, "凭证字不能为空 (voucher word name must not be blank)")
        sys.exit(1)
    client = _get_client(ctx)
    try:
        _voucher.add_voucher_word(client, name)
    except WukongError as e:
        _handle_error(ctx, e)
        return
    if ctx.obj.get("json"):
        _out(ctx, {"created": True, "name": name})
    else:
        _skin.success(f"Added voucher word: {name}")


@voucher.command("delete")
@click.argument("voucher_id", type=int)
@click.pass_context
def voucher_delete(ctx: click.Context, voucher_id: int):
    """Delete a voucher word by ID."""
    client = _get_client(ctx)
    try:
        _voucher.delete_voucher_word(client, voucher_id)
    except WukongError as e:
        _handle_error(ctx, e)
        return
    if ctx.obj.get("json"):
        _out(ctx, {"deleted": voucher_id})
    else:
        _skin.success(f"Deleted voucher word {voucher_id}")


# ── certificate group ──────────────────────────────────────────────────


@cli.group()
def certificate():
    """Journal entry / certificate (凭证) operations."""


@certificate.command("list")
@click.option("--start", default=None, help="Start period yyyyMM (e.g. 202401)")
@click.option("--end", default=None, help="End period yyyyMM (e.g. 202412)")
@click.option("--voucher-id", type=int, default=None, help="Filter by voucher word ID")
@click.option("--status", "check_status", type=int, default=None, help="0=unreviewed 1=reviewed")
@click.option("--page", default=1, show_default=True, help="Page number")
@click.option("--size", default=20, show_default=True, help="Page size")
@click.pass_context
def certificate_list(ctx: click.Context, start, end, voucher_id, check_status, page, size):
    """List journal entry certificates.

    --start and --end must be in yyyyMM format (e.g. 202401).
    The backend compares periods as strings in that format.
    """
    _period_re = re.compile(r"^\d{4}(0[1-9]|1[0-2])$")
    if start and not _period_re.match(start):
        _err(ctx, f"--start must be yyyyMM (e.g. 202401), got: {start!r}")
        sys.exit(1)
    if end and not _period_re.match(end):
        _err(ctx, f"--end must be yyyyMM (e.g. 202412), got: {end!r}")
        sys.exit(1)
    client = _get_client(ctx)
    try:
        result = _cert.list_certificates(client, start, end, voucher_id, check_status, page, size)
    except WukongError as e:
        _handle_error(ctx, e)
        return
    records = result.get("records") or result.get("list") or []
    total = result.get("total", len(records))
    if ctx.obj.get("json"):
        _out(ctx, {"total": total, "records": records})
    else:
        if not records:
            _skin.warning("No certificates found")
            return
        _skin.info(f"Total: {total}")
        headers = ["ID", "Date", "Voucher", "Num", "Debit", "Credit", "Status"]
        rows = []
        for r in records:
            rows.append([
                str(r.get("certificateId", "")),
                str(r.get("certificateTime", ""))[:10],
                r.get("voucherName", ""),
                str(r.get("certificateNum", "")),
                str(r.get("debtorBalance", "")),
                str(r.get("ownerBalance", "")),
                "reviewed" if r.get("checkStatus") == 1 else "pending",
            ])
        _skin.table(headers, rows)


@certificate.command("get")
@click.argument("certificate_id", type=int)
@click.pass_context
def certificate_get(ctx: click.Context, certificate_id: int):
    """Get certificate detail by ID."""
    client = _get_client(ctx)
    try:
        cert = _cert.get_certificate(client, certificate_id)
    except WukongError as e:
        _handle_error(ctx, e)
        return
    if ctx.obj.get("json"):
        _out(ctx, cert)
    else:
        _skin.status("ID", str(cert.get("certificateId", "")))
        _skin.status("Date", str(cert.get("certificateTime", ""))[:10])
        _skin.status("Voucher", cert.get("voucherName", ""))
        _skin.status("Number", str(cert.get("certificateNum", "")))
        details = cert.get("details") or []
        if details:
            _skin.section("Details")
            headers = ["Subject Code", "Subject Name", "Summary", "Debit", "Credit"]
            rows = []
            for d in details:
                rows.append([
                    d.get("subjectNumber", ""),
                    d.get("subjectName", ""),
                    d.get("digestContent", ""),
                    str(d.get("debtorBalance") or ""),
                    str(d.get("ownerBalance") or ""),
                ])
            _skin.table(headers, rows)


@certificate.command("add")
@click.option("--voucher-id", required=True, type=int, help="Voucher word ID")
@click.option("--date", required=True, help="Certificate date (YYYY-MM-DD)")
@click.option("--detail", "details_json", required=True,
              help='Details as JSON array: \'[{"subjectId":1,"digestContent":"memo","debtorBalance":1000,"ownerBalance":0}]\'')
@click.pass_context
def certificate_add(ctx: click.Context, voucher_id: int, date: str, details_json: str):
    """Add a new journal entry certificate.

    Each detail line requires: subjectId, digestContent, debtorBalance, ownerBalance.
    Total debits must equal total credits.
    """
    try:
        details = json.loads(details_json)
    except json.JSONDecodeError as e:
        _skin.error(f"Invalid JSON for --detail: {e}")
        sys.exit(1)
    client = _get_client(ctx)
    try:
        result = _cert.add_certificate(client, voucher_id, date, details)
    except ValueError as e:
        _err(ctx, str(e))
        sys.exit(1)
    except WukongError as e:
        _handle_error(ctx, e)
        return
    cert_id = result.get("certificateId") if isinstance(result, dict) else None
    if ctx.obj.get("json"):
        _out(ctx, result if isinstance(result, dict) else {"created": True})
    else:
        _skin.success(f"Certificate created" + (f" (ID: {cert_id})" if cert_id else ""))


@certificate.command("delete")
@click.argument("certificate_ids", nargs=-1, type=int, required=True)
@click.pass_context
def certificate_delete(ctx: click.Context, certificate_ids: tuple):
    """Delete certificates by ID."""
    client = _get_client(ctx)
    try:
        _cert.delete_certificates(client, list(certificate_ids))
    except WukongError as e:
        _handle_error(ctx, e)
        return
    if ctx.obj.get("json"):
        _out(ctx, {"deleted": list(certificate_ids)})
    else:
        _skin.success(f"Deleted {len(certificate_ids)} certificate(s)")


@certificate.command("review")
@click.argument("certificate_ids", nargs=-1, type=int, required=True)
@click.option("--approve/--unapprove", default=True, help="Approve or unapprove")
@click.pass_context
def certificate_review(ctx: click.Context, certificate_ids: tuple, approve: bool):
    """Review (approve or unapprove) certificates."""
    client = _get_client(ctx)
    status_val = 1 if approve else 0
    try:
        _cert.review_certificates(client, list(certificate_ids), status_val)
    except WukongError as e:
        _handle_error(ctx, e)
        return
    action = "approved" if approve else "unapproved"
    if ctx.obj.get("json"):
        _out(ctx, {"action": action, "ids": list(certificate_ids)})
    else:
        _skin.success(f"{action.capitalize()} {len(certificate_ids)} certificate(s)")


@certificate.command("next-num")
@click.option("--voucher-id", required=True, type=int, help="Voucher word ID")
@click.option("--date", required=True, help="Certificate date (YYYY-MM-DD)")
@click.pass_context
def certificate_next_num(ctx: click.Context, voucher_id: int, date: str):
    """Get the next available certificate number for a voucher + date."""
    client = _get_client(ctx)
    try:
        result = _cert.get_next_certificate_num(client, voucher_id, date)
    except WukongError as e:
        _handle_error(ctx, e)
        return
    num = result.get("certificateNum") if isinstance(result, dict) else result
    if ctx.obj.get("json"):
        _out(ctx, result)
    else:
        _skin.status("Next certificate number", str(num))


@certificate.command("update")
@click.option("--id", "certificate_id", required=True, type=int, help="Certificate ID to update")
@click.option("--voucher-id", required=True, type=int, help="Voucher word ID")
@click.option("--date", required=True, help="Certificate date (YYYY-MM-DD)")
@click.option("--detail", "details_json", required=True,
              help='Details as JSON array: \'[{"subjectId":1,"digestContent":"memo","debtorBalance":1000,"ownerBalance":0}]\'')
@click.pass_context
def certificate_update(ctx: click.Context, certificate_id: int, voucher_id: int, date: str, details_json: str):
    """Update an existing journal entry certificate.

    Each detail line requires: subjectId, digestContent, debtorBalance, ownerBalance.
    Total debits must equal total credits.
    """
    try:
        details = json.loads(details_json)
    except json.JSONDecodeError as e:
        _skin.error(f"Invalid JSON for --detail: {e}")
        sys.exit(1)
    client = _get_client(ctx)
    try:
        _cert.update_certificate(client, certificate_id, voucher_id, date, details)
    except ValueError as e:
        _err(ctx, str(e))
        sys.exit(1)
    except WukongError as e:
        _handle_error(ctx, e)
        return
    if ctx.obj.get("json"):
        _out(ctx, {"updated": True, "certificate_id": certificate_id})
    else:
        _skin.success(f"Certificate {certificate_id} updated")


# ── ledger group ───────────────────────────────────────────────────────


@cli.group()
def ledger():
    """Account book (账簿) queries."""


def _ledger_date_options(f):
    f = click.option("--start", required=True, help="Start date (YYYY-MM-DD)")(f)
    f = click.option("--end", required=True, help="End date (YYYY-MM-DD)")(f)
    return f


def _print_ledger_table(ctx, rows: list):
    if not rows:
        _skin.warning("No data")
        return
    if isinstance(rows[0], dict):
        keys = list(rows[0].keys())
        headers = keys
        table_rows = [[str(r.get(k, "")) for k in keys] for r in rows]
        _skin.table(headers, table_rows)
    else:
        click.echo(str(rows))


@ledger.command("detail")
@click.option("--subject-id", required=True, type=int, help="Subject ID")
@_ledger_date_options
@click.pass_context
def ledger_detail(ctx: click.Context, subject_id: int, start: str, end: str):
    """Query detail ledger (明细账) for a subject."""
    client = _get_client(ctx)
    try:
        rows = _ledger.query_detail_account(client, subject_id, start, end)
    except WukongError as e:
        _handle_error(ctx, e)
        return
    if ctx.obj.get("json"):
        _out(ctx, rows)
    else:
        _skin.section(f"Detail Ledger — Subject {subject_id}  [{start} ~ {end}]")
        _print_ledger_table(ctx, rows)


@ledger.command("general")
@click.option("--subject-id", required=True, type=int, help="Subject ID")
@_ledger_date_options
@click.pass_context
def ledger_general(ctx: click.Context, subject_id: int, start: str, end: str):
    """Query general ledger (总账) — summarized monthly balances."""
    client = _get_client(ctx)
    try:
        rows = _ledger.query_general_ledger(client, subject_id, start, end)
    except WukongError as e:
        _handle_error(ctx, e)
        return
    if ctx.obj.get("json"):
        _out(ctx, rows)
    else:
        _skin.section(f"General Ledger — Subject {subject_id}  [{start} ~ {end}]")
        _print_ledger_table(ctx, rows)


@ledger.command("balance")
@_ledger_date_options
@click.option("--subject-id", type=int, default=None, help="Optional subject filter")
@click.option("--level", type=int, default=None, help="Subject level (1, 2, 3...)")
@click.pass_context
def ledger_balance(ctx: click.Context, start: str, end: str, subject_id, level):
    """Query subject balance table (科目余额表)."""
    client = _get_client(ctx)
    try:
        rows = _ledger.query_subject_balance(client, start, end, subject_id, level)
    except WukongError as e:
        _handle_error(ctx, e)
        return
    if ctx.obj.get("json"):
        _out(ctx, rows)
    else:
        _skin.section(f"Subject Balance  [{start} ~ {end}]")
        _print_ledger_table(ctx, rows)


@ledger.command("multi-column")
@click.option("--subject-id", required=True, type=int, help="Subject ID")
@_ledger_date_options
@click.pass_context
def ledger_multi_column(ctx: click.Context, subject_id: int, start: str, end: str):
    """Query multi-column ledger (多栏账)."""
    client = _get_client(ctx)
    try:
        result = _ledger.query_multi_column(client, subject_id, start, end)
    except WukongError as e:
        _handle_error(ctx, e)
        return
    if ctx.obj.get("json"):
        _out(ctx, result)
    else:
        _skin.section(f"Multi-column Ledger — Subject {subject_id}  [{start} ~ {end}]")
        rows = result.get("list") or result.get("data") or []
        _print_ledger_table(ctx, rows)


# ── report group ───────────────────────────────────────────────────────


@cli.group()
def report():
    """Financial reports (报表): balance sheet, income statement, cash flow."""


def _report_options(f):
    f = click.option("--period", type=click.Choice(["month", "quarter", "year"]),
                     default="month", show_default=True, help="Period type")(f)
    f = click.option("--date", required=True, help="Period date (YYYY-MM-DD)")(f)
    return f


def _print_report_table(rows: list):
    if not rows:
        _skin.warning("No data")
        return
    if isinstance(rows[0], dict):
        key_cols = ["name", "rowKey", "subjectNumber"]
        val_cols = [k for k in rows[0].keys() if k not in key_cols and "balance" in k.lower()]
        name_key = next((k for k in key_cols if k in rows[0]), list(rows[0].keys())[0])
        headers = [name_key] + val_cols
        table_rows = [[str(r.get(k, "")) for k in headers] for r in rows]
        _skin.table(headers, table_rows)
    else:
        click.echo(str(rows))


@report.command("balance-sheet")
@_report_options
@click.option("--check", is_flag=True, default=False, help="Also run balance check")
@click.pass_context
def report_balance_sheet(ctx: click.Context, period: str, date: str, check: bool):
    """Balance sheet (资产负债表)."""
    client = _get_client(ctx)
    period_type = _PERIOD_MAP[period]
    try:
        rows = _report.balance_sheet(client, period_type, date)
        check_result = _report.balance_sheet_check(client, period_type, date) if check else None
    except WukongError as e:
        _handle_error(ctx, e)
        return
    if ctx.obj.get("json"):
        out = {"rows": rows}
        if check_result is not None:
            out["balance_check"] = check_result
        _out(ctx, out)
    else:
        _skin.section(f"Balance Sheet (资产负债表) — {period.title()} {date}")
        _print_report_table(rows)
        if check_result:
            balanced = check_result.get("balanced", check_result.get("status"))
            _skin.success("Balanced") if balanced else _skin.warning(f"NOT balanced: {check_result}")


@report.command("income")
@_report_options
@click.option("--check", is_flag=True, default=False, help="Also run balance check")
@click.pass_context
def report_income(ctx: click.Context, period: str, date: str, check: bool):
    """Income statement / P&L (利润表)."""
    client = _get_client(ctx)
    period_type = _PERIOD_MAP[period]
    try:
        rows = _report.income_statement(client, period_type, date)
        check_result = _report.income_statement_check(client, period_type, date) if check else None
    except WukongError as e:
        _handle_error(ctx, e)
        return
    if ctx.obj.get("json"):
        out = {"rows": rows}
        if check_result is not None:
            out["balance_check"] = check_result
        _out(ctx, out)
    else:
        _skin.section(f"Income Statement (利润表) — {period.title()} {date}")
        _print_report_table(rows)
        if check_result:
            balanced = check_result.get("balanced", check_result.get("status"))
            _skin.success("Balanced") if balanced else _skin.warning(f"NOT balanced: {check_result}")


@report.command("cash-flow")
@_report_options
@click.option("--check", is_flag=True, default=False, help="Also run balance check")
@click.pass_context
def report_cash_flow(ctx: click.Context, period: str, date: str, check: bool):
    """Cash flow statement (现金流量表)."""
    client = _get_client(ctx)
    period_type = _PERIOD_MAP[period]
    try:
        rows = _report.cash_flow_statement(client, period_type, date)
        check_result = _report.cash_flow_check(client, period_type, date) if check else None
    except WukongError as e:
        _handle_error(ctx, e)
        return
    if ctx.obj.get("json"):
        out = {"rows": rows}
        if check_result is not None:
            out["balance_check"] = check_result
        _out(ctx, out)
    else:
        _skin.section(f"Cash Flow Statement (现金流量表) — {period.title()} {date}")
        _print_report_table(rows)
        if check_result:
            balanced = check_result.get("balanced", check_result.get("status"))
            _skin.success("Balanced") if balanced else _skin.warning(f"NOT balanced: {check_result}")


# ── adjuvant group ─────────────────────────────────────────────────────

_ADJUVANT_LABEL_NAMES = {
    1: "客户(Customer)",
    2: "供应商(Supplier)",
    3: "职员(Employee)",
    4: "项目(Project)",
    5: "部门(Department)",
    6: "存货(Inventory)",
    7: "自定义(Custom)",
}


@cli.group()
def adjuvant():
    """Auxiliary accounting (辅助核算) management."""


@adjuvant.command("list")
@click.pass_context
def adjuvant_list(ctx: click.Context):
    """List all auxiliary accounting categories (辅助核算)."""
    client = _get_client(ctx)
    try:
        items = _adjuvant.list_adjuvants(client)
    except WukongError as e:
        _handle_error(ctx, e)
        return
    if ctx.obj.get("json"):
        _out(ctx, items)
    else:
        if not items:
            _skin.warning("No auxiliary accounting categories found")
            return
        headers = ["ID", "Name", "Label", "Type"]
        rows = []
        for it in items:
            label = it.get("label")
            rows.append([
                str(it.get("adjuvantId", "")),
                it.get("adjuvantName", ""),
                _ADJUVANT_LABEL_NAMES.get(label, str(label or "")),
                "固定" if it.get("adjuvantType") == 1 else "自定义",
            ])
        _skin.table(headers, rows)


@adjuvant.command("add")
@click.option("--name", required=True, help="Category name (e.g. 部门)")
@click.option("--label", type=int, default=7, show_default=True,
              help="1=客户 2=供应商 3=职员 4=项目 5=部门 6=存货 7=自定义")
@click.pass_context
def adjuvant_add(ctx: click.Context, name: str, label: int):
    """Add a new auxiliary accounting category."""
    if not name.strip():
        _err(ctx, "名称不能为空 (adjuvant name must not be blank)")
        sys.exit(1)
    if label not in range(1, 8):
        _err(ctx, f"--label must be 1–7 (got {label}): 1=客户 2=供应商 3=职员 4=项目 5=部门 6=存货 7=自定义")
        sys.exit(1)
    client = _get_client(ctx)
    try:
        _adjuvant.add_adjuvant(client, name, label)
    except WukongError as e:
        _handle_error(ctx, e)
        return
    if ctx.obj.get("json"):
        _out(ctx, {"created": True, "name": name, "label": label})
    else:
        _skin.success(f"Added adjuvant: {name}")


@adjuvant.command("delete")
@click.argument("adjuvant_id", type=int)
@click.pass_context
def adjuvant_delete(ctx: click.Context, adjuvant_id: int):
    """Delete an auxiliary accounting category by ID."""
    client = _get_client(ctx)
    try:
        _adjuvant.delete_adjuvant(client, adjuvant_id)
    except WukongError as e:
        _handle_error(ctx, e)
        return
    if ctx.obj.get("json"):
        _out(ctx, {"deleted": adjuvant_id})
    else:
        _skin.success(f"Deleted adjuvant {adjuvant_id}")


# ── statement group ─────────────────────────────────────────────────────


@cli.group()
def statement():
    """Period closing (结账) operations."""


@statement.command("status")
@click.pass_context
def statement_status(ctx: click.Context):
    """Query current period closing status (结账状态)."""
    client = _get_client(ctx)
    try:
        result = _statement.query_statement(client)
    except WukongError as e:
        _handle_error(ctx, e)
        return
    if ctx.obj.get("json"):
        _out(ctx, result)
    else:
        settle_time = result.get("settleTime", "")
        number = result.get("number", 0)
        statements = result.get("statements") or []
        _skin.status("Last settlement", str(settle_time)[:19] if settle_time else "none")
        _skin.status("Certificates this period", str(number))
        if statements:
            _skin.section("Statement items")
            headers = ["Name", "Status"]
            rows = []
            for s in statements:
                name = s.get("statementName") or s.get("name", "")
                st = s.get("status") or s.get("statementStatus", "")
                rows.append([name, str(st)])
            _skin.table(headers, rows)


@statement.command("close")
@click.option("--date", required=True, help="Period date (YYYY-MM-DD or YYYY-MM-01)")
@click.pass_context
def statement_close(ctx: click.Context, date: str):
    """Close (结账) the accounting period."""
    client = _get_client(ctx)
    try:
        _statement.close_period(client, date)
    except WukongError as e:
        _handle_error(ctx, e)
        return
    if ctx.obj.get("json"):
        _out(ctx, {"closed": True, "date": date})
    else:
        _skin.success(f"Period {date} closed")


@statement.command("reopen")
@click.option("--date", required=True, help="Period date (YYYY-MM-DD or YYYY-MM-01)")
@click.pass_context
def statement_reopen(ctx: click.Context, date: str):
    """Reopen (反结账) a previously closed period."""
    client = _get_client(ctx)
    try:
        _statement.reopen_period(client, date)
    except WukongError as e:
        _handle_error(ctx, e)
        return
    if ctx.obj.get("json"):
        _out(ctx, {"reopened": True, "date": date})
    else:
        _skin.success(f"Period {date} reopened")


# ── Entry point ────────────────────────────────────────────────────────


def main():
    cli()


if __name__ == "__main__":
    main()
