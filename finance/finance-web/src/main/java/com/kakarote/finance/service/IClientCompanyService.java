package com.kakarote.finance.service;

import com.kakarote.finance.entity.BO.ClientCompanyQueryBO;
import com.kakarote.finance.entity.BO.ClientCompanySaveBO;
import com.kakarote.finance.entity.PO.ClientCompany;
import com.kakarote.finance.entity.VO.ClientCompanySimpleVO;

import java.util.List;

public interface IClientCompanyService {

    List<ClientCompany> queryList(ClientCompanyQueryBO queryBO);

    List<ClientCompanySimpleVO> querySelectableList();

    ClientCompany save(ClientCompanySaveBO saveBO);

    ClientCompany update(ClientCompanySaveBO saveBO);

    void updateStatus(Long clientId, Integer status);

    ClientCompany getById(Long clientId);
}
