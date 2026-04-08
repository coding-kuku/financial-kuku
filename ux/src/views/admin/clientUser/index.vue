<template>
  <div class="app-container client-page">
    <xr-header label="客户用户管理" />

    <div class="toolbar">
      <el-select
        v-if="userInfo.isAdmin"
        v-model="query.clientId"
        clearable
        placeholder="选择客户公司"
        class="toolbar-item"
        @change="loadData">
        <el-option
          v-for="item in clientOptions"
          :key="item.clientId"
          :label="item.clientName"
          :value="item.clientId" />
      </el-select>
      <el-input
        v-model.trim="query.keyword"
        placeholder="搜索账号/姓名"
        clearable
        class="toolbar-item"
        @keyup.enter.native="loadData" />
      <el-select
        v-model="query.status"
        clearable
        placeholder="状态"
        class="toolbar-item"
        @change="loadData">
        <el-option label="启用" :value="1" />
        <el-option label="停用" :value="0" />
      </el-select>
      <el-button type="primary" @click="openCreate">新建用户</el-button>
    </div>

    <el-table
      v-loading="loading"
      :data="list"
      :stripe="WKConfig.tableStyle.stripe"
      :class="WKConfig.tableStyle.class">
      <el-table-column prop="clientName" label="客户公司" min-width="160" />
      <el-table-column prop="username" label="登录账号" min-width="140" />
      <el-table-column prop="realname" label="姓名" min-width="120" />
      <el-table-column prop="phone" label="手机号" min-width="140" />
      <el-table-column label="客户管理员" width="110">
        <template slot-scope="{ row }">
          <el-tag :type="row.isClientAdmin ? 'warning' : 'info'" size="mini">
            {{ row.isClientAdmin ? '是' : '否' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template slot-scope="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'info'" size="mini">
            {{ row.status === 1 ? '启用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" min-width="320" fixed="right">
        <template slot-scope="{ row }">
          <el-button type="text" @click="openEdit(row)">编辑</el-button>
          <el-button type="text" @click="toggleAdmin(row)">
            {{ row.isClientAdmin ? '取消管理员' : '设为管理员' }}
          </el-button>
          <el-button type="text" @click="toggleStatus(row)">
            {{ row.status === 1 ? '停用' : '启用' }}
          </el-button>
          <el-button type="text" @click="openResetPassword(row)">重置密码</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog
      :visible.sync="dialogVisible"
      :title="dialogTitle"
      width="640px"
      :close-on-click-modal="false">
      <el-form
        ref="form"
        :model="form"
        :rules="rules"
        label-width="110px">
        <el-form-item v-if="userInfo.isAdmin" label="客户公司" prop="clientId">
          <el-select v-model="form.clientId" placeholder="请选择客户公司" style="width: 100%;">
            <el-option
              v-for="item in clientOptions"
              :key="item.clientId"
              :label="item.clientName"
              :value="item.clientId" />
          </el-select>
        </el-form-item>
        <el-form-item label="登录账号" prop="username">
          <el-input v-model.trim="form.username" :disabled="!!form.userId" />
        </el-form-item>
        <el-form-item label="姓名" prop="realname">
          <el-input v-model.trim="form.realname" />
        </el-form-item>
        <el-form-item label="手机号" prop="phone">
          <el-input v-model.trim="form.phone" />
        </el-form-item>
        <el-form-item v-if="!form.userId" label="初始密码" prop="password">
          <el-input v-model.trim="form.password" show-password />
        </el-form-item>
        <el-form-item label="客户管理员" prop="isClientAdmin">
          <el-switch v-model="form.isClientAdmin" />
        </el-form-item>
        <el-form-item label="状态" prop="status">
          <el-switch
            v-model="statusSwitch"
            active-text="启用"
            inactive-text="停用" />
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="save">确定</el-button>
      </div>
    </el-dialog>

    <el-dialog
      :visible.sync="passwordDialogVisible"
      title="重置密码"
      width="420px"
      :close-on-click-modal="false">
      <el-form ref="passwordForm" :model="passwordForm" :rules="passwordRules" label-width="90px">
        <el-form-item label="新密码" prop="password">
          <el-input v-model.trim="passwordForm.password" show-password />
        </el-form-item>
      </el-form>
      <div slot="footer">
        <el-button @click="passwordDialogVisible = false">取消</el-button>
        <el-button type="primary" @click="resetPassword">确定</el-button>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import XrHeader from '@/components/XrHeader'
import { queryClientCompanySelectableListAPI } from '@/api/admin/clientCompany'
import {
  queryClientUserListAPI,
  addClientUserAPI,
  updateClientUserAPI,
  updateClientUserStatusAPI,
  updateClientUserAdminStatusAPI,
  resetClientUserPasswordAPI
} from '@/api/admin/clientUser'
import { mapGetters } from 'vuex'

export default {
  name: 'ClientUserManage',
  components: { XrHeader },
  data() {
    return {
      loading: false,
      list: [],
      clientOptions: [],
      query: {
        clientId: null,
        keyword: '',
        status: null
      },
      dialogVisible: false,
      dialogTitle: '新建用户',
      form: {
        userId: null,
        clientId: null,
        username: '',
        realname: '',
        phone: '',
        password: '',
        status: 1,
        isClientAdmin: false
      },
      rules: {
        clientId: [{ required: true, message: '请选择客户公司', trigger: 'change' }],
        username: [{ required: true, message: '请输入登录账号', trigger: 'blur' }],
        realname: [{ required: true, message: '请输入姓名', trigger: 'blur' }],
        password: [{ required: true, message: '请输入初始密码', trigger: 'blur' }]
      },
      passwordDialogVisible: false,
      passwordForm: {
        userId: null,
        password: ''
      },
      passwordRules: {
        password: [{ required: true, message: '请输入新密码', trigger: 'blur' }]
      }
    }
  },
  computed: {
    ...mapGetters(['userInfo']),
    statusSwitch: {
      get() {
        return this.form.status === 1
      },
      set(val) {
        this.form.status = val ? 1 : 0
      }
    }
  },
  created() {
    this.loadClientOptions()
  },
  methods: {
    loadClientOptions() {
      queryClientCompanySelectableListAPI().then(res => {
        this.clientOptions = res.data || []
        if (!this.userInfo.isAdmin) {
          this.query.clientId = this.userInfo.clientId
        }
        this.loadData()
      })
    },
    loadData() {
      this.loading = true
      queryClientUserListAPI(this.query).then(res => {
        this.list = res.data || []
        this.loading = false
      }).catch(() => {
        this.loading = false
      })
    },
    openCreate() {
      this.dialogTitle = '新建用户'
      this.form = {
        userId: null,
        clientId: this.userInfo.isAdmin ? this.query.clientId : this.userInfo.clientId,
        username: '',
        realname: '',
        phone: '',
        password: '',
        status: 1,
        isClientAdmin: false
      }
      this.dialogVisible = true
      this.$nextTick(() => this.$refs.form && this.$refs.form.clearValidate())
    },
    openEdit(row) {
      this.dialogTitle = '编辑用户'
      this.form = {
        userId: row.userId,
        clientId: row.clientId,
        username: row.username,
        realname: row.realname,
        phone: row.phone,
        password: '',
        status: row.status,
        isClientAdmin: row.isClientAdmin
      }
      this.dialogVisible = true
      this.$nextTick(() => this.$refs.form && this.$refs.form.clearValidate())
    },
    save() {
      this.$refs.form.validate(valid => {
        if (!valid) return
        const request = this.form.userId ? updateClientUserAPI : addClientUserAPI
        request(this.form).then(() => {
          this.$message.success('保存成功')
          this.dialogVisible = false
          this.loadData()
        })
      })
    },
    toggleStatus(row) {
      updateClientUserStatusAPI({
        userId: row.userId,
        status: row.status === 1 ? 0 : 1
      }).then(() => {
        this.$message.success('状态已更新')
        this.loadData()
      })
    },
    toggleAdmin(row) {
      updateClientUserAdminStatusAPI({
        userId: row.userId,
        isClientAdmin: !row.isClientAdmin
      }).then(() => {
        this.$message.success('管理员状态已更新')
        this.loadData()
      })
    },
    openResetPassword(row) {
      this.passwordForm = {
        userId: row.userId,
        password: ''
      }
      this.passwordDialogVisible = true
      this.$nextTick(() => this.$refs.passwordForm && this.$refs.passwordForm.clearValidate())
    },
    resetPassword() {
      this.$refs.passwordForm.validate(valid => {
        if (!valid) return
        resetClientUserPasswordAPI(this.passwordForm).then(() => {
          this.$message.success('密码已重置')
          this.passwordDialogVisible = false
        })
      })
    }
  }
}
</script>

<style scoped lang="scss">
.client-page {
  padding: 15px 40px 0;
}

.toolbar {
  display: flex;
  gap: 12px;
  align-items: center;
  margin: 16px 0;
}

.toolbar-item {
  width: 240px;
}
</style>
