<template>
  <el-dialog
    :visible.sync="innerVisible"
    title="修改密码"
    width="420px"
    :close-on-click-modal="false"
    @close="handleClose">
    <el-form ref="form" :model="form" :rules="rules" label-width="90px">
      <el-form-item label="旧密码" prop="oldPassword">
        <el-input v-model.trim="form.oldPassword" show-password />
      </el-form-item>
      <el-form-item label="新密码" prop="newPassword">
        <el-input v-model.trim="form.newPassword" show-password />
      </el-form-item>
    </el-form>
    <div slot="footer">
      <el-button @click="innerVisible = false">取消</el-button>
      <el-button type="primary" @click="submit">确定</el-button>
    </div>
  </el-dialog>
</template>

<script>
import { updateSelfPasswordAPI } from '@/api/admin/clientUser'

export default {
  name: 'ChangePasswordDialog',
  props: {
    visible: Boolean
  },
  data() {
    return {
      innerVisible: false,
      form: {
        oldPassword: '',
        newPassword: ''
      },
      rules: {
        oldPassword: [{ required: true, message: '请输入旧密码', trigger: 'blur' }],
        newPassword: [{ required: true, message: '请输入新密码', trigger: 'blur' }]
      }
    }
  },
  watch: {
    visible: {
      handler(val) {
        this.innerVisible = val
      },
      immediate: true
    }
  },
  methods: {
    submit() {
      this.$refs.form.validate(valid => {
        if (!valid) return
        updateSelfPasswordAPI(this.form).then(() => {
          this.$message.success('密码已更新，请重新登录')
          this.innerVisible = false
          this.$store.dispatch('LogOut').then(() => {
            window.location.reload()
          })
        })
      })
    },
    handleClose() {
      this.form = {
        oldPassword: '',
        newPassword: ''
      }
      this.$emit('update:visible', false)
    }
  }
}
</script>
