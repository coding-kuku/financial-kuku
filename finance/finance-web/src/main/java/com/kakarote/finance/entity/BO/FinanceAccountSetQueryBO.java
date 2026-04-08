package com.kakarote.finance.entity.BO;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

@Data
@ApiModel("账套查询参数")
public class FinanceAccountSetQueryBO {

    @ApiModelProperty("客户公司ID")
    private Long clientId;
}
