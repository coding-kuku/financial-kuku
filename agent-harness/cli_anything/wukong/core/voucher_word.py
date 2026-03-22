"""Voucher word (凭证字) operations.

Voucher words are labels for certificate types, e.g. "记" (journal), "付" (payment).
"""

from cli_anything.wukong.utils.wukong_backend import WukongClient


def list_voucher_words(client: WukongClient) -> list:
    """Return all voucher words for the current account set."""
    return client.post("/financeVoucher/queryList") or []


def add_voucher_word(client: WukongClient, name: str) -> None:
    """Create a new voucher word.

    Args:
        name: Voucher word label (e.g. "记", "付", "收")
    """
    client.post("/financeVoucher/add", {"voucherName": name})


def update_voucher_word(client: WukongClient, voucher_id: int, name: str) -> None:
    """Update a voucher word name."""
    client.post("/financeVoucher/update", {"voucherId": voucher_id, "voucherName": name})


def delete_voucher_word(client: WukongClient, voucher_id: int) -> None:
    """Delete a voucher word by ID."""
    client.post("/financeVoucher/deleteById", params={"voucherId": voucher_id})
