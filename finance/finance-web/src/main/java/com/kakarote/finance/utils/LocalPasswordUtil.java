package com.kakarote.finance.utils;

import cn.hutool.core.util.IdUtil;
import cn.hutool.crypto.digest.DigestUtil;
import com.kakarote.finance.entity.PO.LocalUser;

public final class LocalPasswordUtil {

    private LocalPasswordUtil() {
    }

    public static String generateSalt() {
        return IdUtil.simpleUUID();
    }

    public static String hashPassword(String password, String salt) {
        return DigestUtil.sha256Hex(password + salt);
    }

    public static void resetPassword(LocalUser user, String password) {
        String salt = generateSalt();
        user.setSalt(salt);
        user.setPassword(hashPassword(password, salt));
    }

    public static boolean matches(LocalUser user, String rawPassword) {
        if (user == null || user.getSalt() == null || user.getPassword() == null) {
            return false;
        }
        return user.getPassword().equals(hashPassword(rawPassword, user.getSalt()));
    }
}
