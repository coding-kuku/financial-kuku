package com.kakarote.finance.entity.VO;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

@Data
@ApiModel("客户公司简单信息")
public class ClientCompanySimpleVO {

    @ApiModelProperty("客户公司ID")
    private Long clientId;

    @ApiModelProperty("客户公司名称")
    private String clientName;
}
