<template>
  <div class="recommend-card">
    <h3>推荐方案</h3>
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
  background: linear-gradient(135deg, #67c23a 0%, #409eff 100%);
  color: white;
  border-radius: 10px;
  padding: 25px;
  margin-top: 20px;
}
.recommend-card h3 { font-size: 20px; margin-bottom: 15px; }
.recommend-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 15px;
}
.recommend-item {
  background: rgba(255,255,255,0.2);
  padding: 15px;
  border-radius: 8px;
}
.recommend-item .label { font-size: 12px; opacity: 0.9; }
.recommend-item .value { font-size: 24px; font-weight: bold; margin-top: 5px; }
.reason-box {
  background: rgba(255,255,255,0.15);
  padding: 15px;
  border-radius: 8px;
  margin-top: 15px;
}
.reason-box .label { font-size: 12px; opacity: 0.9; }
.reason-box .content { margin-top: 8px; line-height: 1.6; }
</style>
