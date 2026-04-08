<template>
  <el-dialog
    :visible.sync="innerVisible"
    title="选择用户"
    width="720px"
    :close-on-click-modal="false"
    @close="handleClose">
    <div class="toolbar">
      <el-input
        v-model.trim="keyword"
        placeholder="搜索账号/姓名"
        clearable
        @input="loadData" />
    </div>

    <el-table
      v-loading="loading"
      :data="userList"
      height="360"
      @selection-change="selectionChange">
      <el-table-column type="selection" width="55" />
      <el-table-column prop="username" label="登录账号" min-width="140" />
      <el-table-column prop="realname" label="姓名" min-width="120" />
      <el-table-column prop="phone" label="手机号" min-width="140" />
      <el-table-column label="管理员" width="100">
        <template slot-scope="{ row }">
          {{ row.isClientAdmin ? '是' : '否' }}
        </template>
      </el-table-column>
    </el-table>

    <div slot="footer">
      <el-button @click="innerVisible = false">取消</el-button>
      <el-button type="primary" @click="confirmSelect">确定</el-button>
    </div>
  </el-dialog>
</template>

<script>
import { queryClientUserSelectableListAPI } from '@/api/admin/clientUser'

export default {
  name: 'ClientUserSelectDialog',
  props: {
    visible: Boolean,
    clientId: [String, Number],
    selectedIds: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      innerVisible: false,
      loading: false,
      keyword: '',
      userList: [],
      selection: []
    }
  },
  watch: {
    visible: {
      handler(val) {
        this.innerVisible = val
        if (val) {
          this.loadData()
        }
      },
      immediate: true
    }
  },
  methods: {
    loadData() {
      if (!this.clientId) {
        this.userList = []
        return
      }
      this.loading = true
      queryClientUserSelectableListAPI({ clientId: this.clientId }).then(res => {
        const list = res.data || []
        const keyword = this.keyword
        this.userList = keyword
          ? list.filter(item => [item.username, item.realname].some(text => (text || '').includes(keyword)))
          : list
        this.loading = false
      }).catch(() => {
        this.loading = false
      })
    },
    selectionChange(list) {
      this.selection = list
    },
    confirmSelect() {
      this.$emit('confirm', this.selection)
      this.innerVisible = false
    },
    handleClose() {
      this.$emit('update:visible', false)
      this.keyword = ''
      this.selection = []
    }
  }
}
</script>

<style scoped lang="scss">
.toolbar {
  margin-bottom: 16px;
}
</style>
