# 前端改造清单

## 1. 目标

本清单用于明确本次“客户公司隔离 + 客户内账套授权 + 完整登录闭环”在前端侧需要做哪些改造。

本次前端不是单页补丁式修改，而是一次结构性改造。原因是：

- 当前管理端基本只有账套管理页，没有客户公司管理页和用户管理页。
- 当前授权用户选择组件依赖全局组织架构缓存，而本地后端并没有完整组织架构能力。
- 当前财务布局中的账套切换只考虑“当前用户的账套列表”，没有“平台超管先切客户公司再切账套”的分层。
- 本文列出的前端改造项均为本次必须完成项。

## 2. 基于现有代码的前端现状

## 2.1 现有可复用页面

- 账套管理页：
  - [accountBook.vue](/Users/czj/Desktop/kauiji/financial-kuku/ux/src/views/admin/finance/accountBook.vue)
- 账套初始化弹窗：
  - [AccountStepDialog.vue](/Users/czj/Desktop/kauiji/financial-kuku/ux/src/views/admin/finance/components/AccountStepDialog.vue)
- 财务主布局：
  - [FmLayout.vue](/Users/czj/Desktop/kauiji/financial-kuku/ux/src/views/layout/FmLayout.vue)
- 管理端布局：
  - [AdminLayout.vue](/Users/czj/Desktop/kauiji/financial-kuku/ux/src/views/layout/AdminLayout.vue)

## 2.2 当前前端的关键限制

### 2.2.1 管理端路由过少

当前管理端路由几乎只有财务账套管理：

- [admin.js](/Users/czj/Desktop/kauiji/financial-kuku/ux/src/router/modules/admin.js)

这意味着本次必须新增：

- 客户公司管理路由
- 客户公司用户管理路由
- 可能还需要客户公司详情页或编辑弹窗

### 2.2.2 授权组件依赖全局组织架构缓存

当前账套授权使用：

- [Dialog.vue](/Users/czj/Desktop/kauiji/financial-kuku/ux/src/components/NewCom/WkUserDialogSelect/Dialog.vue)

它的数据源来自：

- [user.js](/Users/czj/Desktop/kauiji/financial-kuku/ux/src/store/modules/user.js)

而缓存来源是：

- `adminUser/queryUserList`
- `adminUser/queryDeptTree`
- `adminUser/queryOrganizationInfo`

但当前本地后端只提供兼容存根，不是真实组织架构能力。

结论：

- 这次不能继续依赖“全局组织树 = 可授权用户源”
- 需要改为“客户公司内用户列表 = 可授权用户源”

### 2.2.3 平台超管财务切换链路不满足需求

当前财务布局中的账套切换只有一层：

- 当前账套下拉

文件：

- [FmLayout.vue](/Users/czj/Desktop/kauiji/financial-kuku/ux/src/views/layout/FmLayout.vue)

但本次已经明确：

- 平台超级管理员应先选择客户公司
- 再在该客户公司内切换账套

因此财务主布局必须重构切换入口。

### 2.2.4 用户信息和权限初始化不够表达客户边界

当前用户信息只返回基础登录信息：

- [personCenter.js](/Users/czj/Desktop/kauiji/financial-kuku/ux/src/api/user/personCenter.js)

前端登录态初始化链路：

- [user.js](/Users/czj/Desktop/kauiji/financial-kuku/ux/src/store/modules/user.js)
- [permission.js](/Users/czj/Desktop/kauiji/financial-kuku/ux/src/permission.js)

后续必须让前端拿到更完整的身份信息，例如：

- 是否平台超管
- 所属客户公司
- 是否客户公司管理员

## 3. 前端总体设计原则

## 3.1 管理端与业务端分层

前端应明确区分两类使用场景：

- 管理端：
  - 客户公司管理
  - 用户管理
  - 账套管理
  - 账套授权

- 财务业务端：
  - 切换客户公司
  - 切换账套
  - 进入财务工作台与各业务模块

## 3.2 平台超管视图与客户管理员视图分流

同一个页面不应通过大量 `if/else` 同时兼容两类角色的所有逻辑。

处理原则：

- 页面可以复用
- 但数据源、入口、顶部筛选、按钮集要分层处理

## 3.3 用户选择组件去组织树依赖

本次先采用“用户列表选择”方案，不做“部门树授权”。

原因：

- 后端无真实组织树能力
- 当前主线需求是客户隔离和账套授权
- 先确保闭环，再考虑组织架构

## 3.4 Store 中的“全局组织架构缓存”与“客户内授权用户列表”分离

当前 `userDeptObj/userDeptMap/searchUserDept` 是全局级缓存。

本次要求：

- 保留全局用户组织缓存逻辑，但逐步弱化它在账套授权中的用途
- 新增“客户公司内用户列表”专用 store 或页面内状态

## 4. 页面级改造清单

## 4.1 新增“客户公司管理”页面

新增页面：

- `ux/src/views/admin/clientCompany/index.vue`

功能：

- 列表
- 搜索
- 新建客户公司
- 编辑客户公司
- 停用/启用客户公司

字段：

- 客户公司名称
- 客户公司编码
- 联系人
- 联系电话
- 备注
- 状态

使用者：

- 平台超级管理员

## 4.2 新增“客户公司用户管理”页面

新增页面：

- `ux/src/views/admin/clientUser/index.vue`

功能：

- 查看当前客户公司用户列表
- 新建用户
- 编辑用户
- 启用/停用用户
- 设置/取消客户管理员身份
- 重置密码

字段：

- 登录账号
- 姓名
- 手机号
- 状态
- 是否客户管理员
- 所属客户公司

视图规则：

- 平台超管：可按客户公司切换查看用户
- 客户公司管理员：只看本公司用户

## 4.3 改造“账套管理”页面

现有页面：

- [accountBook.vue](/Users/czj/Desktop/kauiji/financial-kuku/ux/src/views/admin/finance/accountBook.vue)

改造为：

- 平台超管进入时：
  - 页面顶部先选客户公司
  - 选中客户公司后再加载该公司的账套
- 客户公司管理员进入时：
  - 默认只显示本公司账套

需要改造的点：

- 列表数据源
- 顶部筛选区
- 新建账套时自动带入当前客户公司
- 授权弹窗只能选择当前客户公司用户

## 4.4 改造“账套初始化弹窗”

现有页面：

- [AccountStepDialog.vue](/Users/czj/Desktop/kauiji/financial-kuku/ux/src/views/admin/finance/components/AccountStepDialog.vue)

改造要求：

- 继续保留
- 但初始化前必须基于新的账套访问权和客户公司上下文判断
- 初始化成功后跳转逻辑要兼容新的客户公司和账套切换状态

## 4.5 改造财务主布局的切换体验

现有页面：

- [FmLayout.vue](/Users/czj/Desktop/kauiji/financial-kuku/ux/src/views/layout/FmLayout.vue)

改造目标：

- 平台超管：
  - 顶部新增“客户公司切换”
  - 账套下拉只展示当前选中客户公司的账套
- 客户公司用户：
  - 不展示客户公司切换
  - 只展示自己被授权的账套下拉

交互：

- 左侧或顶部优先展示当前客户公司
- 右侧账套下拉展示当前客户公司内可切换账套

## 4.6 无账套授权提示页或空状态

当前逻辑位于：

- [finance.js](/Users/czj/Desktop/kauiji/financial-kuku/ux/src/store/modules/finance.js)

当前只是简单弹框提示。

本次要求：

- 对普通用户：
  - 若没有任何账套授权，显示明确提示
  - 提示联系本公司管理员授权
- 对客户公司管理员：
  - 若本公司无账套，可引导去创建账套
- 对平台超管：
  - 若未选客户公司，应先引导选择客户公司

## 5. 路由改造清单

## 5.1 管理端新增路由

在：

- [admin.js](/Users/czj/Desktop/kauiji/financial-kuku/ux/src/router/modules/admin.js)

新增模块：

- 客户公司管理
- 客户公司用户管理
- 财务账套管理

结构示意：

```js
/manage/client-company
/manage/client-user
/manage/finance/handle
```

## 5.2 路由权限元信息调整

当前主要依赖：

- `meta.permissions`

本次新增更明确的前端权限点，例如：

- `manage.clientCompany`
- `manage.clientUser`
- `manage.finance.accountSet`

这样页面入口和按钮显隐才会清晰。

## 6. Store 改造清单

## 6.1 用户身份信息增强

文件：

- [user.js](/Users/czj/Desktop/kauiji/financial-kuku/ux/src/store/modules/user.js)

新增用户态字段：

- `clientId`
- `clientName`
- `isPlatformSuperAdmin`
- `isClientAdmin`

这些字段应从登录用户接口中拿到。

## 6.2 财务上下文增强

文件：

- [finance.js](/Users/czj/Desktop/kauiji/financial-kuku/ux/src/store/modules/finance.js)

新增状态：

- `currentClient`
- `clientListForFinance`
- `accountListByCurrentClient`

行为变化：

- 平台超管先确定 `currentClient`
- 再请求该客户公司的账套列表
- 再确定默认账套

## 6.3 组织缓存与授权候选用户分离

当前：

- `userDeptObj`
- `userDeptMap`
- `searchUserDept`

要求：

- 不删除现有结构
- 但账套授权页不要继续依赖这套全局缓存
- 新增按客户公司查询用户列表的独立接口和状态

## 7. 组件改造清单

## 7.1 账套授权用户选择组件

现有：

- [Dialog.vue](/Users/czj/Desktop/kauiji/financial-kuku/ux/src/components/NewCom/WkUserDialogSelect/Dialog.vue)

结论：

- 本次不继续直接复用为账套授权主组件

方案：

- 新增“客户公司用户选择弹窗”轻量版组件
- 只支持用户列表搜索与勾选
- 不支持部门树
- 不依赖 `userDeptObj`

新组件：

- `ux/src/components/ClientUserSelect/Dialog.vue`

## 7.2 导航栏与顶部切换组件

文件：

- [Navbar.vue](/Users/czj/Desktop/kauiji/financial-kuku/ux/src/views/layout/components/Navbar.vue)
- [ManagerNavbar.vue](/Users/czj/Desktop/kauiji/financial-kuku/ux/src/views/layout/components/ManagerNavbar.vue)

要求：

- 增加“当前客户公司”展示
- 平台超管在财务端可切换客户公司
- 客户公司管理员不展示客户公司切换控件

## 8. API 接口联动要求

前端改造依赖后端提供以下能力：

- 客户公司列表
- 客户公司详情
- 客户公司保存/更新/启停
- 客户公司用户列表
- 客户公司用户新增/编辑/状态切换/重置密码
- 按客户公司范围查询账套
- 按客户公司范围查询可授权用户
- 当前登录用户返回更完整身份信息

## 9. 登录闭环前端方案

## 9.1 创建用户

- 由平台超管或客户管理员创建用户
- 设置登录账号和初始密码

## 9.2 用户登录

- 继续沿用账号密码登录页
- 不依赖短信验证码

## 9.3 登录后初始化

前端应根据用户身份做不同初始化：

- 平台超管：
  - 获取客户公司列表
  - 默认进入客户公司管理或上次访问客户公司
- 客户公司管理员：
  - 默认进入本公司管理视图或财务视图
- 普通用户：
  - 直接进入财务端账套选择逻辑

## 9.4 无账套授权场景

- 普通用户登录后无账套授权：
  - 显示空状态页
  - 文案指向“请联系本公司管理员授权账套”

## 10. 前端实施顺序

### 第一阶段

- 登录用户信息结构增强
- 管理端新路由骨架
- 客户公司管理页

### 第二阶段

- 客户公司用户管理页
- 重置密码、启停用户

### 第三阶段

- 账套管理页改造成客户公司内视图
- 新的客户公司用户选择弹窗

### 第四阶段

- 财务主布局加入客户公司切换
- 完成平台超管两层切换体验
- 补无账套空状态

## 11. 本次前端不纳入的内容

- 真实部门树管理
- 部门树授权账套
- 手机验证码登录
- 手机验证码找回密码

原因：

- 后端当前没有可用的生产级支撑
- 会明显稀释本次主线目标

## 12. 结论

本次前端改造不是“账套页加几个字段”，而是要完成以下四件事：

- 新增客户公司管理能力
- 新增客户公司用户管理能力
- 重构账套授权所依赖的用户选择方式
- 重构平台超管在财务端的客户公司/账套双层切换体验

在这个前提下，现有账套管理页和财务业务页仍然可以继续沿用主体结构，但必须建立在新的客户公司边界和身份模型上。
