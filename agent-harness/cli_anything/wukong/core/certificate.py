"""Certificate / journal entry (凭证) operations.

A certificate (凭证) is an accounting journal entry containing:
- Header: voucher word, number, date, creator
- Detail lines (分录): subject, debit/credit amount, summary
"""

from typing import Optional
from cli_anything.wukong.utils.wukong_backend import WukongClient


def _to_float(value) -> float:
    """Coerce a balance field to float; treat None/empty/falsy as 0."""
    if not value:
        return 0.0
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def validate_certificate_details(details: list[dict]) -> list[dict]:
    """Validate and filter certificate details to match frontend rules.

    Steps (mirrors Create.vue checkForm logic):
      1. Filter pure empty rows (no subjectId AND both balances 0/None).
      2. Raise if filtered list is empty.
      3. For each remaining row:
         - subjectId set but both balances 0 → error.
         - non-zero balance but no subjectId → error.
      4. Raise if no valid entry (subjectId + at least one non-zero balance).
      5. Raise if first valid entry has no digestContent.
      6. Raise if total debits ≠ total credits.

    Returns the filtered details list (pure empty rows removed) on success.
    Raises ValueError with a descriptive message on any failure.
    """
    # Rule 7: drop rows with neither subjectId nor any amount
    filtered = [
        row for row in details
        if row.get("subjectId")
        or _to_float(row.get("debtorBalance"))
        or _to_float(row.get("creditBalance"))
    ]

    # Rule 1: must not be empty after filtering
    if not filtered:
        raise ValueError(
            "certificateDetails 不能为空 — 至少需要一条有效分录 (at least one valid entry required)"
        )

    # Rules 4 & 5: per-row consistency check
    for i, row in enumerate(filtered):
        has_subject = bool(row.get("subjectId"))
        debit = _to_float(row.get("debtorBalance"))
        credit = _to_float(row.get("creditBalance"))
        has_amount = debit != 0.0 or credit != 0.0

        if has_subject and not has_amount:
            raise ValueError(
                f"第 {i + 1} 条：有科目但借贷金额均为 0 (row {i + 1}: subject set but both balances are zero)"
            )
        if has_amount and not has_subject:
            raise ValueError(
                f"第 {i + 1} 条：有金额但没有科目 (row {i + 1}: amount set but subjectId is missing)"
            )

    # Collect valid entries: subjectId + at least one non-zero balance
    valid_entries = [
        row for row in filtered
        if row.get("subjectId")
        and (_to_float(row.get("debtorBalance")) or _to_float(row.get("creditBalance")))
    ]

    # Rule 2: must have at least one valid entry
    if not valid_entries:
        raise ValueError(
            "没有有效分录 — 每条分录必须有科目且借方或贷方金额非零 (no valid entry: each entry needs a subjectId with non-zero balance)"
        )

    # Rule 3: first valid entry must have digestContent
    if not valid_entries[0].get("digestContent"):
        raise ValueError(
            "第一条摘要不能为空 (digestContent of the first valid entry must not be empty)"
        )

    # Rule 6: debits must equal credits (rounded to 2 dp to handle float imprecision)
    total_debit = round(sum(_to_float(row.get("debtorBalance")) for row in valid_entries), 2)
    total_credit = round(sum(_to_float(row.get("creditBalance")) for row in valid_entries), 2)
    if total_debit != total_credit:
        raise ValueError(
            f"借贷不平衡：借方合计 {total_debit:.2f}，贷方合计 {total_credit:.2f} "
            f"(debits {total_debit:.2f} ≠ credits {total_credit:.2f})"
        )

    return filtered


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
        start_time: Start period in yyyyMM format (e.g. "202401") —
            the SQL compares DATE_FORMAT(certificate_time,'%Y%m') against this string directly.
            CLI converts YYYY-MM input to this format before calling.
        end_time: End period in yyyyMM format (e.g. "202412")
        voucher_id: Filter by voucher word ID
        check_status: 0=unreviewed, 1=reviewed
        page_no: Page number (1-based)
        page_size: Records per page

    Returns:
        {"records": [...], "total": N, "pages": N}
    """
    body: dict = {"page": page_no, "limit": page_size}
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
    """Return detailed certificate by ID, including all debit/credit lines.

    Enriches the response to match Web frontend behaviour:
    - voucherName: resolved by fetching the voucher word list and matching voucherId
      (the raw queryById response only contains voucherId, not the name)
    - subjectName in each detail line: extracted from the subjectContent JSON column
      (the raw response omits the transient subjectName field populated only by JOIN queries)
    - Normalises certificateDetails → details for consistency with list records
    """
    import json as _json
    from cli_anything.wukong.core.voucher_word import list_voucher_words

    result = client.post("/financeCertificate/queryById", params={"certificateId": certificate_id}) or {}

    # Enrich voucherName (Web loads voucher list separately and matches by voucherId)
    voucher_id = result.get("voucherId")
    if voucher_id:
        vouchers = list_voucher_words(client)
        voucher_map = {v["voucherId"]: v.get("voucherName", "") for v in vouchers if v.get("voucherId")}
        result["voucherName"] = voucher_map.get(voucher_id, "")

    # Normalise certificateDetails → details; enrich subjectName/subjectNumber
    raw_details = result.pop("certificateDetails", None) or []

    # First pass: try to extract from subjectContent JSON (populated for newer records)
    needs_subject_lookup = []
    for d in raw_details:
        if not d.get("subjectName") and d.get("subjectContent"):
            try:
                subject = _json.loads(d["subjectContent"])
                d["subjectName"] = subject.get("subjectName", "")
                if not d.get("subjectNumber"):
                    d["subjectNumber"] = subject.get("number", "")
            except (ValueError, TypeError):
                pass
        if not d.get("subjectName") and d.get("subjectId"):
            needs_subject_lookup.append(d)

    # Second pass: fall back to subject list lookup for old records where subjectContent is null
    if needs_subject_lookup:
        from cli_anything.wukong.core.subject import list_subjects
        subjects = list_subjects(client)
        subject_map = {str(s["subjectId"]): s for s in subjects if s.get("subjectId")}
        for d in needs_subject_lookup:
            s = subject_map.get(str(d["subjectId"]))
            if s:
                d["subjectName"] = s.get("subjectName", "")
                if not d.get("subjectNumber"):
                    d["subjectNumber"] = s.get("number", "")

    result["details"] = raw_details

    return result


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
                "creditBalance": float,  # credit amount (0 if debit)
                "adjuvantList": []       # optional auxiliary accounting items
            }
        certificate_num: Certificate number (auto-assigned if None)

    Returns:
        Created certificate dict
    """
    filtered = validate_certificate_details(details)
    body: dict = {
        "voucherId": voucher_id,
        "certificateTime": certificate_time,
        "certificateDetails": filtered,
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
    filtered = validate_certificate_details(details)
    # Snowflake IDs arrive as strings from the API; convert to int for Java Long
    body: dict = {
        "certificateId": int(certificate_id),
        "voucherId": int(voucher_id),
        "certificateTime": certificate_time,
        "certificateDetails": filtered,
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
        certificate_time: Date in YYYY-MM-DD format (e.g. "2024-06-01")

    Returns:
        {"certificateNum": N}
    """
    # BeanUtil on the backend maps this String field to LocalDateTime.
    # It can parse "YYYY-MM-DD HH:mm:ss" but not "yyyyMM".
    # We pass the first day of the month as a full datetime string.
    year_month = certificate_time[:7]  # "2024-06"
    full_dt = f"{year_month}-01 00:00:00"
    return client.post("/financeCertificate/queryNumByTime", {
        "voucherId": voucher_id,
        "certificateTime": full_dt,
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
