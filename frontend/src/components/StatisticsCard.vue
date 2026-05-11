<template>
  <div class="card">
    <h2>数据概览</h2>
    <div class="stats-grid">
      <div class="stat-item">
        <div class="number">{{ statistics.total_records || 0 }}</div>
        <div class="label">报价记录</div>
      </div>
      <div class="stat-item">
        <div class="number">{{ statistics.carriers?.length || 0 }}</div>
        <div class="label">承运商</div>
      </div>
      <div class="stat-item">
        <div class="number">{{ statistics.orig_ports?.length || 0 }}</div>
        <div class="label">起运港</div>
      </div>
      <div class="stat-item">
        <div class="number">{{ statistics.transport_modes?.length || 0 }}</div>
        <div class="label">运输方式</div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  statistics: { type: Object, default: () => ({}) }
})
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
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 15px;
}
.stat-item {
  text-align: center;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
}
.stat-item .number {
  font-size: 24px;
  font-weight: bold;
  color: #667eea;
}
.stat-item .label {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}
</style>
