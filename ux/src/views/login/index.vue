<template>
  <div class="login">
    <div class="login__content">
      <div class="login-title">
        {{ companyInfo.name || '财务虾' }}
      </div>

      <login-by-pwd
        v-if="loginType === 'loginPwd'"
        :username.sync="username"
        @toggle="toggle"
      />

      <login-by-code
        v-else-if="loginType === 'loginCode'"
        @toggle="toggle"
      />

      <login-forget-pwd
        v-else-if="loginType === 'forgetPwd'"
        @toggle="toggle"
      />
    </div>

    <div class="footer">
      <img v-if="companyInfo.logo" :src="companyInfo.logo" class="company-logo">
      <img v-else src="@/assets/img/logo-full.png" class="company-logo company-logo--default">
      <div class="footer-des">FinClaw — 财务虾财务管理系统</div>
    </div>
  </div>
</template>

<script>
import { adminSystemIndexAPI } from '@/api/admin/config'
import LoginByPwd from './component/LoginByPwd'
import LoginByCode from './component/LoginByCode'
import LoginForgetPwd from './component/LoginForgetPwd'
import Lockr from 'lockr'
import { updateNavLinkName } from '@/utils'
import { LOCAL_LOGIN_LOGO_NAME } from '@/utils/constants.js'

export default {
  name: 'Login',
  components: { LoginByPwd, LoginByCode, LoginForgetPwd },
  data() {
    return {
      loginType: 'loginPwd',
      username: '',
      companyInfo: { name: '', logo: '' }
    }
  },
  created() {
    this.handleLoginCache('get')
    this.getLogoAndName()
  },
  methods: {
    toggle(type) {
      this.loginType = type
    },
    getLogoAndName() {
      adminSystemIndexAPI().then(res => {
        const resData = res.data
        if (resData) {
          this.handleLoginCache('set', resData)
        }
      }).catch(() => {})
    },
    handleLoginCache(type, data) {
      const hostname = window.location.hostname
      if (type === 'get') {
        updateNavLinkName()
        const logCacheInfo = Lockr.get(LOCAL_LOGIN_LOGO_NAME)
        if (logCacheInfo && logCacheInfo[hostname]) {
          const domainData = logCacheInfo[hostname]
          this.companyInfo = { name: domainData.companyName, logo: domainData.companyLoginLogo }
          updateNavLinkName(domainData)
        }
      } else if (type === 'set') {
        const logCacheInfo = Lockr.get(LOCAL_LOGIN_LOGO_NAME) || {}
        logCacheInfo[hostname] = data
        Lockr.set(LOCAL_LOGIN_LOGO_NAME, logCacheInfo)
        this.companyInfo.logo = data.companyLoginLogo
        this.companyInfo.name = data.companyName
        updateNavLinkName(data)
      }
    }
  }
}
</script>

<style lang="scss" scoped>
@media screen and (max-width: 1200px) {
  .login {
    background-image: none !important;
  }
}

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
