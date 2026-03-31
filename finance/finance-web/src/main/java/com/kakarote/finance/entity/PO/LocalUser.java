package com.kakarote.finance.entity.PO;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.io.Serializable;
import java.time.LocalDateTime;

@Data
@TableName("wk_admin_user")
public class LocalUser implements Serializable {

    private static final long serialVersionUID = 1L;

    @TableId(value = "user_id", type = IdType.ASSIGN_ID)
    private Long userId;

    private String username;

    private String password;

    private String salt;

    private String realname;

    private Integer status;

    private Boolean isAdmin;

    private LocalDateTime createTime;

    private String phone;
}
