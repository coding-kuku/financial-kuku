"""Account set (账套) operations."""

from cli_anything.wukong.utils.wukong_backend import WukongClient


def list_accounts(client: WukongClient) -> list:
    """Return active account sets (status=1) the current user can access."""
    return client.post("/financeAccountSet/getAccountSetList") or []


def list_all_accounts(client: WukongClient) -> list:
    """Return all account sets including unconfigured ones (status=0).

    Uses the admin queryPageList endpoint which returns all records.
    """
    result = client.post("/financeAccountSet/queryPageList", {"pageNo": 1, "pageSize": 100}) or []
    if isinstance(result, dict):
        return result.get("records") or result.get("list") or []
    return result


def get_account(client: WukongClient, account_id: int) -> dict:
    """Return account set details by ID."""
    return client.post("/financeAccountSet/getAccountSetById", params={"accountId": account_id}) or {}


def switch_account(client: WukongClient, account_id: int) -> None:
    """Switch the server-side session to a different account set."""
    client.post("/financeAccountSet/switchAccountSet", params={"accountId": account_id})


def create_account(client: WukongClient, company_name: str, start_time: str = "2026-01-01") -> int:
    """Create a new account set and return its ID.

    Calls /financeAccountSet/addAccount which creates the account (status=0),
    links the current user, and initializes RMB currency and default voucher words.
    The account is not yet active; call configure_account() to activate it.

    Returns:
        The new account set ID (int)
    """
    client.post("/financeAccountSet/addAccount", {
        "companyName": company_name,
        "companyCode": company_name,
    })
    all_accounts = list_all_accounts(client)
    for acc in reversed(all_accounts):
        if acc.get("companyName") == company_name and acc.get("status") == 0:
            return int(acc["accountId"])
    for acc in reversed(all_accounts):
        if acc.get("status") == 0:
            return int(acc["accountId"])
    raise RuntimeError(f"Could not find newly created account set for '{company_name}'")


def configure_account(client: WukongClient, account_id: int, start_time: str = "2026-01-01") -> None:
    """Activate an account set (sets status=1) so it appears in list_accounts.

    Switches to the account, discovers its RMB currency, then calls saveAccountSet.

    Args:
        account_id: The account set ID to configure
        start_time: Accounting start date (YYYY-MM-DD)
    """
    switch_account(client, account_id)
    currencies = client.post("/financeCurrency/queryAllList") or []
    currency_id = None
    for c in currencies:
        if c.get("homeCurrency") == 1:
            currency_id = int(c["currencyId"])
            break
    if currency_id is None and currencies:
        currency_id = int(currencies[0]["currencyId"])
    if currency_id is None:
        raise RuntimeError(f"No currency found for account {account_id}")
    client.post("/financeAccountSet/saveAccountSet", {
        "accountId": account_id,
        "currencyId": currency_id,
        "startTime": start_time,
    })


