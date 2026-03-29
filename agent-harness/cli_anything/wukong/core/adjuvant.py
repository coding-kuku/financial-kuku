"""Auxiliary accounting (辅助核算) operations.

辅助核算 allows attaching supplementary dimensions (department, project,
employee, customer, etc.) to journal entry lines for finer-grained tracking.

Standard labels:
    1=客户  2=供应商  3=职员  4=项目  5=部门  6=存货  7=自定义
"""

from typing import Optional
from cli_anything.wukong.utils.wukong_backend import WukongClient


def list_adjuvants(client: WukongClient) -> list:
    """Return all auxiliary accounting categories for the current account set."""
    return client.post("/financeAdjuvant/queryAllList") or []


def add_adjuvant(client: WukongClient, name: str, label: int = 7) -> None:
    """Create a new auxiliary accounting category.

    Args:
        name: Category name (e.g. "部门", "项目")
        label: Predefined type: 1=客户 2=供应商 3=职员 4=项目 5=部门
               6=存货 7=自定义 (default)
    """
    client.post("/financeAdjuvant/add", {"adjuvantName": name, "label": label})


def delete_adjuvant(client: WukongClient, adjuvant_id: int) -> None:
    """Delete an auxiliary accounting category by ID."""
    client.post("/financeAdjuvant/deleteById", params={"adjuvantId": adjuvant_id})


# ── Carte (卡片) operations ────────────────────────────────────────────
# Cartes are the individual entries within an adjuvant category.
# e.g. category "客户" contains cartes like "蓬江区世祥商行", "测试客户".
# When recording a certificate line against a subject with auxiliary accounting,
# you must supply the carteId in adjuvantList[].relationId.


def list_cartes(
    client: WukongClient,
    adjuvant_id: int,
    search: Optional[str] = None,
    page_no: int = 1,
    page_size: int = 50,
) -> dict:
    """List cartes (卡片) under an adjuvant category.

    Args:
        adjuvant_id: Adjuvant category ID
        search: Optional keyword to filter by carteNumber or carteName
        page_no: Page number (1-based)
        page_size: Records per page

    Returns:
        {"list": [...], "totalCount": N}  — each item has carteId, carteNumber, carteName, status
    """
    body: dict = {"adjuvantId": adjuvant_id, "pageNo": page_no, "pageSize": page_size}
    if search:
        body["search"] = search
    result = client.post("/financeAdjuvantCarte/queryByAdjuvantId", body) or {}
    # API returns {"list": [...], "totalCount": N} inside data
    return result


def add_carte(
    client: WukongClient,
    adjuvant_id: int,
    number: str,
    name: str,
    specification: Optional[str] = None,
    unit: Optional[str] = None,
    remark: Optional[str] = None,
) -> dict:
    """Create a new carte under an adjuvant category.

    Args:
        adjuvant_id: Adjuvant category ID
        number: Carte code (carteNumber) — can be numeric or alphanumeric
        name: Carte name (carteName)
        specification: Item spec, used for inventory (存货) cartes
        unit: Unit of measure, used for inventory cartes
        remark: Notes, used for customer/supplier cartes

    Returns:
        Created carte dict
    """
    body: dict = {"adjuvantId": adjuvant_id, "carteNumber": number, "carteName": name}
    if specification is not None:
        body["specification"] = specification
    if unit is not None:
        body["unit"] = unit
    if remark is not None:
        body["remark"] = remark
    return client.post("/financeAdjuvantCarte/add", body) or {}


def update_carte(
    client: WukongClient,
    carte_id: int,
    adjuvant_id: int,
    name: Optional[str] = None,
    number: Optional[str] = None,
    specification: Optional[str] = None,
    unit: Optional[str] = None,
    remark: Optional[str] = None,
) -> dict:
    """Update an existing carte.

    Args:
        carte_id: Carte ID to update
        adjuvant_id: Parent adjuvant category ID (required by backend for logging)
        name: New carte name (carteName)
        number: New carte code (carteNumber)
        specification: Item spec (存货 cartes)
        unit: Unit of measure (存货 cartes)
        remark: Notes (customer/supplier cartes)

    Returns:
        Updated carte dict
    """
    body: dict = {"carteId": int(carte_id), "adjuvantId": int(adjuvant_id)}
    if name is not None:
        body["carteName"] = name
    if number is not None:
        body["carteNumber"] = number
    if specification is not None:
        body["specification"] = specification
    if unit is not None:
        body["unit"] = unit
    if remark is not None:
        body["remark"] = remark
    return client.post("/financeAdjuvantCarte/update", body) or {}


def delete_cartes(client: WukongClient, carte_ids: list) -> None:
    """Delete cartes by ID list.

    Args:
        carte_ids: List of carte IDs (int or str snowflake IDs)
    """
    client.post("/financeAdjuvantCarte/deleteById", [int(cid) for cid in carte_ids])
