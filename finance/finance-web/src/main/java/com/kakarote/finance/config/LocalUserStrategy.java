package com.kakarote.finance.config;

import com.kakarote.common.entity.UserInfo;
import com.kakarote.common.servlet.UserStrategy;
import com.kakarote.common.utils.UserUtil;
import org.springframework.stereotype.Component;

import javax.annotation.PostConstruct;

/**
 * 本地单机部署的 UserStrategy 实现。
 * 将用户信息存入 ThreadLocal，使 UserUtil.setUser/getUser 在本地模式下正常工作。
 * 原微服务架构中此接口由 provider 服务注入，单机部署时需自行实现。
 */
@Component
public class LocalUserStrategy implements UserStrategy {

    private static final ThreadLocal<UserInfo> USER_HOLDER = new ThreadLocal<>();

    @PostConstruct
    public void init() {
        // 注册自身到 UserUtil，使所有代码的 UserUtil.setUser/getUser 生效
        UserUtil.setUserStrategy(this);
    }

    @Override
    public UserInfo getUser() {
        return USER_HOLDER.get();
    }

    @Override
    public void setUser(UserInfo userInfo) {
        USER_HOLDER.set(userInfo);
    }

    @Override
    public void setUser(Long userId) {
        UserInfo info = new UserInfo();
        info.setUserId(userId);
        USER_HOLDER.set(info);
    }

    @Override
    public void removeUser() {
        USER_HOLDER.remove();
    }
}
