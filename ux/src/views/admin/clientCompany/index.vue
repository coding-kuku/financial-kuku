<template>
  <div class="app-container client-page">
    <xr-header label="客户公司管理" />

    <div class="toolbar">
      <el-input
        v-model.trim="query.keyword"
        placeholder="搜索客户公司名称/编码"
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
      <el-button type="primary" @click="openCreate">新建客户公司</el-button>
    </div>

    <el-table
      v-loading="loading"
      :data="list"
      :stripe="WKConfig.tableStyle.stripe"
      :class="WKConfig.tableStyle.class">
      <el-table-column prop="clientName" label="客户公司名称" min-width="180" />
      <el-table-column prop="clientCode" label="公司编码" min-width="140" />
      <el-table-column prop="contactName" label="联系人" min-width="120" />
      <el-table-column prop="contactPhone" label="联系电话" min-width="140" />
      <el-table-column prop="remark" label="备注" min-width="180" />
      <el-table-column label="状态" width="100">
        <template slot-scope="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'info'" size="mini">
            {{ row.status === 1 ? '启用' : '停用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="220" fixed="right">
        <template slot-scope="{ row }">
          <el-button type="text" @click="openEdit(row)">编辑</el-button>
          <el-button
            type="text"
            @click="toggleStatus(row)">
            {{ row.status === 1 ? '停用' : '启用' }}
          </el-button>
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
        <el-form-item label="客户公司名称" prop="clientName">
          <el-input v-model.trim="form.clientName" />
        </el-form-item>
        <el-form-item label="公司编码" prop="clientCode">
          <el-input v-model.trim="form.clientCode" />
        </el-form-item>
        <el-form-item label="联系人" prop="contactName">
          <el-input v-model.trim="form.contactName" />
        </el-form-item>
        <el-form-item label="联系电话" prop="contactPhone">
          <el-input v-model.trim="form.contactPhone" />
        </el-form-item>
        <el-form-item label="备注" prop="remark">
          <el-input v-model.trim="form.remark" type="textarea" :rows="3" />
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
  </div>
</template>

<script>
import XrHeader from '@/components/XrHeader'
import {
  queryClientCompanyListAPI,
  addClientCompanyAPI,
  updateClientCompanyAPI,
  updateClientCompanyStatusAPI
} from '@/api/admin/clientCompany'

export default {
  name: 'ClientCompanyManage',
  components: { XrHeader },
  data() {
    return {
      loading: false,
      list: [],
      query: {
        keyword: '',
        status: null
      },
      dialogVisible: false,
      dialogTitle: '新建客户公司',
      form: {
        clientId: null,
        clientName: '',
        clientCode: '',
        contactName: '',
        contactPhone: '',
        remark: '',
        status: 1
      },
      rules: {
        clientName: [{ required: true, message: '请输入客户公司名称', trigger: 'blur' }]
      }
    }
  },
  computed: {
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
    this.loadData()
  },
  methods: {
    loadData() {
      this.loading = true
      queryClientCompanyListAPI(this.query).then(res => {
        this.list = res.data || []
        this.loading = false
      }).catch(() => {
        this.loading = false
      })
    },
    openCreate() {
      this.dialogTitle = '新建客户公司'
      this.form = {
        clientId: null,
        clientName: '',
        clientCode: '',
        contactName: '',
        contactPhone: '',
        remark: '',
        status: 1
      }
      this.dialogVisible = true
      this.$nextTick(() => this.$refs.form && this.$refs.form.clearValidate())
    },
    openEdit(row) {
      this.dialogTitle = '编辑客户公司'
      this.form = { ...row }
      this.dialogVisible = true
      this.$nextTick(() => this.$refs.form && this.$refs.form.clearValidate())
    },
    save() {
      this.$refs.form.validate(valid => {
        if (!valid) return
        const request = this.form.clientId ? updateClientCompanyAPI : addClientCompanyAPI
        request(this.form).then(() => {
          this.$message.success('保存成功')
          this.dialogVisible = false
          this.loadData()
        })
      })
    },
    toggleStatus(row) {
      updateClientCompanyStatusAPI({
        clientId: row.clientId,
        status: row.status === 1 ? 0 : 1
      }).then(() => {
        this.$message.success('状态已更新')
        this.loadData()
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
