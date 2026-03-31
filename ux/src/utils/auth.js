import axios from '@/utils/request'
import cache from './cache'
import Lockr from 'lockr'
import store from '@/store'
import router from '@/router'
import Cookies from 'js-cookie'
import { getCookiesDomain } from '@/utils'
import { LOCAL_ADMIN_TOKEN, COOKIE_ADMIN_TOKEN } from '@/utils/constants.js'

/** 移除授权信息 */
export function removeAuth(props = { clearCookies: false }) {
  return new Promise((resolve, reject) => {
    cache.rmAxiosCache()
    store.commit('SET_ALLAUTH', null)
    delete axios.defaults.headers.common[LOCAL_ADMIN_TOKEN]
    resolve(true)
  })
}

/** 注入授权信息 */
export function addAuth(adminToken) {
  return new Promise((resolve, reject) => {
    axios.defaults.headers.common[LOCAL_ADMIN_TOKEN] = adminToken
    Lockr.set(LOCAL_ADMIN_TOKEN, adminToken)
    const domain = getCookiesDomain()
    Cookies.set(COOKIE_ADMIN_TOKEN, adminToken, { domain: domain, expires: 365 })
    // store.dispatch('SystemLogoAndName')
    resolve(true)
  })
}

/** 获取授权信息 */
export function getAuth() {
  return new Promise((resolve, reject) => {
    const token = Lockr.get(LOCAL_ADMIN_TOKEN) || Cookies.get(COOKIE_ADMIN_TOKEN)
    if (!token) return reject('Not Found Token')

    cache.updateAxiosCache(token)
    if (!store.state.user.userInfo) {
      store.dispatch('GetUserInfo')
        .then(() => {
          resolve()
        })
        .catch(error => {
          reject(error)
        })
    } else {
      resolve()
    }
  })
}

/**
 * 重定向到登录页
 */
export function redirectLogin() {
  const redirect = window.location.pathname
  router.replace({ path: '/login', query: { redirect } }, () => {}, () => {})
}
