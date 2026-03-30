<template>
  <div class="main">
    <div class="main-title">
      升级日志
    </div>
    <div class="main-des">
      <i class="wk wk-announcement icon" />
      <div class="content">做账快会不定期进行日常bug更新及新增功能更新。</div>
    </div>
    <div class="main-body">
      <el-timeline>
        <el-timeline-item
          v-for="(item, index) in list"
          :key="index"
          type="primary"
          color="#0052CC"
          placement="top"
          :timestamp="item.title">
          <div v-html="item.content" />
        </el-timeline-item>
      </el-timeline>
    </div>
  </div>
</template>

<script>
import request from './request'

export default {
  // Update
  name: 'Update',

  components: {},

  props: {},

  data() {
    return {
      list: []
    }
  },

  computed: {},

  watch: {},

  created() {
    this.getData()
  },

  mounted() {},

  beforeDestroy() {},

  methods: {
    getData() {
      request({
        url: '/upgradeLog',
        method: 'post'
      })
        .then((response) => {
          const res = response.data
          if (response.status === 200 && res.code === 200) {
            const resData = res.data || []
            this.list = resData
          }
        })
        .catch(() => {
        })
    }
  }
}
</script>

<style lang="scss" scoped>
@import "./style.scss";

.icon {
  color: $--color-primary;
}

.main-body {
  padding: 0 8px;

  ::v-deep .el-timeline-item {
    .el-timeline-item__timestamp {
      padding-top: 0;
      font-size: 20px;
      color: $--color-black;
    }

    .el-timeline-item__content {
      font-size: 16px;
      line-height: 1.5;
      color: $--color-text-regular;

      div {
        font-weight: normal !important;
        white-space: pre-wrap;
      }
    }
  }
}
</style>
