# 数据结构改造方案

## 1. 目标

本方案用于把当前“账套 + 账套授权”的结构升级为“客户公司 + 用户归属 + 账套归属 + 账套授权”的结构。

设计原则：

- 尽量少改财务业务表
- 优先补齐边界字段
- 先加结构，再切逻辑
- 超管能力不落到业务授权表

当前项目阶段说明：

- 系统尚未正式上线
- 现有数据均为测试数据
- 因此本次结构方案不以历史数据迁移为重点
- 数据库设计以目标结构正确和开发落地简单为优先
- 本文写到的结构均为本次要落地的结构，不设置增强项独立范围。

## 2. 现有核心表

当前已识别到的关键表：

- `wk_admin_user`
- `wk_finance_account_set`
- `wk_finance_account_user`

它们当前职责如下：

- `wk_admin_user`：系统登录用户
- `wk_finance_account_set`：账套主体
- `wk_finance_account_user`：账套与用户、账套角色关系

当前主要问题：

- 用户没有客户公司归属字段
- 账套没有客户公司归属字段
- 无法从数据库层面表达客户公司隔离

## 3. 新增表设计

## 3.1 客户公司表

本次新增：

- `wk_client_company`

字段：

```sql
CREATE TABLE wk_client_company (
    client_id        BIGINT       NOT NULL PRIMARY KEY,
    client_code      VARCHAR(64)  NOT NULL,
    client_name      VARCHAR(128) NOT NULL,
    status           TINYINT      NOT NULL DEFAULT 1,
    remark           VARCHAR(512) NULL,
    create_user_id   BIGINT       NULL,
    create_time      DATETIME     NOT NULL,
    update_user_id   BIGINT       NULL,
    update_time      DATETIME     NOT NULL
);
```

索引：

```sql
CREATE UNIQUE INDEX uk_client_company_code ON wk_client_company(client_code);
CREATE INDEX idx_client_company_status ON wk_client_company(status);
```

字段说明：

- `client_id`：客户公司主键
- `client_code`：客户公司编码，便于后台管理和外部对接
- `client_name`：客户公司名称
- `status`：启用、停用状态

## 4. 现有表改造

## 4.1 用户表 `wk_admin_user`

新增字段：

```sql
ALTER TABLE wk_admin_user
ADD COLUMN client_id BIGINT NULL,
ADD COLUMN user_type VARCHAR(32) NOT NULL DEFAULT 'client_user';
```

索引：

```sql
CREATE INDEX idx_admin_user_client_id ON wk_admin_user(client_id);
CREATE INDEX idx_admin_user_user_type ON wk_admin_user(user_type);
```

语义：

- `user_type = 'platform_super_admin'`
- `user_type = 'client_user'`

约束规则：

- 平台超级管理员：`client_id` 可为空
- 客户公司用户：`client_id` 必填

不建议只依赖现有 `is_admin` 字段表达全部语义，原因如下：

- `is_admin` 更像旧系统中的管理标记
- 未来会区分平台超管、客户管理员、普通用户
- `user_type` 更利于长期演进

兼容方案：

- 保留 `is_admin`
- 新逻辑逐步迁移到 `user_type`

## 4.2 账套表 `wk_finance_account_set`

新增字段：

```sql
ALTER TABLE wk_finance_account_set
ADD COLUMN client_id BIGINT NULL;
```

索引：

```sql
CREATE INDEX idx_finance_account_set_client_id ON wk_finance_account_set(client_id);
CREATE INDEX idx_finance_account_set_client_status ON wk_finance_account_set(client_id, status);
```

目标规则：

- 每个账套必须属于一个客户公司
- 在正式建表和联调阶段即可直接按 `NOT NULL` 目标推进

## 4.3 账套授权表 `wk_finance_account_user`

本次保留原结构，不新增 `client_id`。

理由：

- 用户通过 `wk_admin_user.client_id` 确定归属
- 账套通过 `wk_finance_account_set.client_id` 确定归属
- 授权时只要强制校验两者一致即可

补充索引：

```sql
CREATE INDEX idx_finance_account_user_account_user ON wk_finance_account_user(account_id, user_id);
CREATE INDEX idx_finance_account_user_user_default ON wk_finance_account_user(user_id, is_default);
```

唯一性约束说明：

- 同一用户在同一账套下可拥有多条记录，因为一条记录对应一个角色

因此本次不对 `(account_id, user_id)` 做唯一约束。

本次也不拆为两张表：

- 账套成员表
- 成员角色关联表

## 5. 本次不做的结构项

## 5.1 客户公司管理员关系表

本次不单独新建。

原因：

- 现在先通过用户角色表达即可
- 额外新表会增加复杂度

本次统一通过用户身份和权限模型表达客户管理员。

## 5.2 客户公司审计日志表

本次不做：

- 记录客户管理员创建账套、授权用户、移除授权等行为

## 6. 数据一致性约束

即使数据库暂不直接加外键，业务层也必须强制执行以下规则：

1. `wk_admin_user.client_id` 与 `wk_finance_account_set.client_id` 是客户隔离根字段
2. `wk_finance_account_user` 中每一条授权关系都必须满足：
   - 用户存在
   - 账套存在
   - 用户和账套的 `client_id` 相同
3. 平台超级管理员不写入 `wk_finance_account_user`

## 7. 建表与改表顺序

由于当前无需考虑历史生产数据迁移，本次直接按以下顺序落库：

### 第一步：创建客户公司表

- 创建 `wk_client_company`

### 第二步：扩展用户表

- 给 `wk_admin_user` 增加 `client_id`
- 给 `wk_admin_user` 增加 `user_type`

### 第三步：扩展账套表

- 给 `wk_finance_account_set` 增加 `client_id`

### 第四步：补索引

- 补用户、账套、账套授权相关索引

### 第五步：开发阶段直接按目标约束使用

- 新创建的客户用户必须带 `client_id`
- 新创建的账套必须带 `client_id`
- 新建授权关系必须校验客户归属一致

## 8. SQL 草案

以下为本次落地草案，执行前按实际数据库版本校验语法。

```sql
CREATE TABLE wk_client_company (
    client_id        BIGINT       NOT NULL PRIMARY KEY,
    client_code      VARCHAR(64)  NOT NULL,
    client_name      VARCHAR(128) NOT NULL,
    status           TINYINT      NOT NULL DEFAULT 1,
    remark           VARCHAR(512) NULL,
    create_user_id   BIGINT       NULL,
    create_time      DATETIME     NOT NULL,
    update_user_id   BIGINT       NULL,
    update_time      DATETIME     NOT NULL
);

CREATE UNIQUE INDEX uk_client_company_code ON wk_client_company(client_code);

ALTER TABLE wk_admin_user
ADD COLUMN client_id BIGINT NULL,
ADD COLUMN user_type VARCHAR(32) NOT NULL DEFAULT 'client_user';

CREATE INDEX idx_admin_user_client_id ON wk_admin_user(client_id);
CREATE INDEX idx_admin_user_user_type ON wk_admin_user(user_type);

ALTER TABLE wk_finance_account_set
ADD COLUMN client_id BIGINT NULL;

CREATE INDEX idx_finance_account_set_client_id ON wk_finance_account_set(client_id);
CREATE INDEX idx_finance_account_set_client_status ON wk_finance_account_set(client_id, status);

CREATE INDEX idx_finance_account_user_account_user ON wk_finance_account_user(account_id, user_id);
CREATE INDEX idx_finance_account_user_user_default ON wk_finance_account_user(user_id, is_default);
```

## 9. 最终结构职责总结

- `wk_client_company`
  - 管客户公司

- `wk_admin_user`
  - 管用户
  - 通过 `client_id` 表达唯一归属

- `wk_finance_account_set`
  - 管账套
  - 通过 `client_id` 表达归属客户公司

- `wk_finance_account_user`
  - 管账套授权
  - 只表达“谁可进入哪个账套、拥有哪些账套角色”

## 10. 结论

本次结构改造的关键不是增加更多业务表，而是补齐客户公司这一层主边界。

只要用户和账套都具备明确 `client_id`，再保留现有账套授权表，就能以较低代价把系统升级到可维护的多客户公司模式。
