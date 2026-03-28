# -*- coding: utf-8 -*-
import json
import re
import sys
from collections import OrderedDict
from pathlib import Path

import xlrd

sys.path.insert(0, 'agent-harness')
from cli_anything.wukong.utils.wukong_backend import WukongClient
from cli_anything.wukong.core.session import load_session
from cli_anything.wukong.core import certificate as cert_core

ACCOUNT_ID = '2036268933673287680'
XLS_PATH = '/Users/czj/Desktop/kauiji/202101记账凭证.xls'
BACKUP_PATH = Path('jietu/jan202101_preimport_backup.json')
IMPORT_SUMMARY = Path('jietu/jan202101_import_summary.json')

ADJUVANTS = {
    '客户': {'id': '2036269088271138816', 'label': 1},
    '供应商': {'id': '2036269088271138817', 'label': 2},
    '存货': {'id': '2036269088271138821', 'label': 6},
}
VOUCHER_NAME_MAP = {'银收': '收', '银付': '付', '转': '转'}
CODE_ALIAS = {
    '1002001': '1002',
    '1012001': '1012',
    '5603002': '560303',
    '1221': '122101',
    '221100201': '221101',
    '221100202': '221101',
    '221100203': '221101',
    '221100204': '221101',
    '221100205': '221101',
}

CREATE_SUBJECTS = [
    {'code': '5601001', 'name': '销售费用-销售人员职工薪酬', 'parent_code': '5601', 'type': 5, 'direction': 1},
    {'code': '5602001', 'name': '管理费用-管理人员职工薪酬', 'parent_code': '5602', 'type': 5, 'direction': 1},
    {'code': '5602013', 'name': '管理费用-社保费', 'parent_code': '5602', 'type': 5, 'direction': 1},
    {'code': '2211001', 'name': '应付职工薪酬-工资及奖金', 'parent_code': '2211', 'type': 2, 'direction': 2},
    {'code': '5403002', 'name': '税金及附加-印花税', 'parent_code': '5403', 'type': 5, 'direction': 1},
    {'code': '2221017', 'name': '应交税费-印花税', 'parent_code': '2221', 'type': 2, 'direction': 2},
]


def get_client():
    sess = load_session()
    client = WukongClient(sess['base_url'], token=sess['token'])
    client.post('/financeAccountSet/switchAccountSet', params={'accountId': ACCOUNT_ID})
    return client


def load_xls_groups(path):
    book = xlrd.open_workbook(path)
    s = book.sheet_by_name('凭证列表')
    groups = OrderedDict()
    for i in range(1, s.nrows):
        row = s.row_values(i)
        vnum = str(row[1]).strip()
        if not vnum:
            continue
        groups.setdefault(vnum, {'date': str(row[0]).strip(), 'voucher_num': vnum, 'digest': str(row[2]).strip(), 'rows': []})
        groups[vnum]['rows'].append(row)
    return groups


def query_existing_jan_certs(client):
    data = client.post('/financeCertificate/queryPageList', {
        'pageNo': 1,
        'pageSize': 200,
        'startTime': '202101',
        'endTime': '202101',
    }) or {}
    if isinstance(data, dict) and 'records' not in data and 'list' in data:
        data = {'records': data.get('list', []), 'total': data.get('totalRow')}
    return data


def backup_current(client):
    data = query_existing_jan_certs(client)
    BACKUP_PATH.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    return data


def get_all_subjects(client):
    return client.post('/financeSubject/queryListByType', params={'isTree': 0}) or []


def get_subject_map(client, current_records=None):
    subject_map = {}
    for subj in get_all_subjects(client):
        subject_map[str(subj['number'])] = {'id': str(subj['subjectId']), 'name': subj['subjectName'], 'raw': subj}
    if current_records:
        for rec in current_records:
            for d in rec.get('certificateDetails', []):
                num = str(d.get('subjectNumber') or '').strip()
                sid = str(d.get('subjectId') or '').strip()
                name = str(d.get('subjectName') or '').strip()
                if num and sid:
                    subject_map[num] = {'id': sid, 'name': name, 'raw': None}
    return subject_map


def ensure_subjects(client, subject_map):
    all_subjects = get_all_subjects(client)
    by_code = {str(s['number']): s for s in all_subjects}
    created = []
    for item in CREATE_SUBJECTS:
        if item['code'] in subject_map:
            continue
        parent = by_code[item['parent_code']]
        body = {
            'number': item['code'],
            'subjectName': item['name'],
            'type': item['type'],
            'category': parent['category'],
            'balanceDirection': item['direction'],
            'currencyType': 1,
            'isEnd': 1,
            'parentId': int(parent['subjectId']),
        }
        client.post('/financeSubject/add', body)
        created.append(item['code'])
    refreshed = get_subject_map(client)
    return refreshed, created


def query_label_names(client, adjuvant_id):
    items = client.post('/financeCertificate/queryLabelName', params={'adjuvantId': adjuvant_id}) or []
    return items


def ensure_adjuvants(client, groups):
    expected = {
        '客户': {},
        '供应商': {},
        '存货': {},
    }
    for g in groups.values():
        for row in g['rows']:
            ccode, cname = str(row[12]).strip(), str(row[13]).strip()
            scode, sname = str(row[14]).strip(), str(row[15]).strip()
            icode, iname = str(row[22]).strip(), str(row[23]).strip()
            if cname and not cname.isdigit():
                expected['客户'][cname] = ccode or ''
            if sname and not sname.isdigit():
                expected['供应商'][sname] = scode or ''
            if iname and not iname.isdigit():
                expected['存货'][iname] = icode or ''

    existing = {}
    for name, meta in ADJUVANTS.items():
        items = query_label_names(client, meta['id'])
        existing[name] = {it['name']: it for it in items}

    updates = []
    # repair malformed supplier cards from previous attempts if present
    weird_suppliers = {it['name']: it for it in query_label_names(client, ADJUVANTS['供应商']['id'])}
    if '37' in weird_suppliers and '徐州欧耐家具有限公司' not in weird_suppliers:
        client.post('/financeAdjuvantCarte/update', {
            'carteId': int(weird_suppliers['37']['relationId']),
            'carteNumber': '37',
            'carteName': '徐州欧耐家具有限公司',
            'adjuvantId': int(ADJUVANTS['供应商']['id']),
        })
        updates.append('修正供应商 37 -> 徐州欧耐家具有限公司')
    weird_suppliers = {it['name']: it for it in query_label_names(client, ADJUVANTS['供应商']['id'])}
    if '1' in weird_suppliers and '东莞市米纯服饰有限公司' not in weird_suppliers:
        client.post('/financeAdjuvantCarte/update', {
            'carteId': int(weird_suppliers['1']['relationId']),
            'carteNumber': '39',
            'carteName': '东莞市米纯服饰有限公司',
            'adjuvantId': int(ADJUVANTS['供应商']['id']),
        })
        updates.append('修正供应商 39 -> 东莞市米纯服饰有限公司')

    created = []
    for kind in ['客户', '供应商', '存货']:
        items = {it['name']: it for it in query_label_names(client, ADJUVANTS[kind]['id'])}
        for name, code in expected[kind].items():
            if name in items:
                continue
            if kind == '存货' and name == '小卫衣' and '童装卫衣' in items:
                client.post('/financeAdjuvantCarte/update', {
                    'carteId': int(items['童装卫衣']['relationId']),
                    'carteNumber': code or 'C0002',
                    'carteName': '小卫衣',
                    'adjuvantId': int(ADJUVANTS[kind]['id']),
                })
                updates.append('修正存货 童装卫衣 -> 小卫衣')
                continue
            body = {
                'carteNumber': code or name,
                'carteName': name,
                'adjuvantId': int(ADJUVANTS[kind]['id']),
            }
            client.post('/financeAdjuvantCarte/add', body)
            created.append(f'{kind}:{code}:{name}')

    final_maps = {}
    for kind in ['客户', '供应商', '存货']:
        items = query_label_names(client, ADJUVANTS[kind]['id'])
        final_maps[kind] = {it['name']: it for it in items}
    return final_maps, updates, created


def delete_current_jan(client, backup_data):
    ids = [int(r['certificateId']) for r in backup_data.get('records', [])]
    if ids:
        cert_core.delete_certificates(client, ids)
    return ids


def build_payloads(groups, subject_map, adjuvant_maps, voucher_ids):
    payloads = []
    for v in groups.values():
        prefix = v['voucher_num'].split('-')[0]
        voucher_name = VOUCHER_NAME_MAP[prefix]
        voucher_id = voucher_ids[voucher_name]
        cert_num = int(v['voucher_num'].split('-')[1])
        details = []
        for row in v['rows']:
            code = str(row[3]).strip()
            lookup_code = code if code in subject_map else CODE_ALIAS.get(code, code)
            if lookup_code not in subject_map:
                raise RuntimeError(f'科目编码缺失映射: {code} -> {lookup_code} {row[4]} in {v["voucher_num"]}')
            associations = []
            cname = str(row[13]).strip()
            sname = str(row[15]).strip()
            iname = str(row[23]).strip()
            if cname and not cname.isdigit():
                associations.append({
                    'label': ADJUVANTS['客户']['label'],
                    'labelName': '客户',
                    'relationId': int(adjuvant_maps['客户'][cname]['relationId']),
                    'adjuvantId': int(ADJUVANTS['客户']['id']),
                })
            if sname and not sname.isdigit():
                associations.append({
                    'label': ADJUVANTS['供应商']['label'],
                    'labelName': '供应商',
                    'relationId': int(adjuvant_maps['供应商'][sname]['relationId']),
                    'adjuvantId': int(ADJUVANTS['供应商']['id']),
                })
            if iname and not iname.isdigit():
                associations.append({
                    'label': ADJUVANTS['存货']['label'],
                    'labelName': '存货',
                    'relationId': int(adjuvant_maps['存货'][iname]['relationId']),
                    'adjuvantId': int(ADJUVANTS['存货']['id']),
                })
            details.append({
                'subjectId': int(subject_map[lookup_code]['id']),
                'digestContent': v['digest'],
                'debtorBalance': float(row[8] or 0),
                'creditBalance': float(row[11] or 0),
                'associationBOS': associations,
            })
        payloads.append({
            'voucher_name': voucher_name,
            'voucher_id': int(voucher_id),
            'date': v['date'],
            'certificate_num': cert_num,
            'voucher_num': v['voucher_num'],
            'digest': v['digest'],
            'details': details,
        })
    return payloads


def import_payloads(client, payloads):
    created = []
    for p in payloads:
        result = cert_core.add_certificate(client, p['voucher_id'], p['date'], p['details'], certificate_num=p['certificate_num'])
        created.append({'voucher_num': p['voucher_num'], 'certificateId': result.get('certificateId'), 'date': p['date']})
    return created


def main():
    client = get_client()
    groups = load_xls_groups(XLS_PATH)

    backup_data = backup_current(client)
    current_records = backup_data.get('records', [])

    voucher_list = client.post('/financeVoucher/queryList') or client.post('/financeVoucher/queryListByType') or []
    if not voucher_list:
        voucher_list = client.post('/financeVoucher/queryList', {}) or []
    if not voucher_list:
        voucher_list = client.post('/financeVoucher/queryList', params={}) or []
    voucher_ids = {v['voucherName']: v['voucherId'] for v in voucher_list}

    adjuvant_maps, adjuvant_updates, adjuvant_created = ensure_adjuvants(client, groups)

    subject_map = get_subject_map(client, current_records=current_records)
    subject_map, subject_created = ensure_subjects(client, subject_map)
    subject_map = get_subject_map(client, current_records=current_records)

    payloads = build_payloads(groups, subject_map, adjuvant_maps, voucher_ids)

    deleted_ids = delete_current_jan(client, backup_data)
    created = import_payloads(client, payloads)

    verify = query_existing_jan_certs(client)
    summary = {
        'backup_file': str(BACKUP_PATH),
        'deleted_certificate_ids': deleted_ids,
        'adjuvant_updates': adjuvant_updates,
        'adjuvant_created': adjuvant_created,
        'subject_created': subject_created,
        'imported_count': len(created),
        'verify_total': verify.get('total'),
        'created': created[:10],
    }
    IMPORT_SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(summary, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
