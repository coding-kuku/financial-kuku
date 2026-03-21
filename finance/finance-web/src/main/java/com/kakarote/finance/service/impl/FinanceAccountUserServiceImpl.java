package com.kakarote.finance.service.impl;

import cn.hutool.core.collection.CollUtil;
import cn.hutool.core.util.ObjectUtil;
import com.alibaba.fastjson.JSONObject;
import com.kakarote.common.entity.UserInfo;
import com.kakarote.common.utils.UserUtil;
import com.kakarote.core.servlet.BaseServiceImpl;
import com.kakarote.finance.common.AccountSet;
import com.kakarote.finance.constant.FinanceConst;
import com.kakarote.finance.entity.PO.AdminMenu;
import com.kakarote.finance.entity.PO.FinanceAccountUser;
import com.kakarote.finance.mapper.FinanceAccountUserMapper;
import com.kakarote.finance.service.IAdminMenuService;
import com.kakarote.finance.service.IAdminRoleService;
import com.kakarote.finance.service.IFinanceAccountUserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.*;
import java.util.stream.Collectors;

import com.kakarote.core.common.Const;

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
        JSONObject auth = adminRoleService.auth(userId);
        JSONObject result = new JSONObject();
        if (ObjectUtil.isNotNull(auth) && ObjectUtil.isNotNull(auth.getJSONObject(FinanceConst.FINANCE_SERVICE))) {
            result.put(FinanceConst.FINANCE_SERVICE, auth.getJSONObject(FinanceConst.FINANCE_SERVICE));
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
}
