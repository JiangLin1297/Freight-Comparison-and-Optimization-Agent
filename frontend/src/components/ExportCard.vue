<template>
  <div class="card">
    <div class="card-header">
      <div>
        <p class="eyebrow">交付物</p>
        <h2>导出报告</h2>
      </div>
    </div>
    <el-button type="primary" plain @click="$emit('export')" :loading="exporting">
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
  border: 1px solid #d9e2ec;
  border-radius: 8px;
  padding: 18px;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.05);
}

.card-header {
  margin-bottom: 14px;
}

.card h2 {
  color: #1f2937;
  font-size: 18px;
}

.eyebrow {
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 4px;
}
.report-content {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  padding: 20px;
  border-radius: 6px;
  margin-top: 15px;
  white-space: pre-wrap;
  font-size: 13px;
}
</style>
