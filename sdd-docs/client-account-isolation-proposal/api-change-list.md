# 接口改造清单

## 1. 目标

本清单用于说明现有接口在“客户公司隔离 + 客户内账套授权”模式下应如何调整。

原则：

- 先做边界控制，再做功能权限控制
- 能保留接口路径尽量保留，减少前端震荡
- 每个接口都要明确调用人身份和资源边界
- 本文列出的接口改造项均为本次必须完成项。

## 2. 当前重点接口

本次优先关注以下接口和前端调用点：

- `financeAccountSet/queryPageList`
- `financeAccountSet/getAccountSetById`
- `financeAccountSet/addAccount`
- `financeAccountSet/updateAccount`
- `financeAccountSet/getUserByAccountId`
- `financeAccountSet/saveAccountAuth`
- `financeAccountSet/deleteAccountUser`
- `financeAccountSet/saveAccountSet`
- `financeAccountSet/getAccountSetList`
- `financeAccountSet/switchAccountSet`
- `financeAccountUser/financeAuth`
- `adminRole/auth`

## 3. 接口改造原则

### 3.1 所有账套相关接口统一增加前置校验

所有账套接口统一调用：

- `ClientScopeService`
- `AccountPermissionService`

统一处理：

- 当前用户是否为平台超管
- 当前用户属于哪个客户公司
- 目标账套属于哪个客户公司
- 当前用户是否具备账套访问权或管理权

### 3.2 Controller 不直接拼业务规则

Controller 只负责路由和参数，不负责客户隔离判断。

### 3.3 错误返回要统一

统一返回：

- 无客户范围权限：`SYSTEM_NO_AUTH`
- 有客户范围但无账套访问权：`SYSTEM_NO_AUTH`
- 资源不存在：`DATA_NOT_FOUND`

## 4. 逐接口改造说明

## 4.1 `POST /financeAccountSet/queryPageList`

### 当前问题

- 当前实现直接返回全部账套。

### 目标行为

- 平台超级管理员：返回全部客户公司的账套
- 客户公司管理员：返回本公司账套
- 普通用户：本次不开放该管理接口

### 改造要求

- 保留接口路径
- 服务层增加按 `client_id` 过滤
- 平台超管筛选客户时，接口增加参数：
  - `clientId`
  - `status`

### 前端影响

- `/#/manage/finance/handle` 的列表数据将变为“当前公司账套视图”或“指定客户账套视图”

## 4.2 `POST /financeAccountSet/getAccountSetById`

### 当前问题

- 仅按 `accountId` 查询，没有边界控制

### 目标行为

- 平台超管：可查任意账套
- 客户公司管理员：只能查本公司账套
- 普通用户：仅在确有业务需求时允许查自己已授权账套

### 改造要求

- 服务层先查账套
- 校验该账套是否属于当前用户可访问范围

## 4.3 `POST /financeAccountSet/addAccount`

### 当前问题

- 当前新增账套时没有客户公司归属概念

### 目标行为

- 平台超管：可为任意客户公司新建账套
- 客户公司管理员：只能为自己公司新建账套

### 改造要求

- 请求体中支持 `clientId`
- 如果当前用户不是平台超管，则忽略前端传入的 `clientId`，强制使用当前用户 `clientId`
- 新增账套时写入 `wk_finance_account_set.client_id`

## 4.4 `POST /financeAccountSet/updateAccount`

### 当前问题

- 可编辑账套，但未强校验客户边界

### 目标行为

- 平台超管：可编辑任意账套
- 客户公司管理员：只能编辑本公司账套

### 改造要求

- 根据 `accountId` 取账套
- 校验当前用户是否可管理该账套
- 禁止修改账套 `client_id`

## 4.5 `POST /financeAccountSet/getUserByAccountId`

### 当前问题

- 当前接口能按账套直接返回成员及角色，是明显的越权风险点

### 目标行为

- 平台超管：可查看任意账套成员
- 客户公司管理员：可查看本公司账套成员
- 普通用户：默认无权查看

### 改造要求

- 服务层增加“账套管理权限”校验
- 返回的用户列表必须来自该账套所属客户公司

## 4.6 `POST /financeAccountSet/saveAccountAuth`

### 当前问题

- 当前逻辑可保存账套授权，但没有客户边界校验

### 目标行为

- 平台超管：可维护任意账套授权
- 客户公司管理员：只能维护本公司账套授权
- 被授权用户必须属于该账套所属客户公司

### 改造要求

- 先校验调用人是否可管理该账套
- 再校验待授权用户列表是否全部属于该账套同一 `client_id`
- 若发现跨客户用户，整次请求拒绝

## 4.7 `POST /financeAccountSet/deleteAccountUser`

### 当前问题

- 当前接口按账套和用户删除授权，未做范围校验

### 目标行为

- 平台超管：可删除任意账套授权
- 客户公司管理员：可删除本公司账套授权

### 改造要求

- 校验账套是否在当前用户管理范围内
- 校验被删除用户是否属于该账套所属客户公司

## 4.8 `POST /financeAccountSet/saveAccountSet`

### 当前问题

- 当前接口用于开账初始化，默认认为当前人已能进入账套

### 目标行为

- 只能对当前人有权操作的账套执行初始化

### 改造要求

- 执行初始化前校验：
  - 当前账套可访问
  - 当前用户有初始化权限

## 4.9 `POST /financeAccountSet/getAccountSetList`

### 当前问题

- 当前接口本质是账套切换列表
- 超管逻辑会自动把自己写进所有账套成员表

### 目标行为

- 平台超管：可获得全量账套切换视图，但不写入业务授权表
- 客户公司用户：只获得自己被授权的账套列表

### 改造要求

- 去掉“超管自动补成员”的逻辑
- 平台超管走独立分支直接返回可切换账套
- 普通用户按 `wk_finance_account_user` 返回授权账套

## 4.10 `POST /financeAccountSet/switchAccountSet`

### 当前问题

- 当前切换主要依赖成员表更新默认账套，但缺少访问边界强校验

### 目标行为

- 平台超管：可切换任意账套
- 客户公司用户：只能切换自己有访问权的账套

### 改造要求

- 切换前先校验账套访问权
- 若无权，直接拒绝

## 4.11 `POST /financeAccountUser/financeAuth`

### 当前问题

- 当前财务权限来源不够准确，未真正基于“当前账套授权角色”

### 目标行为

- 返回当前用户在当前账套下的财务权限树

### 改造要求

- 优先根据当前账套上下文查 `wk_finance_account_user`
- 取当前用户在当前账套下的角色
- 根据角色返回财务菜单权限
- 平台超管可走全权限分支，但不需要伪造成账套成员

## 4.12 `POST /adminRole/auth`

### 当前问题

- 当前全局菜单权限逻辑与账套内财务权限界限不清

### 目标行为

- 仅返回系统级、平台级、后台管理级权限
- 账套内财务权限不要继续混在这里处理

## 5. 本次新增接口

本次新增以下接口。

## 5.1 客户公司管理接口

- `POST /clientCompany/queryPageList`
- `POST /clientCompany/getById`
- `POST /clientCompany/save`
- `POST /clientCompany/update`
- `POST /clientCompany/changeStatus`

用途：

- 平台超级管理员管理客户公司

## 5.2 客户公司用户管理接口

- `POST /clientUser/queryPageList`
- `POST /clientUser/save`
- `POST /clientUser/update`
- `POST /clientUser/resetPassword`
- `POST /clientUser/changeStatus`

用途：

- 平台超管管理所有用户
- 客户公司管理员管理本公司用户

## 5.3 账套授权候选用户接口

本次新增：

- `POST /financeAccountSet/queryAssignableUsers`

用途：

- 返回当前账套所属客户公司内可授权用户列表

这样可以避免前端继续沿用全局用户接口。

## 6. 前端调用改造清单

## 6.1 `ux/src/api/admin/accountBook.js`

需要保留但重定义行为的接口：

- `queryPageList`
- `getUserByaccountId`
- `addAccount`
- `updateAccount`
- `deleteAccountUser`
- `saveAccountAuth`
- `saveAccountSet`
- `getAccountSetListAPI`
- `switchAccountSetAPI`

## 6.2 `ux/src/views/admin/finance/accountBook.vue`

改造重点：

- 列表只展示当前客户公司账套
- 授权时只允许选择当前客户公司用户
- 普通用户不应进入本页

## 6.3 `ux/src/store/modules/finance.js`

改造重点：

- `getAccountSetListAPI` 返回值需要严格限定为当前用户可切换账套
- 切换账套失败时需给出明确提示

## 7. 实施顺序

1. 先改后端校验和数据边界
2. 再改返回结构
3. 最后改前端页面和交互

原因：

- 前端限制无法代替后端安全
- 先保安全，再保体验

## 8. 结论

本次接口改造的重点不是“增删几个字段”，而是把所有账套相关接口从全局视角改成客户公司边界内视角。

只要接口层把边界守住，现有账套业务逻辑和前端交互都可以较平滑地演进。
