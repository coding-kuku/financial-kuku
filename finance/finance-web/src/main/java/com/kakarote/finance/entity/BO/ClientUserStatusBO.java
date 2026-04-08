package com.kakarote.finance.entity.BO;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

@Data
@ApiModel("客户用户状态更新参数")
public class ClientUserStatusBO {

    @ApiModelProperty("用户ID")
    private Long userId;

    @ApiModelProperty("状态")
    private Integer status;
}
