package com.kakarote.finance.service.impl;

import cn.hutool.core.collection.CollUtil;
import cn.hutool.core.util.ObjectUtil;
import com.alibaba.fastjson.JSONObject;
import com.kakarote.common.entity.UserInfo;
import com.kakarote.common.utils.UserUtil;
import com.kakarote.core.servlet.BaseServiceImpl;
import com.kakarote.finance.common.AccountSet;
import com.kakarote.finance.entity.PO.AdminMenu;
import com.kakarote.finance.entity.PO.AdminRole;
import com.kakarote.finance.entity.PO.FinanceAccountUser;
import com.kakarote.finance.entity.PO.LocalUser;
import com.kakarote.finance.mapper.FinanceAccountUserMapper;
import com.kakarote.finance.service.IAdminMenuService;
import com.kakarote.finance.service.IAdminRoleService;
import com.kakarote.finance.service.IClientAccessService;
import com.kakarote.finance.service.IFinanceAccountUserService;
import com.kakarote.finance.mapper.LocalUserMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;
import java.util.stream.Collectors;

/**
 * <p>
 * 账套员工对应关系表 服务实现类
 * </p>
 *
 * @author dsc
 * @since 2021-08-29
 */
@Service
public class FinanceAccountUserServiceImpl extends BaseServiceImpl<FinanceAccountUserMapper, FinanceAccountUser> implements IFinanceAccountUserService {

    @Autowired
    private IAdminMenuService adminMenuService;

    @Autowired
    private IAdminRoleService adminRoleService;

    @Autowired
    private IClientAccessService clientAccessService;

    @Autowired
    private LocalUserMapper localUserMapper;

    public List<Long> getRoleList() {
        Long userId = UserUtil.getUserId();
        if (userId == null && UserUtil.getUser() != null) {
            userId = UserUtil.getUser().getUserId();
        }
        List<FinanceAccountUser> accountUserList = lambdaQuery()
                .eq(FinanceAccountUser::getAccountId, AccountSet.getAccountSetId())
                .eq(FinanceAccountUser::getUserId, userId)
                .isNotNull(FinanceAccountUser::getRoleId).list();
        if (CollUtil.isEmpty(accountUserList)) {
            return new ArrayList<>();
        }
        return accountUserList.stream().map(FinanceAccountUser::getRoleId).collect(Collectors.toList());
    }

    /**
     * 查询用户所属权限
     *
     * @return obj
     */
    @Override
    public JSONObject financeAuth() {
        Long userId = UserUtil.getUserId();
        if (userId == null && UserUtil.getUser() != null) {
            userId = UserUtil.getUser().getUserId();
        }
        JSONObject result = new JSONObject();
        if (userId == null) {
            return result;
        }
        LocalUser user = localUserMapper.selectById(userId);

        // Platform super admin always has full finance access
        if (user != null && clientAccessService.isPlatformSuperAdmin(user)) {
            result.put("finance", fullFinanceAuth());
            return result;
        }

        // If an account set is already selected in session, use role-based auth for it
        if (AccountSet.getAccountSetId() != null) {
            FinanceAccountUser founderRelation = lambdaQuery()
                    .eq(FinanceAccountUser::getAccountId, AccountSet.getAccountSetId())
                    .eq(FinanceAccountUser::getUserId, userId)
                    .eq(FinanceAccountUser::getIsFounder, 1)
                    .last("limit 1")
                    .one();
            if (founderRelation != null) {
                result.put("finance", fullFinanceAuth());
                return result;
            }
            List<Long> roleIds = getRoleList();
            if (!CollUtil.isEmpty(roleIds)) {
                List<AdminRole> roles = roleIds.stream()
                        .map(adminRoleService::getById)
                        .filter(Objects::nonNull)
                        .collect(Collectors.toList());
                result.put("finance", buildRoleFinanceAuth(roles));
                return result;
            }
        }

        // No account set selected yet — check if user has access to any account
        Long clientId = (user != null) ? user.getClientId() : null;
        List<Long> accessibleAccountIds = clientAccessService.getReadableAccountIds(user, clientId);
        if (!CollUtil.isEmpty(accessibleAccountIds)) {
            result.put("finance", fullFinanceAuth());
        }
        return result;
    }

    /**
     * 财务管理获取角色权限
     *
     * @return
     */
    public List<AdminMenu> queryMenuListByAdmin() {
        UserInfo user = UserUtil.getUser();
        if (user != null && user.isAdmin()) {
            return adminMenuService.queryMenuList(user.getUserId());
        }
        List<Long> roleList = getRoleList();
        if (roleList.size() > 0) {
            return adminMenuService.queryMenuListByRoleIds(roleList);
        }
        return new ArrayList<>();
    }

    @Override
    @Transactional(rollbackFor = Exception.class)
    public boolean saveBatch(Collection<FinanceAccountUser> entityList, int batchSize) {
        if (CollUtil.isEmpty(entityList)) {
            return true;
        }
        for (FinanceAccountUser entity : entityList) {
            save(entity);
        }
        return true;
    }

    private JSONObject createMenu(Set<AdminMenu> adminMenuList, Long parentId) {
        JSONObject jsonObject = new JSONObject();
        adminMenuList.forEach(adminMenu -> {
            if (Objects.equals(parentId, adminMenu.getParentId())) {
                if (Objects.equals(1, adminMenu.getMenuType())) {
                    JSONObject object = createMenu(adminMenuList, adminMenu.getMenuId());
                    if (!object.isEmpty()) {
                        jsonObject.put(adminMenu.getRealm(), object);
                    }
                } else {
                    jsonObject.put(adminMenu.getRealm(), Boolean.TRUE);
                }
            }
        });
        return jsonObject;
    }

    private JSONObject buildRoleFinanceAuth(List<AdminRole> roles) {
        boolean fullAccess = roles.stream().anyMatch(role -> {
            String roleName = role.getRoleName();
            return "主管".equals(roleName) || "会计".equals(roleName);
        });
        if (fullAccess) {
            return fullFinanceAuth();
        }
        return readOnlyFinanceAuth();
    }

    private JSONObject fullFinanceAuth() {
        JSONObject finance = new JSONObject();
        finance.put("subject", createActionMap("read", "save", "update", "delete", "import", "export", "print"));
        finance.put("voucherWord", createActionMap("save", "update", "delete", "read"));
        finance.put("currency", createActionMap("save", "update", "delete", "read"));
        finance.put("systemParam", createActionMap("read", "update"));
        finance.put("financialInitial", createActionMap("read", "update", "export", "import"));
        finance.put("voucher", createActionMap("read", "save", "update", "delete", "export", "print", "import", "insert", "arrangement", "examine", "noExamine"));
        finance.put("voucherSummary", createActionMap("read", "export"));
        finance.put("generalLedger", createActionMap("read", "export", "print"));
        finance.put("subLedger", createActionMap("read", "export", "print"));
        finance.put("accountBalance", createActionMap("read", "export", "print"));
        finance.put("multiColumn", createActionMap("read", "export", "print"));
        finance.put("balanceSheet", createActionMap("read", "update", "export", "print"));
        finance.put("profit", createActionMap("read", "update", "export", "print"));
        finance.put("cashFlow", createActionMap("read", "update", "export", "print"));
        finance.put("checkOut", createActionMap("generate", "profitAndLoss", "checkOut", "cancelClosing"));
        return finance;
    }

    private JSONObject readOnlyFinanceAuth() {
        JSONObject finance = new JSONObject();
        finance.put("subject", createActionMap("read", "export", "print"));
        finance.put("voucherWord", createActionMap("read"));
        finance.put("currency", createActionMap("read"));
        finance.put("systemParam", createActionMap("read"));
        finance.put("financialInitial", createActionMap("read", "export"));
        finance.put("voucher", createActionMap("read", "print", "export"));
        finance.put("voucherSummary", createActionMap("read", "export"));
        finance.put("generalLedger", createActionMap("read", "export", "print"));
        finance.put("subLedger", createActionMap("read", "export", "print"));
        finance.put("accountBalance", createActionMap("read", "export", "print"));
        finance.put("multiColumn", createActionMap("read", "export", "print"));
        finance.put("balanceSheet", createActionMap("read", "export", "print"));
        finance.put("profit", createActionMap("read", "export", "print"));
        finance.put("cashFlow", createActionMap("read", "export", "print"));
        finance.put("checkOut", new JSONObject());
        return finance;
    }

    private JSONObject createActionMap(String... actions) {
        JSONObject object = new JSONObject();
        for (String action : actions) {
            object.put(action, true);
        }
        return object;
    }
}
