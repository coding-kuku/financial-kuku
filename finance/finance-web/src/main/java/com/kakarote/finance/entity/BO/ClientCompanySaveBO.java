package com.kakarote.finance.entity.BO;

import io.swagger.annotations.ApiModel;
import io.swagger.annotations.ApiModelProperty;
import lombok.Data;

@Data
@ApiModel("客户公司保存参数")
public class ClientCompanySaveBO {

    @ApiModelProperty("客户公司ID")
    private Long clientId;

    @ApiModelProperty("客户公司名称")
    private String clientName;

    @ApiModelProperty("客户公司编码")
    private String clientCode;

    @ApiModelProperty("联系人")
    private String contactName;

    @ApiModelProperty("联系电话")
    private String contactPhone;

    @ApiModelProperty("备注")
    private String remark;

    @ApiModelProperty("状态")
    private Integer status;
}
