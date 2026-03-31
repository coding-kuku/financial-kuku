import request from '@/utils/request'

export function loginAPI(params) {
  return request({
    url: '/login',
    method: 'post',
    data: params,
    headers: {
      'Content-Type': 'application/json;charset=UTF-8'
    }
  })
}

export function authorizationAPI(params) {
  return request({
    url: '/adminUser/authorization',
    method: 'post',
    data: params
  })
}

export function logoutAPI() {
  return request({
    url: '/adminUser/logout',
    method: 'post'
  })
}

export function sendSmsAPI(params) {
  return request({
    url: '/adminUser/sendSms',
    method: 'post',
    data: params,
    headers: { 'Content-Type': 'application/json;charset=UTF-8' }
  })
}

export function verfySmsAPI(params) {
  return request({
    url: '/adminUser/verifySms',
    method: 'post',
    data: params,
    headers: { 'Content-Type': 'application/json;charset=UTF-8' }
  })
}

export function smsLoginAPI(params) {
  return request({
    url: '/adminUser/smsLogin',
    method: 'post',
    data: params,
    headers: { 'Content-Type': 'application/json;charset=UTF-8' }
  })
}

export function forgetPwdAPI(params) {
  return request({
    url: '/adminUser/forgetPwd',
    method: 'post',
    data: params,
    headers: { 'Content-Type': 'application/json;charset=UTF-8' }
  })
}

export function resetPwdAPI(params) {
  return request({
    url: '/adminUser/resetPwd',
    method: 'post',
    data: params,
    headers: { 'Content-Type': 'application/json;charset=UTF-8' }
  })
}

export function registerAPI(params) {
  return request({
    url: '/adminUser/register',
    method: 'post',
    data: params,
    headers: { 'Content-Type': 'application/json;charset=UTF-8' }
  })
}
