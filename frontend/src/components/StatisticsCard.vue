<template>
  <div class="card">
    <div class="card-title">
      <span>数据概览</span>
      <small>当前费率库</small>
    </div>
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
  border: 1px solid #d9e2ec;
  border-radius: 8px;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.05);
  display: grid;
  grid-template-columns: 160px minmax(0, 1fr);
  gap: 16px;
  padding: 16px;
}

.card-title {
  align-items: flex-start;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding-right: 16px;
}

.card-title span {
  color: #1f2937;
  font-size: 16px;
  font-weight: 700;
}

.card-title small {
  color: #64748b;
  font-size: 12px;
  margin-top: 4px;
}
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 10px;
}
.stat-item {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 12px;
}
.stat-item .number {
  color: #0f766e;
  font-size: 22px;
  font-weight: bold;
}
.stat-item .label {
  font-size: 12px;
  color: #64748b;
  margin-top: 5px;
}

@media (max-width: 720px) {
  .card {
    grid-template-columns: 1fr;
  }

  .card-title {
    border-right: 0;
    border-bottom: 1px solid #e2e8f0;
    padding: 0 0 12px;
  }
}
</style>
