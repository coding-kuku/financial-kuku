<template>
  <el-form
    ref="ruleForm"
    :model="ruleForm"
    :rules="rules"
    label-width="100px"
    label-position="top"
    @submit.native.prevent>
    <div class="form-title">登录您的帐户</div>
    <el-form-item label="" prop="phone">
      <el-input
        v-model.trim="ruleForm.phone"
        :disabled="loading"
        placeholder="请输入手机号"
        @keyup.enter.native="handleLogin" />
    </el-form-item>
    <el-form-item label="" prop="smsCode">
      <el-input v-model.trim="ruleForm.smsCode" placeholder="请输入验证码">
        <verify-button
          slot="suffix"
          ref="verifyButton"
          :disabled="!ruleForm.phone"
          @success="verifySuccess"
        />
      </el-input>
    </el-form-item>
    <div class="handle-bar">
      <el-button
        :loading="loading"
        :disabled="loading"
        type="primary"
        @click="handleLogin">登录</el-button>
    </div>
  </el-form>
</template>

<script>
import VerifyButton from '@/components/Verify/Button'
import LoginMixin from './LoginMixin'
import { sendSmsAPI, smsLoginAPI } from '@/api/login'
import { addAuth } from '@/utils/auth'

export default {
  name: 'LoginByCode',
  components: { VerifyButton },
  mixins: [LoginMixin],
  data() {
    return {
      loading: false,
      ruleForm: {
        phone: '',
        smsCode: ''
      },
      rules: {
        phone: [{ required: true, message: '手机号不能为空', trigger: 'change' }],
        smsCode: [{ required: true, message: '验证码不能为空', trigger: 'change' }]
      }
    }
  },
  methods: {
    verifySuccess(params) {
      sendSmsAPI({
        telephone: this.ruleForm.phone,
        type: 1,
        ...(params || {})
      }).then(() => {
        this.$refs.verifyButton.startTimer()
        this.$message.success('验证码已发送，请查看服务端日志（Mock 模式）')
      }).catch(() => {})
    },
    handleLogin() {
      this.$refs.ruleForm.validate(valid => {
        if (!valid) return
        this.loading = true
        smsLoginAPI({ phone: this.ruleForm.phone, smsCode: this.ruleForm.smsCode })
          .then(res => {
            this.loading = false
            return addAuth(res.data)
          })
          .then(() => {
            this.$router.push({ path: this.redirect || '/' })
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
@import "../style/index.scss";
</style>
