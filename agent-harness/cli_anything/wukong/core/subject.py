"""Subject / account code (科目) operations."""

from typing import Optional
from cli_anything.wukong.utils.wukong_backend import WukongClient


def list_subjects(
    client: WukongClient,
    subject_type: Optional[int] = None,
    is_tree: int = 0,
    return_type: Optional[int] = None,
    certificate_time: Optional[str] = None,
) -> list:
    """Return subjects (account codes).

    Args:
        subject_type: Subject type filter (1=assets, 2=liabilities, 3=equity, etc.)
        is_tree: 0=flat list, 1=tree structure
        return_type: Optional return type filter
        certificate_time: Optional date filter (YYYY-MM-DD)
    """
    params: dict = {"isTree": is_tree}
    if subject_type is not None:
        params["type"] = subject_type
    if return_type is not None:
        params["returnType"] = return_type
    if certificate_time is not None:
        params["certificateTime"] = certificate_time
    return client.post("/financeSubject/queryListByType", params=params) or []


def get_subject_by_id(client: WukongClient, subject_id: int) -> Optional[dict]:
    """Find a subject by ID from the full subject list."""
    subjects = list_subjects(client)
    sid = str(subject_id)
    for s in subjects:
        if str(s.get("subjectId")) == sid:
            return s
    return None


def add_subject(
    client: WukongClient,
    subject_number: str,
    subject_name: str,
    subject_type: int,
    balance_direction: int,
    parent_id: Optional[int] = None,
    currency_type: int = 1,
    is_end: int = 1,
) -> None:
    """Add or update a subject.

    Args:
        subject_number: Account code (e.g. "1001") — sent as field "number"
        subject_name: Account name (e.g. "库存现金")
        subject_type: 1=资产, 2=负债, 3=权益, 4=成本, 5=损益 — sent as field "type"
        balance_direction: 1=借方 (debit), 2=贷方 (credit) — required by frontend
        parent_id: Parent subject ID (None for top-level)
        currency_type: 1=人民币, 2=外币
        is_end: 1=leaf node (末级), 0=parent node
    """
    from cli_anything.wukong.utils.wukong_backend import WukongError
    body = {
        "number": subject_number,
        "subjectName": subject_name,
        "type": subject_type,
        "balanceDirection": balance_direction,
        "currencyType": currency_type,
        "isEnd": is_end,
    }
    if parent_id is not None:
        body["parentId"] = parent_id
        # Inherit category from parent — backend validates child.category == parent.category
        parent = get_subject_by_id(client, parent_id)
        if parent is None:
            raise WukongError(f"父科目 {parent_id} 不存在")
        body["category"] = parent["category"]
    client.post("/financeSubject/add", body)


def delete_subjects(client: WukongClient, subject_ids: list) -> None:
    """Delete subjects by ID list.

    Note: snowflake IDs from the API arrive as strings; converting to int
    ensures the Java server deserializes them correctly as Long values.
    """
    client.post("/financeSubject/deleteByIds", {"ids": [int(sid) for sid in subject_ids]})


def toggle_subject_status(
    client: WukongClient, subject_ids: list[int], status: int
) -> None:
    """Enable (1) or disable (0) subjects.

    Args:
        subject_ids: List of subject IDs
        status: 1=enable, 0=disable
    """
    client.post("/financeSubject/updateStatus", {"ids": subject_ids, "status": status})
