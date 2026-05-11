<template>
  <div class="card">
    <h2>导出报告</h2>
    <el-button type="success" @click="$emit('export')" :loading="exporting">
      导出比价报告
    </el-button>
    <pre v-if="report" class="report-content">{{ report }}</pre>
  </div>
</template>

<script setup>
defineProps({
  report: { type: String, default: '' },
  exporting: { type: Boolean, default: false }
})

defineEmits(['export'])
</script>

<style scoped>
.card {
  background: white;
  border-radius: 10px;
  padding: 25px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}
.card h2 {
  font-size: 18px;
  color: #303133;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid #667eea;
}
.report-content {
  background: #f5f7fa;
  padding: 20px;
  border-radius: 8px;
  margin-top: 15px;
  white-space: pre-wrap;
  font-size: 13px;
}
</style>
