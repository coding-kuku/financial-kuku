# 202101 按新版 Skill 重新判断报告

## 范围

- 数据源：`/Users/czj/Desktop/kauiji/2021银行明细.xls` 的 `202101` 工作表
- 规则源：`skills/sme-accounting-wukong-flow/SKILL.md` 中新增的 `Enhanced Auto-Decision Rules`
- 本次判断明确忽略任何“标准答案”文件

## 结果摘要

- 有效流水：46 条
- 建议直接/条件入账：23 条
- 建议暂缓：23 条
- 可入账金额合计：156296.58
- 暂缓金额合计：19957.27

## 本次相较旧规则的主要提升

- 将 2 条“流入但备注含采购”的流水改判为客户回款/往来回笼候选。
- 将 1 条 500.00 支付宝备付金改判为其他货币资金，不再一律挂起。
- 对支付宝商户已可做穿透后分类候选，不再只停留在“支付宝客户备付金”。
- 对“公司名 + 货款”的对公付款继续判为可入账，但口径改为应付账款/预付账款二选一，更贴近业务链。
- 对自然人付款新增了映射优先规则；但在没有映射表时仍保持审慎。

## 仍然无法自动放行的核心原因

- 缺社保分项清单与企业/个人承担拆分。
- 缺私户到真实供应商的映射资料。
- 缺支付宝订单号、商户用途、发票或资产属性证明。
- 缺到货/入库信息，无法稳定决定“应付账款”还是“预付账款”，更无法完成库存链。

## 合并建议

- 20210130 奥艺(上海)贸易有限公司 可按同日同主体合并, 共2笔, 金额1412.66
- 20210130 上海童励科技有限公司 可按同日同主体合并, 共2笔, 金额179.92

## 分类分布

- procurement_payment: 17 条
- procurement_payment_unmapped_person: 11 条
- alipay_procurement_or_expense: 11 条
- bank_fee: 2 条
- sales_collection_or_current_account_return: 2 条
- payroll_social_security: 1 条
- transfer_to_other_monetary_funds: 1 条
- procurement_payment_mapped_person: 1 条
