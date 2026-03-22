"""Period closing / settlement (结账) operations.

结账 is the month-end/year-end closing workflow:
1. Query current period status (queryStatement)
2. Close the period (statement with type=1)
3. Reopen if needed (statement with type=2)
4. Generate closing certificates (statementCertificate)
"""

from typing import Optional
from cli_anything.wukong.utils.wukong_backend import WukongClient


def query_statement(client: WukongClient) -> dict:
    """Return current period closing status.

    Returns:
        {
            "settleTime": "...",   # last settlement datetime
            "number": N,           # certificates entered this period
            "accountId": N,
            "statements": [...]    # list of statement items with status
        }
    """
    return client.post("/financeStatement/queryStatement") or {}


def close_period(client: WukongClient, date: str) -> None:
    """Close (结账) the accounting period.

    Args:
        date: Period date (YYYY-MM-DD or YYYY-MM-01), e.g. "2024-01-01"
    """
    client.post("/financeStatement/statement", {
        "certificateTime": date,
        "type": 1,
    })


def reopen_period(client: WukongClient, date: str) -> None:
    """Reopen (反结账) a previously closed period.

    Args:
        date: Period date (YYYY-MM-DD or YYYY-MM-01)
    """
    client.post("/financeStatement/statement", {
        "certificateTime": date,
        "type": 2,
    })


def gen_closing_certificate(
    client: WukongClient,
    date: str,
    statement_ids: Optional[list] = None,
) -> None:
    """Generate closing journal entries (结账生成凭证).

    Args:
        date: Certificate date (YYYY-MM-DD)
        statement_ids: Optional list of statement IDs to generate for.
                       If None, generates for all.
    """
    body: dict = {"certificateTime": date}
    if statement_ids:
        body["statementIds"] = [int(sid) for sid in statement_ids]
    client.post("/financeStatement/statementCertificate", body)
