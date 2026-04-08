package com.kakarote.finance.controller;

import cn.hutool.core.util.IdUtil;
import com.alibaba.fastjson.JSONObject;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.kakarote.common.entity.UserInfo;
import com.kakarote.common.servlet.UserStrategy;
import com.kakarote.common.utils.UserUtil;
import com.kakarote.core.common.Const;
import com.kakarote.core.common.Result;
import com.kakarote.core.redis.Redis;
import com.kakarote.core.servlet.ApplicationContextHolder;
import com.kakarote.finance.entity.PO.LocalUser;
import com.kakarote.finance.entity.VO.ClientUserVO;
import com.kakarote.finance.mapper.LocalUserMapper;
import com.kakarote.finance.service.IClientCompanyService;
import com.kakarote.finance.service.IClientUserService;
import com.kakarote.finance.service.ISelectedAccountService;
import com.kakarote.finance.utils.LocalUserCacheUtil;
import com.kakarote.finance.utils.LocalPasswordUtil;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RestController;

import javax.servlet.http.HttpServletRequest;
import java.time.LocalDateTime;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 本地登录控制器，替换 provider-1.0.1.jar 中的 OAuthController
 */
@Slf4j
@RestController
@Api(tags = "登录模块")
public class LoginController {

    private static final String SMS_KEY_PREFIX = "send:sms:";
    private static final int SMS_TTL = 300; // 5 minutes

    @Autowired
    private LocalUserMapper localUserMapper;

    @Autowired
    private Redis redis;

    @Autowired
    private IClientCompanyService clientCompanyService;

    @Autowired
    private IClientUserService clientUserService;

    @Autowired
    private ISelectedAccountService selectedAccountService;

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
        if (!LocalPasswordUtil.matches(user, password)) {
            return Result.error(400, "用户名或密码错误");
        }
        return Result.ok(issueToken(user));
    }

    /**
     * 前端 /adminUser/logout 接口：使 token 失效
     */
    @PostMapping("/adminUser/logout")
    @ApiOperation("退出登录")
    public Result logout(HttpServletRequest request) {
        UserInfo currentUser = resolveCurrentUser();
        String token = request.getHeader(Const.DEFAULT_TOKEN_NAME);
        if (token != null && !token.isEmpty()) {
            redis.del(token, token + Const.TOKEN_CACHE_NAME);
        }
        if (currentUser != null) {
            selectedAccountService.clearSelectedAccountId(currentUser.getUserId());
        }
        return Result.ok();
    }

    private UserInfo buildUserInfo(LocalUser user) {
        UserInfo userInfo = new UserInfo();
        String realname = user.getRealname() != null ? user.getRealname() : user.getUsername();
        userInfo.setUserId(user.getUserId());
        userInfo.setUsername(user.getUsername());
        userInfo.setNickname(realname);
        userInfo.setAdmin(Boolean.TRUE.equals(user.getIsAdmin()));
        return userInfo;
    }

    private UserInfo resolveCurrentUser() {
        UserInfo user = UserUtil.getUser();
        if (user != null && user.getUserId() != null) {
            return user;
        }
        HttpServletRequest request = ((org.springframework.web.context.request.ServletRequestAttributes) org.springframework.web.context.request.RequestContextHolder.currentRequestAttributes()).getRequest();
        String token = request.getHeader(Const.DEFAULT_TOKEN_NAME);
        if (token == null || token.isEmpty() || !redis.exists(token + Const.TOKEN_CACHE_NAME)) {
            return null;
        }
        Object sessionValue = redis.get(token);
        if (!(sessionValue instanceof UserInfo)) {
            return null;
        }
        UserInfo sessionUser = (UserInfo) sessionValue;
        if (sessionUser.getUserId() == null) {
            return null;
        }
        tryBindUserStrategy();
        UserUtil.setUser(sessionUser);
        return sessionUser;
    }

    private void tryBindUserStrategy() {
        try {
            UserStrategy userStrategy = ApplicationContextHolder.getBean(UserStrategy.class);
            if (userStrategy != null) {
                UserUtil userUtil = ApplicationContextHolder.getBean(UserUtil.class);
                if (userUtil != null) {
                    userUtil.setUserStrategy(userStrategy);
                }
            }
        } catch (Exception ignored) {
        }
    }

    /**
     * 前端 adminUser/queryLoginUser 接口：返回当前登录用户信息
     */
    @PostMapping("/adminUser/queryLoginUser")
    @ApiOperation("获取当前登录用户信息")
    public Result<JSONObject> queryLoginUser(HttpServletRequest request) {
        UserInfo user = resolveCurrentUser();
        JSONObject result = new JSONObject();
        if (user != null && user.getUserId() != null) {
            LocalUser localUser = localUserMapper.selectById(user.getUserId());
            result.put("userId", user.getUserId());
            result.put("username", user.getUsername());
            result.put("nickname", user.getNickname());
            result.put("realname", user.getNickname());
            result.put("isAdmin", user.isAdmin());
            if (localUser != null) {
                result.put("phone", localUser.getPhone());
                result.put("userType", localUser.getUserType());
                result.put("clientId", localUser.getClientId());
                result.put("isClientAdmin", Boolean.TRUE.equals(localUser.getIsClientAdmin()));
                if (localUser.getClientId() != null) {
                    try {
                        result.put("clientName", clientCompanyService.getById(localUser.getClientId()).getClientName());
                    } catch (Exception ignored) {
                    }
                }
            }
        }
        return Result.ok(result);
    }

    @PostMapping("/adminUser/queryUserList")
    @ApiOperation("查询用户列表（本地兼容实现）")
    public Result<JSONObject> queryUserList() {
        LocalUser currentUser = getCurrentLocalUser();
        List<ClientUserVO> users = clientUserService.querySelectableList(currentUser != null ? currentUser.getClientId() : null);
        List<JSONObject> items = users.stream().map(user -> {
            JSONObject item = new JSONObject();
            item.put("userId", user.getUserId());
            item.put("username", user.getUsername());
            item.put("realname", user.getRealname());
            item.put("nickname", user.getRealname());
            item.put("deptId", buildDeptId(user.getClientId()));
            item.put("status", user.getStatus());
            return item;
        }).collect(Collectors.toList());
        JSONObject result = new JSONObject();
        result.put("list", items);
        return Result.ok(result);
    }

    @PostMapping("/adminUser/queryDeptTree")
    @ApiOperation("查询部门树（本地兼容实现）")
    public Result<Object> queryDeptTree() {
        LocalUser currentUser = getCurrentLocalUser();
        JSONObject dept = new JSONObject();
        dept.put("deptId", buildDeptId(currentUser != null ? currentUser.getClientId() : null));
        dept.put("name", currentUser != null && currentUser.getClientId() != null
                ? clientCompanyService.getById(currentUser.getClientId()).getClientName()
                : "平台用户");
        dept.put("children", Collections.emptyList());
        return Result.ok(Collections.singletonList(dept));
    }

    @PostMapping("/adminUser/queryOrganizationInfo")
    @ApiOperation("查询组织架构信息（本地兼容实现）")
    public Result<JSONObject> queryOrganizationInfo() {
        LocalUser currentUser = getCurrentLocalUser();
        List<ClientUserVO> users = clientUserService.querySelectableList(currentUser != null ? currentUser.getClientId() : null);
        Long deptId = buildDeptId(currentUser != null ? currentUser.getClientId() : null);

        JSONObject dept = new JSONObject();
        dept.put("deptId", deptId);
        dept.put("name", currentUser != null && currentUser.getClientId() != null
                ? clientCompanyService.getById(currentUser.getClientId()).getClientName()
                : "平台用户");
        dept.put("children", Collections.emptyList());

        JSONObject userMap = new JSONObject();
        List<JSONObject> userItems = users.stream().map(user -> {
            JSONObject userItem = new JSONObject();
            userItem.put("userId", user.getUserId());
            userItem.put("username", user.getUsername());
            userItem.put("realname", user.getRealname());
            userItem.put("nickname", user.getRealname());
            userItem.put("deptId", deptId);
            userItem.put("status", user.getStatus());
            return userItem;
        }).collect(Collectors.toList());
        userMap.put(String.valueOf(deptId), userItems);

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

    // ─── Mock 滑块验证码（直接放行）───────────────────────────────────────────

    @PostMapping("/cloud/getCaptcha")
    @ApiOperation("获取滑块验证码（Mock）")
    public Result<JSONObject> getCaptcha(@RequestBody(required = false) JSONObject body) {
        JSONObject data = new JSONObject();
        data.put("token", IdUtil.simpleUUID());
        data.put("secretKey", null);
        data.put("originalImageBase64", null);
        data.put("jigsawImageBase64", null);
        return Result.ok(data);
    }

    @PostMapping("/cloud/checkCaptcha")
    @ApiOperation("校验滑块验证码（Mock，直接通过）")
    public Result checkCaptcha(@RequestBody(required = false) JSONObject body) {
        return Result.ok();
    }

    // ─── 短信验证码 ───────────────────────────────────────────────────────────

    @PostMapping("/adminUser/sendSms")
    @ApiOperation("发送短信验证码（Mock 模式，验证码打印到日志）")
    public Result sendSms(@RequestBody JSONObject body) {
        return Result.error(400, "当前系统未启用短信验证码能力");
    }

    @PostMapping("/adminUser/verifySms")
    @ApiOperation("校验短信验证码")
    public Result<Integer> verifySms(@RequestBody JSONObject body) {
        return Result.error(400, "当前系统未启用短信验证码能力");
    }

    // ─── 验证码登录 ───────────────────────────────────────────────────────────

    @PostMapping("/adminUser/smsLogin")
    @ApiOperation("验证码登录")
    public Result<String> smsLogin(@RequestBody JSONObject body) {
        return Result.error(400, "当前系统未启用短信验证码能力");
    }

    // ─── 忘记密码 ─────────────────────────────────────────────────────────────

    @PostMapping("/adminUser/forgetPwd")
    @ApiOperation("忘记密码：手机号+验证码验证，返回账号列表")
    public Result forgetPwd(@RequestBody JSONObject body) {
        return Result.error(400, "当前系统未启用短信找回密码能力，请联系管理员重置密码");
    }

    @PostMapping("/adminUser/resetPwd")
    @ApiOperation("重置密码")
    public Result resetPwd(@RequestBody JSONObject body) {
        return Result.error(400, "当前系统未启用短信找回密码能力，请联系管理员重置密码");
    }

    // ─── 注册账号 ─────────────────────────────────────────────────────────────

    @PostMapping("/adminUser/register")
    @ApiOperation("注册账号")
    public Result<String> register(@RequestBody JSONObject body) {
        return Result.error(400, "当前系统不开放自助注册，请联系管理员创建账号");
    }

    // ─── 内部工具 ─────────────────────────────────────────────────────────────

    private String issueToken(LocalUser user) {
        String token = IdUtil.simpleUUID();
        UserInfo userInfo = buildUserInfo(user);
        int exp = Const.MAX_USER_EXIST_TIME;
        redis.set(token, userInfo);
        redis.expire(token, exp);
        redis.setex(token + Const.TOKEN_CACHE_NAME, exp, "1");
        LocalUserCacheUtil.cacheUserName(user.getUserId(), userInfo.getNickname());
        return token;
    }

    private LocalUser getCurrentLocalUser() {
        UserInfo userInfo = resolveCurrentUser();
        if (userInfo == null || userInfo.getUserId() == null) {
            return null;
        }
        return localUserMapper.selectById(userInfo.getUserId());
    }

    private Long buildDeptId(Long clientId) {
        return clientId == null ? 0L : clientId;
    }
}
