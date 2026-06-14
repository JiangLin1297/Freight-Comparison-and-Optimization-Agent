<template>
  <div class="card">
    <div class="card-header">
      <div>
        <p class="eyebrow">候选方案</p>
        <h2>比价结果</h2>
      </div>
      <div class="result-summary">
        共 {{ result.total_plans_found }} 个方案
      </div>
    </div>
    <p class="table-note">
      <span v-if="result.filtered_by_time">（已按时效要求过滤）</span>
      <el-tag v-if="sortBasis" :type="sortBasis.type" size="small">
        {{ sortBasis.text }}
      </el-tag>
      <el-tag v-if="isOverweight" type="warning" size="small">
        重量超标
      </el-tag>
    </p>

    <div class="table-wrap" v-if="result.available_plans.length > 0">
      <table class="result-table">
        <thead>
          <tr>
            <th>排名</th>
            <th>承运商</th>
            <th>方式</th>
            <th>服务</th>
            <th>评级</th>
            <th>时效</th>
            <th>成本</th>
            <th>评分</th>
            <th>明细</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="(plan, index) in sortedPlans"
            :key="plan.carrier + plan.mode + plan.service_level"
            :class="{ recommended: isRecommended(plan) }"
          >
            <td>
              <span class="rank" :class="{ top: index === 0 }">{{ index + 1 }}</span>
            </td>
            <td><strong>{{ plan.carrier }}</strong></td>
            <td>
              <el-tag :type="plan.mode === 'AIR' ? 'primary' : 'success'" size="small" effect="plain">
                {{ plan.mode === 'AIR' ? '空运' : '陆运' }}
              </el-tag>
            </td>
            <td>{{ plan.service_level === 'DTD' ? '门到门' : '门到港' }}</td>
            <td>
              <el-tag :type="getRatingType(plan.service_rating)" size="small" effect="plain">
                {{ plan.service_rating || '未评级' }}
              </el-tag>
            </td>
            <td>{{ plan.transport_days }}天</td>
            <td><strong class="cost">${{ plan.total_cost.toFixed(2) }}</strong></td>
            <td>
              <el-tag v-if="typeof plan.score === 'number'" :type="getScoreType(plan.score)" size="small" effect="plain">
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
    </div>

    <div class="empty-state" v-else>
      <p v-if="isOverweight && !result.recommended_plan">重量过重，未找到可用方案</p>
      <p v-else-if="isOverweight">重量超标，建议考虑分批运输</p>
      <p v-else>未找到匹配的运输方案</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  result: { type: Object, required: true }
})

const sortBasis = computed(() => {
  const priority = props.result.order_info?.priority
  if (priority === 'cost') {
    return { text: '按成本排序', type: 'success' }
  } else if (priority === 'time') {
    return { text: '按时效排序', type: 'danger' }
  } else {
    return { text: '按综合评分排序', type: 'primary' }
  }
})

const isOverweight = computed(() => {
  if (!props.result.available_plans) return false
  return props.result.available_plans.some(plan => !plan.is_exact_match)
})

const sortedPlans = computed(() => {
  if (!props.result.available_plans) return []

  const priority = props.result.order_info?.priority

  return [...props.result.available_plans].sort((a, b) => {
    if (priority === 'cost') {
      // 成本优先：按成本升序排序（越低越好）
      return a.total_cost - b.total_cost
    } else if (priority === 'time') {
      // 时效优先：按天数升序排序（越快越好）
      return a.transport_days - b.transport_days
    } else {
      // 均衡模式：按综合评分降序排序（分数越高越好）
      const scoreA = typeof a.score === 'number' ? a.score : 0
      const scoreB = typeof b.score === 'number' ? b.score : 0
      return scoreB - scoreA
    }
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
  border: 1px solid #d9e2ec;
  border-radius: 8px;
  padding: 18px;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.05);
}

.card-header {
  align-items: flex-start;
  display: flex;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
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

.result-summary {
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  color: #334155;
  font-size: 13px;
  font-weight: 700;
  padding: 7px 10px;
}

.table-note {
  align-items: center;
  color: #64748b;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 12px;
}

.table-wrap {
  overflow-x: auto;
}

.result-table {
  border-collapse: collapse;
  min-width: 760px;
  width: 100%;
}
.result-table th,
.result-table td {
  border-bottom: 1px solid #e2e8f0;
  padding: 11px 10px;
  text-align: left;
}
.result-table th {
  background: #f8fafc;
  color: #475569;
  font-size: 12px;
  font-weight: 700;
}
.result-table td {
  color: #334155;
  font-size: 13px;
}
.result-table tr:hover { background: #f8fafc; }
.result-table tr.recommended {
  background: #f0fdfa;
  box-shadow: inset 3px 0 0 #0f766e;
}

.rank {
  align-items: center;
  background: #e2e8f0;
  border-radius: 999px;
  color: #475569;
  display: inline-flex;
  font-size: 12px;
  font-weight: 800;
  height: 24px;
  justify-content: center;
  width: 24px;
}

.rank.top {
  background: #ccfbf1;
  color: #0f766e;
}

.cost {
  color: #0f766e;
}
.empty-state { text-align: center; padding: 40px; color: #909399; }
.weights-info {
  font-size: 12px;
  color: #0f766e;
  margin-left: 10px;
}
.score-details p {
  margin: 5px 0;
  font-size: 14px;
}
</style>
