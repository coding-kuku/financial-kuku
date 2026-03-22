"""Certificate / journal entry (凭证) operations.

A certificate (凭证) is an accounting journal entry containing:
- Header: voucher word, number, date, creator
- Detail lines (分录): subject, debit/credit amount, summary
"""

from typing import Optional
from cli_anything.wukong.utils.wukong_backend import WukongClient


def list_certificates(
    client: WukongClient,
    start_time: Optional[str] = None,
    end_time: Optional[str] = None,
    voucher_id: Optional[int] = None,
    check_status: Optional[int] = None,
    page_no: int = 1,
    page_size: int = 20,
) -> dict:
    """List certificates with pagination.

    Args:
        start_time: Start date filter (YYYY-MM-DD)
        end_time: End date filter (YYYY-MM-DD)
        voucher_id: Filter by voucher word ID
        check_status: 0=unreviewed, 1=reviewed
        page_no: Page number (1-based)
        page_size: Records per page

    Returns:
        {"records": [...], "total": N, "pages": N}
    """
    body: dict = {"pageNo": page_no, "pageSize": page_size}
    if start_time:
        body["startTime"] = start_time
    if end_time:
        body["endTime"] = end_time
    if voucher_id is not None:
        body["voucherId"] = voucher_id
    if check_status is not None:
        body["checkStatus"] = check_status
    return client.post("/financeCertificate/queryPageList", body) or {}


def get_certificate(client: WukongClient, certificate_id: int) -> dict:
    """Return detailed certificate by ID, including all debit/credit lines."""
    return client.post("/financeCertificate/queryById", params={"certificateId": certificate_id}) or {}


def add_certificate(
    client: WukongClient,
    voucher_id: int,
    certificate_time: str,
    details: list[dict],
    certificate_num: Optional[int] = None,
) -> dict:
    """Create a new journal entry certificate.

    Args:
        voucher_id: Voucher word ID (from list_voucher_words)
        certificate_time: Date string (YYYY-MM-DD)
        details: List of debit/credit lines, each:
            {
                "subjectId": int,        # subject ID
                "digestContent": str,    # memo/summary
                "debtorBalance": float,  # debit amount (0 if credit)
                "ownerBalance": float,   # credit amount (0 if debit)
                "adjuvantList": []       # optional auxiliary accounting items
            }
        certificate_num: Certificate number (auto-assigned if None)

    Returns:
        Created certificate dict
    """
    body: dict = {
        "voucherId": voucher_id,
        "certificateTime": certificate_time,
        "certificateDetails": details,
    }
    if certificate_num is not None:
        body["certificateNum"] = certificate_num
    return client.post("/financeCertificate/add", body) or {}


def update_certificate(
    client: WukongClient,
    certificate_id: int,
    voucher_id: int,
    certificate_time: str,
    details: list[dict],
    certificate_num: Optional[int] = None,
) -> dict:
    """Update an existing certificate."""
    body: dict = {
        "certificateId": certificate_id,
        "voucherId": voucher_id,
        "certificateTime": certificate_time,
        "certificateDetails": details,
    }
    if certificate_num is not None:
        body["certificateNum"] = certificate_num
    return client.post("/financeCertificate/update", body) or {}


def delete_certificates(client: WukongClient, certificate_ids: list) -> None:
    """Delete certificates by ID list.

    Converts IDs to int — snowflake IDs from the API arrive as strings
    but must be sent as JSON numbers for Java Long deserialization.
    """
    client.post("/financeCertificate/deleteByIds", {"ids": [int(cid) for cid in certificate_ids]})


def review_certificates(
    client: WukongClient, certificate_ids: list, status: int
) -> None:
    """Set review status on certificates.

    Args:
        certificate_ids: List of certificate IDs
        status: 1=approve, 0=unapprove
    """
    client.post("/financeCertificate/updateCheckStatusByIds", {"ids": [int(cid) for cid in certificate_ids], "status": status})


def get_next_certificate_num(
    client: WukongClient, voucher_id: int, certificate_time: str
) -> dict:
    """Get the next available certificate number for a voucher word and date.

    Args:
        voucher_id: Voucher word ID
        certificate_time: Date as yyyyMM (e.g. "202603") or YYYY-MM-DD
            (auto-normalized to yyyyMM — the API requires this format)

    Returns:
        {"certificateNum": N}
    """
    # API requires yyyyMM format for BeanUtil to leave LocalDateTime null,
    # which lets the SQL date filter fall through safely.
    period = certificate_time[:7].replace("-", "") if "-" in certificate_time else certificate_time
    return client.post("/financeCertificate/queryNumByTime", {
        "voucherId": voucher_id,
        "certificateTime": period,
    }) or {}


def settle_certificates(
    client: WukongClient, voucher_id: int, start_time: str, end_time: str
) -> None:
    """Renumber/settle certificates sequentially within a period."""
    client.post("/financeCertificate/certificateSettle", {
        "voucherId": voucher_id,
        "startTime": start_time,
        "endTime": end_time,
    })
