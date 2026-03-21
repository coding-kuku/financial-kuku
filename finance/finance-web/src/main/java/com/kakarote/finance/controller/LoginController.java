package com.kakarote.finance.controller;

import cn.hutool.core.util.IdUtil;
import cn.hutool.crypto.digest.DigestUtil;
import com.alibaba.fastjson.JSONObject;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.kakarote.common.entity.UserInfo;
import com.kakarote.common.utils.UserUtil;
import com.kakarote.core.common.Const;
import com.kakarote.core.common.Result;
import com.kakarote.core.redis.Redis;
import com.kakarote.finance.entity.PO.LocalUser;
import com.kakarote.finance.mapper.LocalUserMapper;
import com.kakarote.finance.utils.LocalUserCacheUtil;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import javax.servlet.http.HttpServletRequest;
import java.util.Collections;

/**
 * 本地登录控制器，替换 provider-1.0.1.jar 中的 OAuthController
 */
@RestController
@Api(tags = "登录模块")
public class LoginController {

    @Autowired
    private LocalUserMapper localUserMapper;

    @Autowired
    private Redis redis;

    /**
     * 前端 /login 接口：用户名密码登录，返回 token
     */
    @PostMapping("/login")
    @ApiOperation("用户名密码登录")
    public Result<String> login(@RequestBody JSONObject body) {
        String username = body.getString("username");
        String password = body.getString("password");
        if (username == null || password == null) {
            return Result.error(400, "用户名和密码不能为空");
        }
        LocalUser user = localUserMapper.selectOne(
                new LambdaQueryWrapper<LocalUser>()
                        .eq(LocalUser::getUsername, username)
                        .eq(LocalUser::getStatus, 1)
        );
        if (user == null) {
            return Result.error(400, "用户名或密码错误");
        }
        String hash = DigestUtil.sha256Hex(password + user.getSalt());
        if (!hash.equals(user.getPassword())) {
            return Result.error(400, "用户名或密码错误");
        }

        String token = IdUtil.simpleUUID();
        UserInfo userInfo = new UserInfo();
        userInfo.setUserId(user.getUserId());
        userInfo.setUsername(user.getUsername());
        userInfo.setNickname(user.getRealname() != null ? user.getRealname() : user.getUsername());
        userInfo.setAdmin(Boolean.TRUE.equals(user.getIsAdmin()));

        int expireSeconds = Const.MAX_USER_EXIST_TIME;
        redis.setex(token, expireSeconds, userInfo);
        redis.setex(token + Const.TOKEN_CACHE_NAME, expireSeconds, "1");
        LocalUserCacheUtil.cacheUserName(user.getUserId(), userInfo.getNickname());

        return Result.ok(token);
    }

    /**
     * 前端 /adminUser/logout 接口：使 token 失效
     */
    @PostMapping("/adminUser/logout")
    @ApiOperation("退出登录")
    public Result logout(HttpServletRequest request) {
        String token = request.getHeader(Const.DEFAULT_TOKEN_NAME);
        if (token != null && !token.isEmpty()) {
            redis.del(token, token + Const.TOKEN_CACHE_NAME);
        }
        return Result.ok();
    }

    /**
     * 前端 adminUser/queryLoginUser 接口：返回当前登录用户信息
     */
    @PostMapping("/adminUser/queryLoginUser")
    @ApiOperation("获取当前登录用户信息")
    public Result<JSONObject> queryLoginUser() {
        UserInfo user = UserUtil.getUser();
        JSONObject result = new JSONObject();
        if (user != null && user.getUserId() != null) {
            result.put("userId", user.getUserId());
            result.put("username", user.getUsername());
            result.put("nickname", user.getNickname());
            result.put("realname", user.getNickname());
            result.put("isAdmin", user.isAdmin());
        }
        return Result.ok(result);
    }

    @PostMapping("/adminUser/queryUserList")
    @ApiOperation("查询用户列表（本地兼容实现）")
    public Result<JSONObject> queryUserList() {
        UserInfo user = UserUtil.getUser();
        JSONObject item = new JSONObject();
        item.put("userId", user != null ? user.getUserId() : 1L);
        item.put("username", user != null ? user.getUsername() : "admin");
        item.put("realname", user != null ? user.getNickname() : "管理员");
        item.put("nickname", user != null ? user.getNickname() : "管理员");
        item.put("deptId", 1L);
        item.put("status", 1);
        JSONObject result = new JSONObject();
        result.put("list", Collections.singletonList(item));
        return Result.ok(result);
    }

    @PostMapping("/adminUser/queryDeptTree")
    @ApiOperation("查询部门树（本地兼容实现）")
    public Result<Object> queryDeptTree() {
        JSONObject dept = new JSONObject();
        dept.put("deptId", 1L);
        dept.put("name", "默认部门");
        dept.put("children", Collections.emptyList());
        return Result.ok(Collections.singletonList(dept));
    }

    @PostMapping("/adminUser/queryOrganizationInfo")
    @ApiOperation("查询组织架构信息（本地兼容实现）")
    public Result<JSONObject> queryOrganizationInfo() {
        UserInfo user = UserUtil.getUser();
        JSONObject userItem = new JSONObject();
        userItem.put("userId", user != null ? user.getUserId() : 1L);
        userItem.put("username", user != null ? user.getUsername() : "admin");
        userItem.put("realname", user != null ? user.getNickname() : "管理员");
        userItem.put("nickname", user != null ? user.getNickname() : "管理员");
        userItem.put("deptId", 1L);
        userItem.put("status", 1);

        JSONObject dept = new JSONObject();
        dept.put("deptId", 1L);
        dept.put("name", "默认部门");
        dept.put("children", Collections.emptyList());

        JSONObject userMap = new JSONObject();
        userMap.put("1", Collections.singletonList(userItem));

        JSONObject result = new JSONObject();
        result.put("deptList", Collections.singletonList(dept));
        result.put("userMap", userMap);
        result.put("disableUserList", Collections.emptyList());
        return Result.ok(result);
    }

    /**
     * 前端 /adminUser/authorization 接口：本地模式不使用 OAuth2 code 换 token。
     * 此接口仅作兼容存根，不实际处理。
     */
    @PostMapping("/adminUser/authorization")
    @ApiOperation("OAuth2 回调（本地模式不支持）")
    public Result authorization(@RequestBody(required = false) JSONObject body) {
        return Result.error(302, "本地部署模式不支持 OAuth2，请通过本地登录页登录");
    }
}
