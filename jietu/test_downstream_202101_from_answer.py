# -*- coding: utf-8 -*-
import json
from pathlib import Path

from cli_anything.wukong.core.session import load_session
from cli_anything.wukong.utils.wukong_backend import WukongClient
from cli_anything.wukong.core import ledger, report, statement

ACCOUNT='2036268933673287680'
SUBJECTS={
    '1002 银行存款':2036268933799116800,
    '1122 应收账款':2036268933803311110,
    '1405 库存商品':2036268933811699715,
    '2202 应付账款':2036268933820088327,
    '3103 本年利润':2036268933832671233,
    '5601 销售费用':2036268933836865552,
    '5602 管理费用':2036268933841059849,
}
OUT=Path('jietu/202101_downstream_test_report.md')
JSON_OUT=Path('jietu/202101_downstream_test_report.json')

AMOUNT_KEYS=('monthValue','yearValue','endValue','yearAmount','periodAmount','balance','debtorBalance','creditBalance')


def client():
    sess=load_session()
    c=WukongClient(sess['base_url'], token=sess['token'])
    c.post('/financeAccountSet/switchAccountSet', params={'accountId': ACCOUNT})
    return c


def extract_amounts(row):
    vals={}
    for k in AMOUNT_KEYS:
        v=row.get(k)
        if isinstance(v,(int,float)) and abs(v)>1e-9:
            vals[k]=v
    return vals


def summarize_detail(rows):
    business=[r for r in rows if r.get('type')=='2']
    ending=rows[-1] if rows else {}
    return {
        'entry_count': len(business),
        'ending': {
            'digestContent': ending.get('digestContent'),
            'balanceDirection': ending.get('balanceDirection'),
            'balance': ending.get('balance'),
            'debtorBalance': ending.get('debtorBalance'),
            'creditBalance': ending.get('creditBalance'),
        },
        'sample_entries': [
            {
                'date': r.get('accountTime'),
                'certificateNum': r.get('certificateNum'),
                'digest': r.get('digestContent'),
                'debtorBalance': r.get('debtorBalance'),
                'creditBalance': r.get('creditBalance'),
                'balance': r.get('balance'),
            }
            for r in business[:5]
        ]
    }


def summarize_report(rows):
    picked=[]
    for r in rows:
        amounts=extract_amounts(r)
        if amounts:
            picked.append({'name': r.get('name'), **amounts})
    return picked


def main():
    c=client()
    result={
        'account_id': ACCOUNT,
        'dataset_basis': '202101记账凭证.xls 标准答案导入结果',
        'checks': {}
    }

    # certificate list bug reproduction
    page1 = c.post('/financeCertificate/queryPageList', {'pageNo':1,'pageSize':200,'startTime':'202101','endTime':'202101'}) or {}
    page2 = c.post('/financeCertificate/queryPageList', {'pageNo':2,'pageSize':200,'startTime':'202101','endTime':'202101'}) or {}
    result['checks']['certificate_list_api'] = {
        'totalRow': page1.get('totalRow'),
        'backendPageSize': page1.get('pageSize'),
        'page1_count': len(page1.get('list') or []),
        'page2_count': len(page2.get('list') or []),
        'page1_first5': [x.get('certificateNum') for x in (page1.get('list') or [])[:5]],
        'page2_first5': [x.get('certificateNum') for x in (page2.get('list') or [])[:5]],
        'page_no_effective': [x.get('certificateId') for x in (page1.get('list') or [])] == [x.get('certificateId') for x in (page2.get('list') or [])],
    }

    # ledgers
    for name, sid in SUBJECTS.items():
        try:
            rows = ledger.query_detail_account(c, sid, '2021-01-01', '2021-01-31')
            result['checks'][f'ledger_detail:{name}'] = {'ok': True, **summarize_detail(rows)}
        except Exception as e:
            result['checks'][f'ledger_detail:{name}'] = {'ok': False, 'error': str(e)}
        try:
            rows = ledger.query_general_ledger(c, sid, '2021-01-01', '2021-01-31')
            result['checks'][f'ledger_general:{name}'] = {'ok': True, 'row_count': len(rows), 'rows': rows}
        except Exception as e:
            result['checks'][f'ledger_general:{name}'] = {'ok': False, 'error': str(e)}

    try:
        rows = ledger.query_subject_balance(c, '2021-01-01', '2021-01-31', level=1)
        result['checks']['ledger_balance_level1'] = {'ok': True, 'row_count': len(rows), 'rows': rows}
    except Exception as e:
        result['checks']['ledger_balance_level1'] = {'ok': False, 'error': str(e)}

    # reports
    for label, query_fn, check_fn in [
        ('report_balance_sheet', report.balance_sheet, report.balance_sheet_check),
        ('report_income', report.income_statement, report.income_statement_check),
        ('report_cash_flow', report.cash_flow_statement, report.cash_flow_check),
    ]:
        item = {}
        try:
            rows = query_fn(c, 1, '2021-01-31')
            item['ok'] = True
            item['row_count'] = len(rows)
            item['nonzero_rows'] = summarize_report(rows)
        except Exception as e:
            item['ok'] = False
            item['error'] = str(e)
        try:
            item['check'] = check_fn(c, 1, '2021-01-31')
        except Exception as e:
            item['check_error'] = str(e)
        result['checks'][label] = item

    try:
        st = statement.query_statement(c)
        result['checks']['statement_status'] = {
            'ok': True,
            'settleTime': st.get('settleTime'),
            'certificateNum': st.get('certificateNum'),
            'items': [
                {
                    'statementName': x.get('statementName'),
                    'isEndOver': x.get('isEndOver'),
                    'certificateCount': len(x.get('certificates') or []),
                }
                for x in (st.get('statements') or [])
            ]
        }
    except Exception as e:
        result['checks']['statement_status'] = {'ok': False, 'error': str(e)}

    JSON_OUT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')

    lines=[]
    lines.append('# 202101 标准答案凭证下游模块测试报告')
    lines.append('')
    lines.append(f'- 账套ID：`{ACCOUNT}`')
    lines.append('- 数据基础：`202101记账凭证.xls` 导入后的标准答案凭证')
    lines.append('')
    cert = result['checks']['certificate_list_api']
    lines.append('## 1. 凭证列表接口')
    lines.append(f"- `totalRow={cert['totalRow']}`，但单页固定返回 `pageSize={cert['backendPageSize']}` 条。")
    lines.append(f"- 第1页前5条：`{cert['page1_first5']}`")
    lines.append(f"- 第2页前5条：`{cert['page2_first5']}`")
    lines.append(f"- `pageNo` 是否失效：`{cert['page_no_effective']}`")
    lines.append('')
    lines.append('## 2. 关键明细账')
    for key in [k for k in result['checks'] if k.startswith('ledger_detail:')]:
        item=result['checks'][key]
        lines.append(f"### {key.split(':',1)[1]}")
        if item['ok']:
            end=item['ending']
            lines.append(f"- 业务分录数：`{item['entry_count']}`")
            lines.append(f"- 期末方向/余额：`{end['balanceDirection']} / {end['balance']}`")
            lines.append(f"- 本期借方/贷方累计：`{end['debtorBalance']} / {end['creditBalance']}`")
        else:
            lines.append(f"- 失败：`{item['error']}`")
    lines.append('')
    lines.append('## 3. 科目余额表 / 总账')
    bal=result['checks']['ledger_balance_level1']
    if bal['ok']:
        lines.append(f"- 科目余额表成功，返回 `{bal['row_count']}` 行。")
    else:
        lines.append(f"- 科目余额表失败：`{bal['error']}`")
    general_keys=[k for k in result['checks'] if k.startswith('ledger_general:')]
    nonempty=[k for k in general_keys if result['checks'][k].get('row_count')]
    lines.append(f"- 总账接口返回非空科目数：`{len(nonempty)}` / `{len(general_keys)}`")
    lines.append('')
    lines.append('## 4. 报表')
    for key in ['report_balance_sheet','report_income','report_cash_flow']:
        item=result['checks'][key]
        lines.append(f"### {key}")
        if item.get('ok'):
            lines.append(f"- 报表行数：`{item['row_count']}`")
            preview=item.get('nonzero_rows', [])[:8]
            lines.append(f"- 关键金额行预览：`{preview}`")
        else:
            lines.append(f"- 报表查询失败：`{item['error']}`")
        if 'check' in item:
            lines.append(f"- 勾稽检查结果：`{item['check']}`")
        if 'check_error' in item:
            lines.append(f"- 勾稽检查失败：`{item['check_error']}`")
    lines.append('')
    st=result['checks']['statement_status']
    lines.append('## 5. 结账状态')
    if st['ok']:
        lines.append(f"- 最近结账时间：`{st['settleTime']}`")
        lines.append(f"- 结账模块项：`{st['items']}`")
    else:
        lines.append(f"- 查询失败：`{st['error']}`")

    OUT.write_text('\n'.join(lines), encoding='utf-8')
    print(str(OUT))
    print(str(JSON_OUT))

if __name__ == '__main__':
    main()
