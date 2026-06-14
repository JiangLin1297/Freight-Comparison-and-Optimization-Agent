<template>
  <div class="recommend-card">
    <div class="recommend-header">
      <div>
        <p class="eyebrow">推荐方案</p>
        <h3>{{ plan.plan.carrier }}</h3>
      </div>
      <el-tag type="success" effect="plain">Top Match</el-tag>
    </div>
    <div class="recommend-info">
      <div class="recommend-item">
        <div class="label">承运商</div>
        <div class="value">{{ plan.plan.carrier }}</div>
      </div>
      <div class="recommend-item">
        <div class="label">运输方式</div>
        <div class="value">{{ plan.plan.mode === 'AIR' ? '空运' : '陆运' }}</div>
      </div>
      <div class="recommend-item">
        <div class="label">服务级别</div>
        <div class="value">{{ plan.plan.service_level === 'DTD' ? '门到门' : '门到港' }}</div>
      </div>
      <div class="recommend-item">
        <div class="label">运输天数</div>
        <div class="value">{{ plan.plan.transport_days }}天</div>
      </div>
      <div class="recommend-item">
        <div class="label">总成本</div>
        <div class="value">${{ plan.plan.total_cost.toFixed(2) }}</div>
      </div>
    </div>
    <div class="reason-box">
      <div class="label">推荐理由</div>
      <div class="content">{{ plan.reason }}</div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  plan: { type: Object, required: true }
})
</script>

<style scoped>
.recommend-card {
  background: #ffffff;
  border: 1px solid #d9e2ec;
  border-radius: 8px;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.05);
  color: #1f2937;
  padding: 18px;
}

.recommend-header {
  align-items: flex-start;
  display: flex;
  justify-content: space-between;
  margin-bottom: 14px;
}

.eyebrow {
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 4px;
}

.recommend-card h3 {
  color: #0f766e;
  font-size: 24px;
}
.recommend-info {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.recommend-item {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  padding: 12px;
}
.recommend-item .label {
  color: #64748b;
  font-size: 12px;
}
.recommend-item .value {
  color: #1e293b;
  font-size: 20px;
  font-weight: bold;
  margin-top: 5px;
}
.reason-box {
  background: #f8fafc;
  border-left: 3px solid #0f766e;
  padding: 12px 14px;
  border-radius: 6px;
  margin-top: 15px;
}
.reason-box .label {
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
}
.reason-box .content {
  color: #334155;
  font-size: 14px;
  margin-top: 8px;
  line-height: 1.6;
}

@media (max-width: 720px) {
  .recommend-info {
    grid-template-columns: 1fr;
  }
}
</style>
