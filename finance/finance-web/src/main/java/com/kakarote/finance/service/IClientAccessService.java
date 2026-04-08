package com.kakarote.finance.service;

import com.kakarote.finance.entity.PO.FinanceAccountSet;
import com.kakarote.finance.entity.PO.LocalUser;

import java.util.List;

public interface IClientAccessService {

    LocalUser getCurrentUser();

    LocalUser getUserRequired(Long userId);

    boolean isPlatformSuperAdmin(LocalUser user);

    boolean isClientAdmin(LocalUser user);

    Long resolveQueryClientId(Long requestedClientId);

    Long requireClientId(LocalUser user);

    void assertPlatformSuperAdmin();

    void assertClientAdminOrPlatformAdmin();

    FinanceAccountSet assertAccountReadable(Long accountId);

    FinanceAccountSet assertAccountManageable(Long accountId);

    List<Long> getReadableAccountIds(LocalUser user, Long clientId);
}
