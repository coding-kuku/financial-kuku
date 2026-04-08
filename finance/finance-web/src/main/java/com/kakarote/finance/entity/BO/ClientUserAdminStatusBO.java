package com.kakarote.finance.entity.BO;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

@Data
@ApiModel("客户管理员状态更新参数")
public class ClientUserAdminStatusBO {

    @ApiModelProperty("用户ID")
    private Long userId;

    @ApiModelProperty("是否客户管理员")
    private Boolean isClientAdmin;
}
