package com.kakarote.finance.service.impl;

import cn.hutool.core.util.ObjectUtil;
import cn.hutool.core.util.StrUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.kakarote.common.utils.UserUtil;
import com.kakarote.core.common.enums.SystemCodeEnum;
import com.kakarote.core.exception.CrmException;
import com.kakarote.finance.entity.BO.ClientCompanyQueryBO;
import com.kakarote.finance.entity.BO.ClientCompanySaveBO;
import com.kakarote.finance.entity.PO.ClientCompany;
import com.kakarote.finance.entity.VO.ClientCompanySimpleVO;
import com.kakarote.finance.mapper.ClientCompanyMapper;
import com.kakarote.finance.service.IClientAccessService;
import com.kakarote.finance.service.IClientCompanyService;
import org.springframework.beans.BeanUtils;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Service
public class ClientCompanyServiceImpl implements IClientCompanyService {

    @Autowired
    private ClientCompanyMapper clientCompanyMapper;

    @Autowired
    private IClientAccessService clientAccessService;

    @Override
    public List<ClientCompany> queryList(ClientCompanyQueryBO queryBO) {
        clientAccessService.assertPlatformSuperAdmin();
        LambdaQueryWrapper<ClientCompany> wrapper = new LambdaQueryWrapper<>();
        if (queryBO != null) {
            wrapper.like(StrUtil.isNotBlank(queryBO.getKeyword()), ClientCompany::getClientName, queryBO.getKeyword())
                    .or(StrUtil.isNotBlank(queryBO.getKeyword()))
                    .like(StrUtil.isNotBlank(queryBO.getKeyword()), ClientCompany::getClientCode, queryBO.getKeyword())
                    .eq(queryBO.getStatus() != null, ClientCompany::getStatus, queryBO.getStatus());
        }
        wrapper.orderByDesc(ClientCompany::getCreateTime);
        return clientCompanyMapper.selectList(wrapper);
    }

    @Override
    public List<ClientCompanySimpleVO> querySelectableList() {
        LambdaQueryWrapper<ClientCompany> wrapper = new LambdaQueryWrapper<>();
        wrapper.eq(ClientCompany::getStatus, 1)
                .orderByAsc(ClientCompany::getClientName);
        return clientCompanyMapper.selectList(wrapper).stream().map(company -> {
            ClientCompanySimpleVO vo = new ClientCompanySimpleVO();
            vo.setClientId(company.getClientId());
            vo.setClientName(company.getClientName());
            return vo;
        }).collect(Collectors.toList());
    }

    @Override
    public ClientCompany save(ClientCompanySaveBO saveBO) {
        clientAccessService.assertPlatformSuperAdmin();
        validateSaveBO(saveBO, false);
        if (existsByNameOrCode(saveBO, null)) {
            throw new CrmException(400, "客户公司名称或编码已存在");
        }
        ClientCompany company = new ClientCompany();
        BeanUtils.copyProperties(saveBO, company);
        if (company.getStatus() == null) {
            company.setStatus(1);
        }
        company.setCreateUserId(UserUtil.getUserId());
        clientCompanyMapper.insert(company);
        return company;
    }

    @Override
    public ClientCompany update(ClientCompanySaveBO saveBO) {
        clientAccessService.assertPlatformSuperAdmin();
        validateSaveBO(saveBO, true);
        ClientCompany company = getById(saveBO.getClientId());
        if (existsByNameOrCode(saveBO, company.getClientId())) {
            throw new CrmException(400, "客户公司名称或编码已存在");
        }
        company.setClientName(saveBO.getClientName());
        company.setClientCode(saveBO.getClientCode());
        company.setContactName(saveBO.getContactName());
        company.setContactPhone(saveBO.getContactPhone());
        company.setRemark(saveBO.getRemark());
        if (saveBO.getStatus() != null) {
            company.setStatus(saveBO.getStatus());
        }
        company.setUpdateUserId(UserUtil.getUserId());
        clientCompanyMapper.updateById(company);
        return company;
    }

    @Override
    public void updateStatus(Long clientId, Integer status) {
        clientAccessService.assertPlatformSuperAdmin();
        ClientCompany company = getById(clientId);
        company.setStatus(status);
        company.setUpdateUserId(UserUtil.getUserId());
        clientCompanyMapper.updateById(company);
    }

    @Override
    public ClientCompany getById(Long clientId) {
        ClientCompany company = clientCompanyMapper.selectById(clientId);
        if (company == null) {
            throw new CrmException(SystemCodeEnum.SYSTEM_NO_FOUND);
        }
        return company;
    }

    private boolean existsByNameOrCode(ClientCompanySaveBO saveBO, Long excludeId) {
        LambdaQueryWrapper<ClientCompany> nameWrapper = new LambdaQueryWrapper<>();
        nameWrapper.eq(ClientCompany::getClientName, saveBO.getClientName())
                .ne(excludeId != null, ClientCompany::getClientId, excludeId);
        if (clientCompanyMapper.selectCount(nameWrapper) > 0) {
            return true;
        }
        if (StrUtil.isBlank(saveBO.getClientCode())) {
            return false;
        }
        LambdaQueryWrapper<ClientCompany> codeWrapper = new LambdaQueryWrapper<>();
        codeWrapper.eq(ClientCompany::getClientCode, saveBO.getClientCode())
                .ne(excludeId != null, ClientCompany::getClientId, excludeId);
        return clientCompanyMapper.selectCount(codeWrapper) > 0;
    }

    private void validateSaveBO(ClientCompanySaveBO saveBO, boolean requireId) {
        if (saveBO == null) {
            throw new CrmException(SystemCodeEnum.SYSTEM_NO_VALID);
        }
        if (requireId && saveBO.getClientId() == null) {
            throw new CrmException(SystemCodeEnum.SYSTEM_NO_VALID);
        }
        if (StrUtil.isBlank(saveBO.getClientName())) {
            throw new CrmException(400, "客户公司名称不能为空");
        }
        if (ObjectUtil.isEmpty(saveBO.getStatus())) {
            saveBO.setStatus(1);
        }
    }
}
