import request from '@/utils/request'

const JSON_HEADER = { 'Content-Type': 'application/json' }

export function queryClientUserListAPI(data) {
  return request({
    url: 'clientUser/queryList',
    method: 'post',
    data,
    headers: JSON_HEADER
  })
}

export function queryClientUserSelectableListAPI(data) {
  return request({
    url: 'clientUser/querySelectableList',
    method: 'post',
    params: data
  })
}

export function addClientUserAPI(data) {
  return request({
    url: 'clientUser/add',
    method: 'post',
    data,
    headers: JSON_HEADER
  })
}

export function updateClientUserAPI(data) {
  return request({
    url: 'clientUser/update',
    method: 'post',
    data,
    headers: JSON_HEADER
  })
}

export function updateClientUserStatusAPI(data) {
  return request({
    url: 'clientUser/updateStatus',
    method: 'post',
    data,
    headers: JSON_HEADER
  })
}

export function updateClientUserAdminStatusAPI(data) {
  return request({
    url: 'clientUser/updateAdminStatus',
    method: 'post',
    data,
    headers: JSON_HEADER
  })
}

export function resetClientUserPasswordAPI(data) {
  return request({
    url: 'clientUser/resetPassword',
    method: 'post',
    data,
    headers: JSON_HEADER
  })
}

export function updateSelfPasswordAPI(data) {
  return request({
    url: 'clientUser/updateSelfPassword',
    method: 'post',
    data,
    headers: JSON_HEADER
  })
}
