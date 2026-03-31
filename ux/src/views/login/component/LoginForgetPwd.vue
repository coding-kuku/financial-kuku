<template>
  <el-form
    ref="ruleForm"
    :model="ruleForm"
    :rules="rules"
    label-width="100px"
    label-position="top"
    @submit.native.prevent>
    <div class="form-title">重置您的帐户密码</div>

    <!-- Step 1: 手机号 -->
    <el-form-item v-if="step === 1" label="" prop="phone">
      <el-input
        v-model.trim="ruleForm.phone"
        placeholder="请输入手机号"
        @keyup.enter.native="nextStep" />
    </el-form-item>

    <!-- Step 2: 验证码 -->
    <template v-if="step === 2">
      <show-item :content="ruleForm.phone" @click.native="step = 1" />
      <el-form-item label="" prop="smscode" style="margin-top:12px">
        <el-input v-model.trim="ruleForm.smscode" placeholder="请输入验证码">
          <verify-button
            slot="suffix"
            ref="verifyButton"
            @success="verifySuccess"
          />
        </el-input>
      </el-form-item>
    </template>

    <!-- Step 3: 新密码 -->
    <template v-if="step === 3">
      <el-form-item label="" prop="password">
        <el-input
          v-model.trim="ruleForm.password"
          :type="passwordType"
          placeholder="请输入新密码">
          <i
            slot="suffix"
            :style="{ color: passwordType === '' ? '#243858' : '#C1C7D0' }"
            class="wk wk-icon-eye-solid"
            @click="passwordType = passwordType === '' ? 'password' : ''" />
        </el-input>
      </el-form-item>
    </template>

    <div class="handle-bar">
      <el-button
        :loading="loading"
        type="primary"
        @click="nextStep">{{ btnText }}</el-button>
    </div>

    <div class="other-handle">
      <el-button type="text" @click="$emit('toggle', 'loginPwd')">返回登录页面</el-button>
    </div>
  </el-form>
</template>

<script>
import ShowItem from './ShowItem'
import VerifyButton from '@/components/Verify/Button'
import { sendSmsAPI, verfySmsAPI, forgetPwdAPI, resetPwdAPI } from '@/api/login'

export default {
  name: 'LoginForgetPwd',
  components: { ShowItem, VerifyButton },
  data() {
    return {
      step: 1,
      loading: false,
      passwordType: 'password',
      companyId: null,
      ruleForm: { phone: '', smscode: '', password: '' },
      rules: {
        phone: [{ required: true, message: '手机号不能为空', trigger: 'change' }],
        smscode: [{ required: true, message: '验证码不能为空', trigger: 'change' }],
        password: [{ required: true, message: '新密码不能为空', trigger: 'change' }]
      }
    }
  },
  computed: {
    btnText() {
      if (this.step === 1) return '继续'
      if (this.step === 2) return '验证'
      return '重置密码'
    }
  },
  methods: {
    verifySuccess(params) {
      sendSmsAPI({ telephone: this.ruleForm.phone, type: 2, ...(params || {}) })
        .then(() => {
          this.$refs.verifyButton.startTimer()
          this.$message.success('验证码已发送，请查看服务端日志（Mock 模式）')
        }).catch(() => {})
    },
    nextStep() {
      if (this.step === 1) {
        this.$refs.ruleForm.validateField('phone', err => {
          if (!err) this.step = 2
        })
      } else if (this.step === 2) {
        this.loading = true
        verfySmsAPI({ phone: this.ruleForm.phone, smsCode: this.ruleForm.smscode })
          .then(res => {
            this.loading = false
            if (res.data === 1) {
              return forgetPwdAPI({ phone: this.ruleForm.phone, smscode: this.ruleForm.smscode })
            }
            this.$message.error('验证码错误')
          })
          .then(res => {
            if (!res) return
            const list = res.data || []
            if (list.length > 0) {
              this.companyId = list[0].companyId
              this.step = 3
            } else {
              this.$message.error('该手机号未注册')
            }
          })
          .catch(() => { this.loading = false })
      } else if (this.step === 3) {
        this.$refs.ruleForm.validateField('password', err => {
          if (err) return
          this.loading = true
          resetPwdAPI({
            phone: this.ruleForm.phone,
            smscode: this.ruleForm.smscode,
            password: this.ruleForm.password,
            companyId: this.companyId
          }).then(() => {
            this.loading = false
            this.$message.success('密码重置成功，请重新登录')
            this.$emit('toggle', 'loginPwd')
          }).catch(() => { this.loading = false })
        })
      }
    }
  }
}
</script>

<style lang="scss" scoped>
@import "../style/index.scss";
</style>
