package com.kakarote.finance.service.impl;

import cn.hutool.core.util.StrUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.kakarote.common.utils.UserUtil;
import com.kakarote.core.common.enums.SystemCodeEnum;
import com.kakarote.core.exception.CrmException;
import com.kakarote.finance.constant.LocalUserTypeEnum;
import com.kakarote.finance.entity.BO.*;
import com.kakarote.finance.entity.PO.ClientCompany;
import com.kakarote.finance.entity.PO.LocalUser;
import com.kakarote.finance.entity.VO.ClientUserVO;
import com.kakarote.finance.mapper.LocalUserMapper;
import com.kakarote.finance.service.IClientAccessService;
import com.kakarote.finance.service.IClientCompanyService;
import com.kakarote.finance.service.IClientUserService;
import com.kakarote.finance.utils.LocalPasswordUtil;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class ClientUserServiceImpl implements IClientUserService {

    @Autowired
    private LocalUserMapper localUserMapper;

    @Autowired
    private IClientAccessService clientAccessService;

    @Autowired
    private IClientCompanyService clientCompanyService;

    @Override
    public List<ClientUserVO> queryList(ClientUserQueryBO queryBO) {
        Long clientId = clientAccessService.resolveQueryClientId(queryBO != null ? queryBO.getClientId() : null);
        LambdaQueryWrapper<LocalUser> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(clientId != null, LocalUser::getClientId, clientId)
                .ne(LocalUser::getUserType, LocalUserTypeEnum.PLATFORM_SUPER_ADMIN.getValue())
                .eq(queryBO != null && queryBO.getStatus() != null, LocalUser::getStatus, queryBO.getStatus())
                .and(queryBO != null && StrUtil.isNotBlank(queryBO.getKeyword()), w ->
                        w.like(LocalUser::getUsername, queryBO.getKeyword())
                                .or()
                                .like(LocalUser::getRealname, queryBO.getKeyword())
                                .or()
                                .like(LocalUser::getPhone, queryBO.getKeyword()))
                .orderByDesc(LocalUser::getCreateTime);
        return localUserMapper.selectList(wrapper).stream()
                .map(this::toVO)
                .collect(Collectors.toList());
    }

    @Override
    public List<ClientUserVO> querySelectableList(Long clientId) {
        Long scopedClientId = clientAccessService.resolveQueryClientId(clientId);
        if (scopedClientId == null) {
            return java.util.Collections.emptyList();
        }
        return localUserMapper.selectList(new LambdaQueryWrapper<LocalUser>()
                        .eq(LocalUser::getClientId, scopedClientId)
                        .eq(LocalUser::getStatus, 1)
                        .eq(LocalUser::getUserType, LocalUserTypeEnum.CLIENT_USER.getValue())
                        .orderByAsc(LocalUser::getRealname))
                .stream()
                .map(this::toVO)
                .collect(Collectors.toList());
    }

    @Override
    public ClientUserVO save(ClientUserSaveBO saveBO) {
        Long clientId = resolveWritableClientId(saveBO.getClientId());
        validateSaveBO(saveBO, false);
        ensureCompanyActive(clientId);
        assertUsernameUnique(saveBO.getUsername(), null);
        LocalUser user = new LocalUser();
        user.setClientId(clientId);
        user.setUsername(saveBO.getUsername());
        user.setRealname(saveBO.getRealname());
        user.setPhone(saveBO.getPhone());
        user.setStatus(saveBO.getStatus() == null ? 1 : saveBO.getStatus());
        user.setIsAdmin(false);
        user.setUserType(LocalUserTypeEnum.CLIENT_USER.getValue());
        user.setIsClientAdmin(Boolean.TRUE.equals(saveBO.getIsClientAdmin()));
        user.setCreateTime(LocalDateTime.now());
        LocalPasswordUtil.resetPassword(user, saveBO.getPassword());
        localUserMapper.insert(user);
        return toVO(user);
    }

    @Override
    public ClientUserVO update(ClientUserSaveBO saveBO) {
        validateSaveBO(saveBO, true);
        LocalUser currentUser = clientAccessService.getCurrentUser();
        LocalUser user = clientAccessService.getUserRequired(saveBO.getUserId());
        Long scopedClientId = resolveWritableClientId(user.getClientId());
        if (!clientAccessService.isPlatformSuperAdmin(currentUser) && currentUser.getUserId().equals(user.getUserId()) && Boolean.FALSE.equals(saveBO.getIsClientAdmin())) {
            throw new CrmException(400, "不能取消自己的客户管理员身份");
        }
        assertUsernameUnique(saveBO.getUsername(), user.getUserId());
        user.setRealname(saveBO.getRealname());
        user.setPhone(saveBO.getPhone());
        user.setStatus(saveBO.getStatus() == null ? user.getStatus() : saveBO.getStatus());
        user.setIsClientAdmin(Boolean.TRUE.equals(saveBO.getIsClientAdmin()));
        if (clientAccessService.isPlatformSuperAdmin(currentUser) && saveBO.getClientId() != null && !saveBO.getClientId().equals(scopedClientId)) {
            ensureCompanyActive(saveBO.getClientId());
            user.setClientId(saveBO.getClientId());
        }
        localUserMapper.updateById(user);
        return toVO(user);
    }

    @Override
    public void updateStatus(ClientUserStatusBO statusBO) {
        LocalUser target = clientAccessService.getUserRequired(statusBO.getUserId());
        resolveWritableClientId(target.getClientId());
        LocalUser currentUser = clientAccessService.getCurrentUser();
        if (currentUser.getUserId().equals(target.getUserId()) && !Integer.valueOf(1).equals(statusBO.getStatus())) {
            throw new CrmException(400, "不能停用当前登录用户");
        }
        target.setStatus(statusBO.getStatus());
        localUserMapper.updateById(target);
    }

    @Override
    public void updateAdminStatus(ClientUserAdminStatusBO statusBO) {
        LocalUser target = clientAccessService.getUserRequired(statusBO.getUserId());
        resolveWritableClientId(target.getClientId());
        LocalUser currentUser = clientAccessService.getCurrentUser();
        if (currentUser.getUserId().equals(target.getUserId()) && !Boolean.TRUE.equals(statusBO.getIsClientAdmin())) {
            throw new CrmException(400, "不能取消当前登录用户的客户管理员身份");
        }
        target.setIsClientAdmin(Boolean.TRUE.equals(statusBO.getIsClientAdmin()));
        localUserMapper.updateById(target);
    }

    @Override
    public void resetPassword(ClientUserResetPasswordBO resetPasswordBO) {
        if (resetPasswordBO == null || resetPasswordBO.getUserId() == null || StrUtil.isBlank(resetPasswordBO.getPassword())) {
            throw new CrmException(SystemCodeEnum.SYSTEM_NO_VALID);
        }
        LocalUser target = clientAccessService.getUserRequired(resetPasswordBO.getUserId());
        resolveWritableClientId(target.getClientId());
        LocalPasswordUtil.resetPassword(target, resetPasswordBO.getPassword());
        localUserMapper.updateById(target);
    }

    @Override
    public void updateSelfPassword(SelfPasswordUpdateBO updateBO) {
        if (updateBO == null || StrUtil.isBlank(updateBO.getOldPassword()) || StrUtil.isBlank(updateBO.getNewPassword())) {
            throw new CrmException(SystemCodeEnum.SYSTEM_NO_VALID);
        }
        LocalUser currentUser = clientAccessService.getCurrentUser();
        if (!LocalPasswordUtil.matches(currentUser, updateBO.getOldPassword())) {
            throw new CrmException(400, "旧密码错误");
        }
        LocalPasswordUtil.resetPassword(currentUser, updateBO.getNewPassword());
        localUserMapper.updateById(currentUser);
    }

    private Long resolveWritableClientId(Long requestedClientId) {
        LocalUser currentUser = clientAccessService.getCurrentUser();
        if (clientAccessService.isPlatformSuperAdmin(currentUser)) {
            if (requestedClientId == null) {
                throw new CrmException(400, "请选择客户公司");
            }
            return requestedClientId;
        }
        if (!clientAccessService.isClientAdmin(currentUser)) {
            throw new CrmException(SystemCodeEnum.SYSTEM_NO_AUTH);
        }
        Long clientId = clientAccessService.requireClientId(currentUser);
        if (requestedClientId != null && !requestedClientId.equals(clientId)) {
            throw new CrmException(SystemCodeEnum.SYSTEM_NO_AUTH);
        }
        return clientId;
    }

    private void validateSaveBO(ClientUserSaveBO saveBO, boolean requireId) {
        if (saveBO == null) {
            throw new CrmException(SystemCodeEnum.SYSTEM_NO_VALID);
        }
        if (requireId && saveBO.getUserId() == null) {
            throw new CrmException(SystemCodeEnum.SYSTEM_NO_VALID);
        }
        if (StrUtil.isBlank(saveBO.getUsername()) || StrUtil.isBlank(saveBO.getRealname())) {
            throw new CrmException(400, "账号和姓名不能为空");
        }
        if (!requireId && StrUtil.isBlank(saveBO.getPassword())) {
            throw new CrmException(400, "初始密码不能为空");
        }
    }

    private void assertUsernameUnique(String username, Long excludeUserId) {
        LambdaQueryWrapper<LocalUser> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(LocalUser::getUsername, username)
                .ne(excludeUserId != null, LocalUser::getUserId, excludeUserId);
        if (localUserMapper.selectCount(wrapper) > 0) {
            throw new CrmException(400, "登录账号已存在");
        }
    }

    private void ensureCompanyActive(Long clientId) {
        ClientCompany company = clientCompanyService.getById(clientId);
        if (!Integer.valueOf(1).equals(company.getStatus())) {
            throw new CrmException(400, "客户公司已停用");
        }
    }

    private ClientUserVO toVO(LocalUser user) {
        ClientUserVO vo = new ClientUserVO();
        vo.setUserId(user.getUserId());
        vo.setClientId(user.getClientId());
        vo.setUsername(user.getUsername());
        vo.setRealname(user.getRealname());
        vo.setPhone(user.getPhone());
        vo.setStatus(user.getStatus());
        vo.setIsAdmin(user.getIsAdmin());
        vo.setIsClientAdmin(user.getIsClientAdmin());
        vo.setUserType(user.getUserType());
        if (user.getClientId() != null) {
            try {
                vo.setClientName(clientCompanyService.getById(user.getClientId()).getClientName());
            } catch (Exception ignored) {
            }
        }
        return vo;
    }
}
