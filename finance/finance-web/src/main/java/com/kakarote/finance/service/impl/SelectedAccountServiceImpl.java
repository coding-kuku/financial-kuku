package com.kakarote.finance.service.impl;

import com.kakarote.core.redis.Redis;
import com.kakarote.finance.service.ISelectedAccountService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class SelectedAccountServiceImpl implements ISelectedAccountService {

    private static final String KEY_PREFIX = "LOCAL:FINANCE:SELECTED_ACCOUNT:";
    private static final int EXPIRE_SECONDS = 30 * 24 * 60 * 60;

    @Autowired
    private Redis redis;

    @Override
    public Long getSelectedAccountId(Long userId) {
        if (userId == null) {
            return null;
        }
        Object value = redis.get(KEY_PREFIX + userId);
        if (value instanceof Number) {
            return ((Number) value).longValue();
        }
        if (value instanceof String) {
            try {
                return Long.valueOf((String) value);
            } catch (NumberFormatException ignored) {
            }
        }
        return null;
    }

    @Override
    public void setSelectedAccountId(Long userId, Long accountId) {
        if (userId != null && accountId != null) {
            redis.setex(KEY_PREFIX + userId, EXPIRE_SECONDS, accountId);
        }
    }

    @Override
    public void clearSelectedAccountId(Long userId) {
        if (userId != null) {
            redis.del(KEY_PREFIX + userId);
        }
    }
}
