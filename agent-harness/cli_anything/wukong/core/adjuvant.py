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
