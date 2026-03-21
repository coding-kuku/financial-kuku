package com.kakarote.finance.utils;

import com.kakarote.core.redis.Redis;
import com.kakarote.finance.entity.PO.LocalUser;
import com.kakarote.finance.mapper.LocalUserMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import javax.annotation.PostConstruct;

/**
 * 本地用户名查询工具，替换 com.kakarote.ids.provider.utils.UserCacheUtil
 */
@Component
public class LocalUserCacheUtil {

    private static LocalUserCacheUtil ME;

    @Autowired
    private Redis redis;

    @Autowired
    private LocalUserMapper localUserMapper;

    @PostConstruct
    public void init() {
        ME = this;
    }

    private static final String CACHE_PREFIX = "LOCAL:USER:REALNAME:";
    private static final int CACHE_SECONDS = 3600;

    public static String getUserName(Long userId) {
        if (userId == null) {
            return "";
        }
        String cacheKey = CACHE_PREFIX + userId;
        String cached = ME.redis.get(cacheKey);
        if (cached != null) {
            return cached;
        }
        LocalUser user = ME.localUserMapper.selectById(userId);
        if (user != null) {
            String name = user.getRealname() != null ? user.getRealname() : user.getUsername();
            ME.redis.setex(cacheKey, CACHE_SECONDS, name);
            return name;
        }
        return "";
    }

    /**
     * 登录时主动写入缓存，避免第一次查询走 DB
     */
    public static void cacheUserName(Long userId, String realname) {
        if (userId != null && realname != null) {
            ME.redis.setex(CACHE_PREFIX + userId, CACHE_SECONDS, realname);
        }
    }
}
