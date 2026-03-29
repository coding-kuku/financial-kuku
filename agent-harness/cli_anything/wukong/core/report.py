"""Financial report (报表) operations.

Three standard Chinese accounting reports:
- 资产负债表 (Balance Sheet)
- 利润表 (Income Statement / P&L)
- 现金流量表 (Cash Flow Statement)
"""

from cli_anything.wukong.utils.wukong_backend import WukongClient


def _report_body(period_type: int, date: str) -> dict:
    """Build the report request body.

    Args:
        period_type: 1=month, 2=quarter, 3=year
        date: Period end date (YYYY-MM-DD or YYYY-MM)

    The API expects fromPeriod/toPeriod as yyyyMM strings.
    For month: fromPeriod == toPeriod.
    For quarter: fromPeriod = first month of the quarter containing date.
    For year: fromPeriod = January of the same year.
    """
    # Normalize: "2026-03-31" or "2026-03" → "202603"
    period = date[:7].replace("-", "")  # "2026-03" → "202603"
    year = period[:4]
    month = int(period[4:6])

    if period_type == 2:  # quarter
        quarter_start = ((month - 1) // 3) * 3 + 1
        from_period = f"{year}{quarter_start:02d}"
    elif period_type == 3:  # year
        from_period = f"{year}01"
    else:  # month
        from_period = period

    return {"type": period_type, "fromPeriod": from_period, "toPeriod": period}


def balance_sheet(client: WukongClient, period_type: int, date: str) -> list:
    """Get balance sheet (资产负债表).

    Args:
        period_type: 1=month, 2=quarter, 3=year
        date: Report period date (YYYY-MM-DD)

    Returns:
        List of report rows with account items and amounts
    """
    return client.post("/financeReport/balanceSheetReport", _report_body(period_type, date)) or []


def income_statement(client: WukongClient, period_type: int, date: str) -> list:
    """Get income statement / profit & loss (利润表).

    Args:
        period_type: 1=month, 2=quarter, 3=year
        date: Report period date (YYYY-MM-DD)

    Returns:
        List of report rows
    """
    return client.post("/financeReport/incomeStatementReport", _report_body(period_type, date)) or []


def cash_flow_statement(client: WukongClient, period_type: int, date: str) -> list:
    """Get cash flow statement (现金流量表).

    Args:
        period_type: 1=month, 2=quarter, 3=year
        date: Report period date (YYYY-MM-DD)

    Returns:
        List of report rows
    """
    return client.post("/financeReport/cashFlowStatementReport", _report_body(period_type, date)) or []


def balance_sheet_check(client: WukongClient, period_type: int, date: str) -> dict:
    """Check if balance sheet balances (资产 = 负债 + 权益).

    Returns:
        {"balanced": bool, "difference": float}
    """
    return client.post("/financeReport/balanceSheetReport/balanceCheck", _report_body(period_type, date)) or {}


def income_statement_check(client: WukongClient, period_type: int, date: str) -> dict:
    """Check if income statement balances."""
    return client.post("/financeReport/incomeStatementReport/balanceCheck", _report_body(period_type, date)) or {}


def cash_flow_check(client: WukongClient, period_type: int, date: str) -> dict:
    """Check if cash flow statement balances."""
    return client.post("/financeReport/cashFlowStatementReport/balanceCheck", _report_body(period_type, date)) or {}


def dashboard_income_statement(client: WukongClient, str_date: str = None) -> list:
    """Get income statement dashboard statistics.

    Args:
        str_date: Optional date string (YYYY-MM-DD)
    """
    params = {}
    if str_date:
        params["strDate"] = str_date
    return client.post("/financeDashboard/incomeStatement", params=params) or []
