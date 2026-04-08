package com.kakarote.finance.service;

import com.alibaba.fastjson.JSONObject;
import com.kakarote.finance.entity.PO.LocalUser;

public interface IPlatformPermissionService {

    JSONObject buildManageAuth(LocalUser user);
}
