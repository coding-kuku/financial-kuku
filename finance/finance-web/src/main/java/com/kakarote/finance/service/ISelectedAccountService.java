package com.kakarote.finance.service;

public interface ISelectedAccountService {

    Long getSelectedAccountId(Long userId);

    void setSelectedAccountId(Long userId, Long accountId);

    void clearSelectedAccountId(Long userId);
}
