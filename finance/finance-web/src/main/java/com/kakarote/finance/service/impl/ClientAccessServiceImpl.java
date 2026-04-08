package com.kakarote.finance.service.impl;

import cn.hutool.core.collection.CollUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.kakarote.common.utils.UserUtil;
import com.kakarote.core.common.enums.SystemCodeEnum;
import com.kakarote.core.exception.CrmException;
import com.kakarote.finance.constant.LocalUserTypeEnum;
import com.kakarote.finance.entity.PO.FinanceAccountSet;
import com.kakarote.finance.entity.PO.FinanceAccountUser;
import com.kakarote.finance.entity.PO.LocalUser;
import com.kakarote.finance.mapper.LocalUserMapper;
import com.kakarote.finance.service.IClientAccessService;
import com.kakarote.finance.service.IFinanceAccountSetService;
import com.kakarote.finance.service.IFinanceAccountUserService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Collections;
import java.util.List;
import java.util.Objects;
import java.util.stream.Collectors;

@Service
public class ClientAccessServiceImpl implements IClientAccessService {

    @Autowired
    private LocalUserMapper localUserMapper;

    @Autowired
    private IFinanceAccountSetService financeAccountSetService;

    @Autowired
    private IFinanceAccountUserService financeAccountUserService;

    @Override
    public LocalUser getCurrentUser() {
        Long userId = UserUtil.getUserId();
        if (userId == null && UserUtil.getUser() != null) {
            userId = UserUtil.getUser().getUserId();
        }
        if (userId == null) {
            throw new CrmException(SystemCodeEnum.SYSTEM_NOT_LOGIN);
        }
        return getUserRequired(userId);
    }

    @Override
    public LocalUser getUserRequired(Long userId) {
        LocalUser user = localUserMapper.selectById(userId);
        if (user == null || !Objects.equals(user.getStatus(), 1)) {
            throw new CrmException(SystemCodeEnum.SYSTEM_NO_AUTH);
        }
        return user;
    }

    @Override
    public boolean isPlatformSuperAdmin(LocalUser user) {
        return user != null
                && Boolean.TRUE.equals(user.getIsAdmin())
                && LocalUserTypeEnum.isPlatformSuperAdmin(user.getUserType());
    }

    @Override
    public boolean isClientAdmin(LocalUser user) {
        return user != null && Boolean.TRUE.equals(user.getIsClientAdmin());
    }

    @Override
    public Long resolveQueryClientId(Long requestedClientId) {
        LocalUser currentUser = getCurrentUser();
        if (isPlatformSuperAdmin(currentUser)) {
            return requestedClientId;
        }
        Long clientId = requireClientId(currentUser);
        if (requestedClientId != null && !Objects.equals(requestedClientId, clientId)) {
            throw new CrmException(SystemCodeEnum.SYSTEM_NO_AUTH);
        }
        return clientId;
    }

    @Override
    public Long requireClientId(LocalUser user) {
        if (user == null || user.getClientId() == null) {
            throw new CrmException(SystemCodeEnum.SYSTEM_NO_AUTH);
        }
        return user.getClientId();
    }

    @Override
    public void assertPlatformSuperAdmin() {
        if (!isPlatformSuperAdmin(getCurrentUser())) {
            throw new CrmException(SystemCodeEnum.SYSTEM_NO_AUTH);
        }
    }

    @Override
    public void assertClientAdminOrPlatformAdmin() {
        LocalUser user = getCurrentUser();
        if (!isPlatformSuperAdmin(user) && !isClientAdmin(user)) {
            throw new CrmException(SystemCodeEnum.SYSTEM_NO_AUTH);
        }
    }

    @Override
    public FinanceAccountSet assertAccountReadable(Long accountId) {
        LocalUser user = getCurrentUser();
        FinanceAccountSet accountSet = getAccountRequired(accountId);
        if (isPlatformSuperAdmin(user)) {
            return accountSet;
        }
        Long clientId = requireClientId(user);
        if (!Objects.equals(clientId, accountSet.getClientId())) {
            throw new CrmException(SystemCodeEnum.SYSTEM_NO_AUTH);
        }
        boolean exists = financeAccountUserService.lambdaQuery()
                .eq(FinanceAccountUser::getAccountId, accountId)
                .eq(FinanceAccountUser::getUserId, user.getUserId())
                .exists();
        if (!exists) {
            throw new CrmException(SystemCodeEnum.SYSTEM_NO_AUTH);
        }
        return accountSet;
    }

    @Override
    public FinanceAccountSet assertAccountManageable(Long accountId) {
        LocalUser user = getCurrentUser();
        FinanceAccountSet accountSet = getAccountRequired(accountId);
        if (isPlatformSuperAdmin(user)) {
            return accountSet;
        }
        Long clientId = requireClientId(user);
        if (!Objects.equals(clientId, accountSet.getClientId()) || !isClientAdmin(user)) {
            throw new CrmException(SystemCodeEnum.SYSTEM_NO_AUTH);
        }
        return accountSet;
    }

    @Override
    public List<Long> getReadableAccountIds(LocalUser user, Long clientId) {
        if (user == null) {
            return Collections.emptyList();
        }
        if (isPlatformSuperAdmin(user)) {
            LambdaQueryWrapper<FinanceAccountSet> wrapper = new LambdaQueryWrapper<>();
            wrapper.select(FinanceAccountSet::getAccountId)
                    .eq(clientId != null, FinanceAccountSet::getClientId, clientId)
                    .eq(FinanceAccountSet::getStatus, 1);
            return financeAccountSetService.list(wrapper).stream()
                    .map(FinanceAccountSet::getAccountId)
                    .collect(Collectors.toList());
        }
        Long scopedClientId = requireClientId(user);
        if (clientId != null && !Objects.equals(clientId, scopedClientId)) {
            throw new CrmException(SystemCodeEnum.SYSTEM_NO_AUTH);
        }
        List<FinanceAccountUser> relations = financeAccountUserService.lambdaQuery()
                .eq(FinanceAccountUser::getUserId, user.getUserId())
                .list();
        if (CollUtil.isEmpty(relations)) {
            return Collections.emptyList();
        }
        List<Long> accountIds = relations.stream().map(FinanceAccountUser::getAccountId).distinct().collect(Collectors.toList());
        return financeAccountSetService.lambdaQuery()
                .select(FinanceAccountSet::getAccountId)
                .in(FinanceAccountSet::getAccountId, accountIds)
                .eq(FinanceAccountSet::getClientId, scopedClientId)
                .eq(FinanceAccountSet::getStatus, 1)
                .list()
                .stream()
                .map(FinanceAccountSet::getAccountId)
                .collect(Collectors.toList());
    }

    private FinanceAccountSet getAccountRequired(Long accountId) {
        FinanceAccountSet accountSet = financeAccountSetService.getById(accountId);
        if (accountSet == null) {
            throw new CrmException(SystemCodeEnum.SYSTEM_NO_FOUND);
        }
        return accountSet;
    }
}
