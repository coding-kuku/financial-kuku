"""Account book (账簿) query operations.

Covers:
- Detail ledger (明细账) — per-subject transaction history
- General ledger (总账) — summarized per-subject balances
- Subject balance (科目余额表) — balance sheet by subject
- Multi-column ledger (多栏账) — side-by-side columns
- Quantity-amount ledger (数量金额账) — quantity + amount tracking
"""

from typing import Optional
from cli_anything.wukong.utils.wukong_backend import WukongClient


def _ledger_body(
    subject_id: Optional[int],
    start_time: str,
    end_time: str,
    show_all: bool = True,
) -> dict:
    body: dict = {"startTime": start_time, "endTime": end_time, "showAll": show_all}
    if subject_id is not None:
        body["subjectId"] = subject_id
    return body


def query_detail_account(
    client: WukongClient,
    subject_id: int,
    start_time: str,
    end_time: str,
) -> list:
    """Query detail ledger (明细账) for a subject.

    Args:
        subject_id: Subject ID
        start_time: Period start in yyyyMM format (e.g. "202101")
        end_time: Period end in yyyyMM format (e.g. "202112")

    Returns:
        List of transaction rows
    """
    body = _ledger_body(subject_id, start_time, end_time)
    return client.post("/financeCertificate/queryDetailAccount", body) or []


def query_general_ledger(
    client: WukongClient,
    subject_id: int,
    start_time: str,
    end_time: str,
    min_level: int = 1,
    max_level: int = 1,
) -> list:
    """Query general ledger (总账) — summarized monthly balances for a subject.

    Args:
        subject_id: Subject ID
        start_time: Period start in yyyyMM format (e.g. "202101")
        end_time: Period end in yyyyMM format (e.g. "202112")
        min_level: Minimum subject grade level to include (default 1)
        max_level: Maximum subject grade level to include (default 1)
    """
    body = _ledger_body(None, start_time, end_time)
    body["minLevel"] = min_level
    body["maxLevel"] = max_level
    if subject_id is not None:
        body["startSubjectId"] = subject_id
        body["endSubjectId"] = subject_id
    return client.post("/financeCertificate/queryDetailUpAccount", body) or []


def query_subject_balance(
    client: WukongClient,
    start_time: str,
    end_time: str,
    subject_id: Optional[int] = None,
    level: Optional[int] = None,
) -> list:
    """Query subject balance table (科目余额表).

    Args:
        start_time: Period start in yyyyMM format (e.g. "202101") —
            the backend parses this with SIMPLE_MONTH_PATTERN, so yyyyMM is required.
        end_time: Period end in yyyyMM format (e.g. "202112")
        subject_id: Optional subject filter
        level: Optional subject level filter (1, 2, 3...)

    Returns:
        List of subject balance rows
    """
    body: dict = {"startTime": start_time, "endTime": end_time}
    if subject_id is not None:
        body["startSubjectId"] = subject_id
        body["endSubjectId"] = subject_id
    if level is not None:
        body["minLevel"] = level
        body["maxLevel"] = level
    return client.post("/financeCertificate/queryDetailBalanceAccount", body) or []


def query_multi_column(
    client: WukongClient,
    subject_id: int,
    start_time: str,
    end_time: str,
) -> dict:
    """Query multi-column ledger (多栏账) for a subject."""
    body = _ledger_body(subject_id, start_time, end_time)
    return client.post("/financeCertificate/queryDiversification", body) or {}


def query_quantity_amount_detail(
    client: WukongClient,
    subject_id: int,
    start_time: str,
    end_time: str,
) -> list:
    """Query quantity-amount detail ledger (数量金额明细账) for a subject."""
    body = _ledger_body(subject_id, start_time, end_time)
    return client.post("/financeCertificate/queryAmountDetailAccount", body) or []


def query_quantity_amount_general(
    client: WukongClient,
    subject_id: int,
    start_time: str,
    end_time: str,
) -> list:
    """Query quantity-amount general ledger (数量总账) for a subject."""
    body = _ledger_body(subject_id, start_time, end_time)
    return client.post("/financeCertificate/queryAmountDetailUpAccount", body) or []
