package com.kakarote.finance.service;

import com.kakarote.finance.entity.BO.*;
import com.kakarote.finance.entity.VO.ClientUserVO;

import java.util.List;

public interface IClientUserService {

    List<ClientUserVO> queryList(ClientUserQueryBO queryBO);

    List<ClientUserVO> querySelectableList(Long clientId);

    ClientUserVO save(ClientUserSaveBO saveBO);

    ClientUserVO update(ClientUserSaveBO saveBO);

    void updateStatus(ClientUserStatusBO statusBO);

    void updateAdminStatus(ClientUserAdminStatusBO statusBO);

    void resetPassword(ClientUserResetPasswordBO resetPasswordBO);

    void updateSelfPassword(SelfPasswordUpdateBO updateBO);
}
