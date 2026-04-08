package com.kakarote.finance.entity.VO;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

@Data
@ApiModel("客户用户视图")
public class ClientUserVO {

    @ApiModelProperty("用户ID")
    private Long userId;

    @ApiModelProperty("客户公司ID")
    private Long clientId;

    @ApiModelProperty("客户公司名称")
    private String clientName;

    @ApiModelProperty("登录账号")
    private String username;

    @ApiModelProperty("姓名")
    private String realname;

    @ApiModelProperty("手机号")
    private String phone;

    @ApiModelProperty("状态")
    private Integer status;

    @ApiModelProperty("是否平台超管")
    private Boolean isAdmin;

    @ApiModelProperty("是否客户管理员")
    private Boolean isClientAdmin;

    @ApiModelProperty("用户类型")
    private String userType;
}
