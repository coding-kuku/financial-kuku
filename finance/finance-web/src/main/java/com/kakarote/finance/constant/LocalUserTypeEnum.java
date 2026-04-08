package com.kakarote.finance.constant;

public enum LocalUserTypeEnum {
    PLATFORM_SUPER_ADMIN("platform_super_admin"),
    CLIENT_USER("client_user");

    private final String value;

    LocalUserTypeEnum(String value) {
        this.value = value;
    }

    public String getValue() {
        return value;
    }

    public static boolean isPlatformSuperAdmin(String value) {
        return PLATFORM_SUPER_ADMIN.value.equals(value);
    }
}
