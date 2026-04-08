import request from '@/utils/request'

const JSON_HEADER = { 'Content-Type': 'application/json' }

export function queryClientCompanyListAPI(data) {
  return request({
    url: 'clientCompany/queryList',
    method: 'post',
    data,
    headers: JSON_HEADER
  })
}

export function queryClientCompanySelectableListAPI() {
  return request({
    url: 'clientCompany/querySelectableList',
    method: 'post'
  })
}

export function addClientCompanyAPI(data) {
  return request({
    url: 'clientCompany/add',
    method: 'post',
    data,
    headers: JSON_HEADER
  })
}

export function updateClientCompanyAPI(data) {
  return request({
    url: 'clientCompany/update',
    method: 'post',
    data,
    headers: JSON_HEADER
  })
}

export function updateClientCompanyStatusAPI(data) {
  return request({
    url: 'clientCompany/updateStatus',
    method: 'post',
    params: data
  })
}
