package com.kakarote.finance.controller;

import com.kakarote.core.common.Result;
import com.kakarote.finance.entity.BO.*;
import com.kakarote.finance.entity.VO.ClientUserVO;
import com.kakarote.finance.service.IClientUserService;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/clientUser")
@Api(tags = "客户用户管理")
public class ClientUserController {

    @Autowired
    private IClientUserService clientUserService;

    @PostMapping("/queryList")
    @ApiOperation("客户用户列表")
    public Result<List<ClientUserVO>> queryList(@RequestBody(required = false) ClientUserQueryBO queryBO) {
        return Result.ok(clientUserService.queryList(queryBO));
    }

    @PostMapping("/querySelectableList")
    @ApiOperation("客户内可选用户列表")
    public Result<List<ClientUserVO>> querySelectableList(@RequestParam(value = "clientId", required = false) Long clientId) {
        return Result.ok(clientUserService.querySelectableList(clientId));
    }

    @PostMapping("/add")
    @ApiOperation("新增客户用户")
    public Result<ClientUserVO> add(@RequestBody ClientUserSaveBO saveBO) {
        return Result.ok(clientUserService.save(saveBO));
    }

    @PostMapping("/update")
    @ApiOperation("编辑客户用户")
    public Result<ClientUserVO> update(@RequestBody ClientUserSaveBO saveBO) {
        return Result.ok(clientUserService.update(saveBO));
    }

    @PostMapping("/updateStatus")
    @ApiOperation("更新用户状态")
    public Result updateStatus(@RequestBody ClientUserStatusBO statusBO) {
        clientUserService.updateStatus(statusBO);
        return Result.ok();
    }

    @PostMapping("/updateAdminStatus")
    @ApiOperation("更新客户管理员状态")
    public Result updateAdminStatus(@RequestBody ClientUserAdminStatusBO statusBO) {
        clientUserService.updateAdminStatus(statusBO);
        return Result.ok();
    }

    @PostMapping("/resetPassword")
    @ApiOperation("重置密码")
    public Result resetPassword(@RequestBody ClientUserResetPasswordBO resetPasswordBO) {
        clientUserService.resetPassword(resetPasswordBO);
        return Result.ok();
    }

    @PostMapping("/updateSelfPassword")
    @ApiOperation("当前用户修改密码")
    public Result updateSelfPassword(@RequestBody SelfPasswordUpdateBO updateBO) {
        clientUserService.updateSelfPassword(updateBO);
        return Result.ok();
    }
}
