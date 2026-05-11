<template>
  <div class="card">
    <h2>比价结果</h2>
    <p style="color: #909399; margin-bottom: 15px;">
      共找到 <strong style="color: #667eea">{{ result.total_plans_found }}</strong> 个可用方案
      <span v-if="result.filtered_by_time">（已按时效要求过滤）</span>
    </p>

    <table class="result-table" v-if="result.available_plans.length > 0">
      <thead>
        <tr>
          <th>承运商</th>
          <th>运输方式</th>
          <th>服务级别</th>
          <th>运输天数</th>
          <th>费率</th>
          <th>最低费用</th>
          <th>总成本</th>
          <th>计算公式</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="plan in result.available_plans"
          :key="plan.carrier + plan.mode + plan.service_level"
          :class="{ recommended: isRecommended(plan) }"
        >
          <td><strong>{{ plan.carrier }}</strong></td>
          <td>
            <el-tag :type="plan.mode === 'AIR' ? 'danger' : 'success'" size="small">
              {{ plan.mode === 'AIR' ? '空运' : '陆运' }}
            </el-tag>
          </td>
          <td>{{ plan.service_level === 'DTD' ? '门到门' : '门到港' }}</td>
          <td>{{ plan.transport_days }}天</td>
          <td>{{ plan.rate }}</td>
          <td>${{ plan.min_cost.toFixed(2) }}</td>
          <td><strong style="color: #667eea">${{ plan.total_cost.toFixed(2) }}</strong></td>
          <td style="font-size: 12px; color: #909399">{{ plan.cost_formula }}</td>
        </tr>
      </tbody>
    </table>

    <div class="empty-state" v-else>
      <p>未找到匹配的运输方案</p>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  result: { type: Object, required: true }
})

const isRecommended = (plan) => {
  const recommended = props.result.recommended_plan?.plan
  return recommended && plan.carrier === recommended.carrier && plan.mode === recommended.mode
}
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
.result-table { width: 100%; border-collapse: collapse; margin-top: 15px; }
.result-table th, .result-table td { padding: 12px; text-align: left; border-bottom: 1px solid #ebeef5; }
.result-table th { background: #f5f7fa; font-weight: bold; color: #303133; }
.result-table tr:hover { background: #f5f7fa; }
.result-table tr.recommended { background: #f0f9eb; }
.empty-state { text-align: center; padding: 40px; color: #909399; }
</style>
