package com.kakarote.finance.service.impl;

import com.alibaba.fastjson.JSONObject;
import com.kakarote.finance.entity.PO.LocalUser;
import com.kakarote.finance.service.IPlatformPermissionService;
import org.springframework.stereotype.Service;

@Service
public class PlatformPermissionServiceImpl implements IPlatformPermissionService {

    @Override
    public JSONObject buildManageAuth(LocalUser user) {
        JSONObject root = new JSONObject();
        if (user == null) {
            return root;
        }

        JSONObject manage = new JSONObject();
        if (Boolean.TRUE.equals(user.getIsAdmin())) {
            JSONObject finance = new JSONObject();
            finance.put("accountSet", true);
            manage.put("finance", finance);
            manage.put("clientCompany", true);
            manage.put("clientUser", true);
        } else if (Boolean.TRUE.equals(user.getIsClientAdmin())) {
            JSONObject finance = new JSONObject();
            finance.put("accountSet", true);
            manage.put("finance", finance);
            manage.put("clientUser", true);
        }

        root.put("manage", manage);
        return root;
    }
}
