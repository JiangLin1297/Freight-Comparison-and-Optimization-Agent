<template>
  <div class="card">
    <h2>比价结果</h2>
    <p style="color: #909399; margin-bottom: 15px;">
      共找到 <strong style="color: #667eea">{{ result.total_plans_found }}</strong> 个可用方案
      <span v-if="result.filtered_by_time">（已按时效要求过滤）</span>
      <span v-if="result.scoring_weights" class="weights-info">
        | 评分权重：成本{{ (result.scoring_weights.cost_weight * 100).toFixed(0) }}%
        时效{{ (result.scoring_weights.time_weight * 100).toFixed(0) }}%
        服务{{ (result.scoring_weights.service_weight * 100).toFixed(0) }}%
      </span>
    </p>

    <table class="result-table" v-if="result.available_plans.length > 0">
      <thead>
        <tr>
          <th>排名</th>
          <th>承运商</th>
          <th>运输方式</th>
          <th>服务级别</th>
          <th>服务评级</th>
          <th>运输天数</th>
          <th>总成本</th>
          <th>综合评分</th>
          <th>评分明细</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="(plan, index) in sortedPlans"
          :key="plan.carrier + plan.mode + plan.service_level"
          :class="{ recommended: isRecommended(plan) }"
        >
          <td>
            <el-tag v-if="index === 0" type="success" size="small">1</el-tag>
            <el-tag v-else-if="index === 1" type="warning" size="small">2</el-tag>
            <el-tag v-else-if="index === 2" type="info" size="small">3</el-tag>
            <span v-else>{{ index + 1 }}</span>
          </td>
          <td><strong>{{ plan.carrier }}</strong></td>
          <td>
            <el-tag :type="plan.mode === 'AIR' ? 'danger' : 'success'" size="small">
              {{ plan.mode === 'AIR' ? '空运' : '陆运' }}
            </el-tag>
          </td>
          <td>{{ plan.service_level === 'DTD' ? '门到门' : '门到港' }}</td>
          <td>
            <el-tag :type="getRatingType(plan.service_rating)" size="small">
              {{ plan.service_rating || '未评级' }}
            </el-tag>
          </td>
          <td>{{ plan.transport_days }}天</td>
          <td><strong style="color: #667eea">${{ plan.total_cost.toFixed(2) }}</strong></td>
          <td>
            <el-tag v-if="typeof plan.score === 'number'" :type="getScoreType(plan.score)" size="small" effect="dark">
              {{ plan.score.toFixed(3) }}
            </el-tag>
            <span v-else>-</span>
          </td>
          <td>
            <el-popover v-if="plan.score_details" placement="left" :width="300" trigger="hover">
              <template #reference>
                <el-button size="small" text type="primary">详情</el-button>
              </template>
              <div class="score-details">
                <p><strong>评分明细：</strong></p>
                <p>成本得分：{{ plan.score_details.cost_score.toFixed(3) }}</p>
                <p>时效得分：{{ plan.score_details.time_score.toFixed(3) }}</p>
                <p>服务得分：{{ plan.score_details.service_score.toFixed(3) }}</p>
                <el-divider />
                <p><strong>权重配置：</strong></p>
                <p>成本：{{ (plan.score_details.weights.cost * 100).toFixed(0) }}%</p>
                <p>时效：{{ (plan.score_details.weights.time * 100).toFixed(0) }}%</p>
                <p>服务：{{ (plan.score_details.weights.service * 100).toFixed(0) }}%</p>
              </div>
            </el-popover>
            <span v-else>-</span>
          </td>
        </tr>
      </tbody>
    </table>

    <div class="empty-state" v-else>
      <p>未找到匹配的运输方案</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  result: { type: Object, required: true }
})

const sortedPlans = computed(() => {
  if (!props.result.available_plans) return []
  // 按评分降序排序（确保所有方案都有评分）
  return [...props.result.available_plans].sort((a, b) => {
    const scoreA = typeof a.score === 'number' ? a.score : 0
    const scoreB = typeof b.score === 'number' ? b.score : 0
    return scoreB - scoreA
  })
})

const isRecommended = (plan) => {
  const recommended = props.result.recommended_plan?.plan
  return recommended && plan.carrier === recommended.carrier && plan.mode === recommended.mode
}

const getRatingType = (rating) => {
  const types = { 'A': 'success', 'B': 'success', 'C': 'warning', 'D': 'danger', 'E': 'danger' }
  return types[rating] || 'info'
}

const getScoreType = (score) => {
  if (score >= 0.8) return 'success'
  if (score >= 0.6) return 'warning'
  return 'danger'
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
.weights-info {
  font-size: 12px;
  color: #67c23a;
  margin-left: 10px;
}
.score-details p {
  margin: 5px 0;
  font-size: 14px;
}
</style>
