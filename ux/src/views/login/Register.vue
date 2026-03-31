<template>
  <div class="login">
    <div class="login__content">
      <div class="login-title">
        开始使用
      </div>

      <el-form
        ref="ruleForm"
        :model="ruleForm"
        :rules="rules"
        label-width="100px"
        label-position="top"
        @submit.native.prevent>
        <el-form-item label="" prop="phone">
          <el-input v-model.trim="ruleForm.phone" placeholder="手机号" />
        </el-form-item>
        <el-form-item label="" prop="smscode">
          <el-input v-model.trim="ruleForm.smscode" placeholder="验证码">
            <verify-button
              slot="suffix"
              ref="verifyButton"
              :disabled="!ruleForm.phone"
              @success="verifySuccess"
            />
          </el-input>
        </el-form-item>
        <el-form-item label="" prop="username">
          <el-input v-model.trim="ruleForm.username" placeholder="用户名" />
        </el-form-item>
        <el-form-item label="" prop="password">
          <el-input
            v-model.trim="ruleForm.password"
            :type="passwordType"
            placeholder="密码">
            <i
              slot="suffix"
              :style="{ color: passwordType === '' ? '#243858' : '#C1C7D0' }"
              class="wk wk-icon-eye-solid"
              @click="passwordType = passwordType === '' ? 'password' : ''" />
          </el-input>
        </el-form-item>
        <div class="handle-bar">
          <el-button
            :loading="loading"
            type="primary"
            @click="handleRegister">同意并注册</el-button>
        </div>
        <div class="other-handle">
          <el-button type="text" @click="$router.push('/login')">已有账号，去登录</el-button>
        </div>
      </el-form>
    </div>

    <div class="footer">
      <img src="@/assets/img/logo-full.png" class="company-logo company-logo--default">
      <div class="footer-des">FinClaw — 财务虾财务管理系统</div>
    </div>
  </div>
</template>

<script>
import VerifyButton from '@/components/Verify/Button'
import { sendSmsAPI, registerAPI } from '@/api/login'
import { addAuth } from '@/utils/auth'

export default {
  name: 'Register',
  components: { VerifyButton },
  data() {
    return {
      loading: false,
      passwordType: 'password',
      ruleForm: { phone: '', smscode: '', username: '', password: '' },
      rules: {
        phone: [{ required: true, message: '手机号不能为空', trigger: 'change' }],
        smscode: [{ required: true, message: '验证码不能为空', trigger: 'change' }],
        username: [{ required: true, message: '用户名不能为空', trigger: 'change' }],
        password: [{ required: true, message: '密码不能为空', trigger: 'change' }]
      }
    }
  },
  methods: {
    verifySuccess(params) {
      sendSmsAPI({ telephone: this.ruleForm.phone, type: 1, ...(params || {}) })
        .then(() => {
          this.$refs.verifyButton.startTimer()
          this.$message.success('验证码已发送，请查看服务端日志（Mock 模式）')
        }).catch(() => {})
    },
    handleRegister() {
      this.$refs.ruleForm.validate(valid => {
        if (!valid) return
        this.loading = true
        registerAPI(this.ruleForm)
          .then(res => {
            this.loading = false
            return addAuth(res.data)
          })
          .then(() => {
            this.$router.push('/')
          })
          .catch(() => {
            this.loading = false
          })
      })
    }
  }
}
</script>

<style lang="scss" scoped>
@import "./style/index.scss";

.login {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 100vh;
  background-image: url("./img/left.png"), url("./img/right.png");
  background-repeat: no-repeat, no-repeat;
  background-attachment: fixed, fixed;
  background-position: left bottom, right bottom;
  background-size: 360px, 480px;

  &__content {
    width: 400px;
    margin: 0 auto;
    text-align: center;
  }

  &-title {
    padding: 40px 0;
    font-size: 25px;
    font-weight: bold;
    line-height: 40px;
    color: $--color-primary;
  }

  .footer {
    width: 400px;
    padding: 24px 0;
    margin: 0 auto;
    font-size: 12px;
    color: $--color-text-secondary;
    text-align: center;

    > .company-logo {
      width: 160px;

      &--default {
        width: 220px;
      }
    }

    &-des {
      margin-top: 16px;
      font-size: 12px;
      color: $--color-text-secondary;
    }
  }
}
</style>
