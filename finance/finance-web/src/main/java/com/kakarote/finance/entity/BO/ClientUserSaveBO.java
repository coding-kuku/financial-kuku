package com.kakarote.finance.entity.BO;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

@Data
@ApiModel("客户用户保存参数")
public class ClientUserSaveBO {

    @ApiModelProperty("用户ID")
    private Long userId;

    @ApiModelProperty("客户公司ID")
    private Long clientId;

    @ApiModelProperty("登录账号")
    private String username;

    @ApiModelProperty("姓名")
    private String realname;

    @ApiModelProperty("手机号")
    private String phone;

    @ApiModelProperty("状态")
    private Integer status;

    @ApiModelProperty("是否客户管理员")
    private Boolean isClientAdmin;

    @ApiModelProperty("初始密码")
    private String password;
}
