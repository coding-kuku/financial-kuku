package com.kakarote.finance.controller;

import com.kakarote.core.common.Result;
import com.kakarote.finance.entity.BO.ClientCompanyQueryBO;
import com.kakarote.finance.entity.BO.ClientCompanySaveBO;
import com.kakarote.finance.entity.PO.ClientCompany;
import com.kakarote.finance.entity.VO.ClientCompanySimpleVO;
import com.kakarote.finance.service.IClientCompanyService;
import io.swagger.annotations.Api;
import io.swagger.annotations.ApiOperation;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/clientCompany")
@Api(tags = "客户公司管理")
public class ClientCompanyController {

    @Autowired
    private IClientCompanyService clientCompanyService;

    @PostMapping("/queryList")
    @ApiOperation("客户公司列表")
    public Result<List<ClientCompany>> queryList(@RequestBody(required = false) ClientCompanyQueryBO queryBO) {
        return Result.ok(clientCompanyService.queryList(queryBO));
    }

    @PostMapping("/querySelectableList")
    @ApiOperation("可选客户公司列表")
    public Result<List<ClientCompanySimpleVO>> querySelectableList() {
        return Result.ok(clientCompanyService.querySelectableList());
    }

    @PostMapping("/add")
    @ApiOperation("新增客户公司")
    public Result<ClientCompany> add(@RequestBody ClientCompanySaveBO saveBO) {
        return Result.ok(clientCompanyService.save(saveBO));
    }

    @PostMapping("/update")
    @ApiOperation("编辑客户公司")
    public Result<ClientCompany> update(@RequestBody ClientCompanySaveBO saveBO) {
        return Result.ok(clientCompanyService.update(saveBO));
    }

    @PostMapping("/updateStatus")
    @ApiOperation("更新客户公司状态")
    public Result updateStatus(@RequestParam("clientId") Long clientId, @RequestParam("status") Integer status) {
        clientCompanyService.updateStatus(clientId, status);
        return Result.ok();
    }
}
