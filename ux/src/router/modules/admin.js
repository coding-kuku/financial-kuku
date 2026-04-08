/** 系统管理路由 */
import Layout from '@/views/layout/AdminLayout'

const layout = function(meta = {}, path = '/manage', requiresAuth = true) {
  return {
    path: path,
    component: Layout,
    meta: {
      requiresAuth: requiresAuth,
      ...meta
    }
  }
}

export default [
  {
    ...layout({
      permissions: ['manage', 'clientCompany'],
      title: '客户公司',
      icon: 'wk wk-enterprise'
    }, '/manage/client'),
    alwaysShow: true,
    children: [{
      path: 'company',
      component: () => import('@/views/admin/clientCompany/index'),
      meta: {
        title: '客户公司管理',
        requiresAuth: true,
        permissions: ['manage', 'clientCompany']
      }
    }]
  },
  {
    ...layout({
      permissionList: [['manage', 'clientUser'], ['manage', 'finance', 'accountSet']],
      title: '客户用户',
      icon: 'wk wk-icon-user'
    }, '/manage/client-user'),
    alwaysShow: true,
    children: [{
      path: 'index',
      component: () => import('@/views/admin/clientUser/index'),
      meta: {
        title: '用户管理',
        requiresAuth: true,
        permissions: ['manage', 'clientUser']
      }
    }]
  },
  // 财务管理，账套管理
  {
    ...layout({
      permissions: ['manage', 'finance'],
      title: '财务管理',
      icon: 'icon-fm-line'
    }, '/manage/finance'),
    alwaysShow: true,
    children: [{
      path: 'handle',
      component: () => import('@/views/admin/finance/accountBook'),
      meta: {
        title: '账套管理',
        requiresAuth: true,
        permissions: ['manage', 'finance', 'accountSet']
      }
    }]
  }
]
