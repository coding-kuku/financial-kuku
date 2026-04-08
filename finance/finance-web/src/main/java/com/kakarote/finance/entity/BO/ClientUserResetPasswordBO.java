package com.kakarote.finance.entity.BO;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

@Data
@ApiModel("客户用户重置密码参数")
public class ClientUserResetPasswordBO {

    @ApiModelProperty("用户ID")
    private Long userId;

    @ApiModelProperty("新密码")
    private String password;
}
