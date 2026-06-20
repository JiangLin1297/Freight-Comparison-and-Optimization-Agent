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

    <!-- 转运路线 -->
    <div v-if="result.transfer_routes && result.transfer_routes.length > 0" class="transfer-section">
      <div class="transfer-header">
        <el-tag type="warning" size="small" effect="dark">转运方案</el-tag>
        <span class="transfer-hint">未找到直达路线，以下为经中转港的转运方案</span>
      </div>
      <div v-for="(tr, i) in result.transfer_routes" :key="'tr-' + i" class="transfer-card">
        <div class="transfer-path">
          <span v-for="(p, j) in tr.path" :key="j">
            <el-tag size="small" :type="j === 0 ? '' : j === tr.path.length - 1 ? 'success' : 'warning'">
              {{ getPortName(p) }}
            </el-tag>
            <span v-if="j < tr.path.length - 1" class="path-arrow">→</span>
          </span>
          <span class="transfer-badge">经{{ tr.hop_count }}次转运</span>
        </div>
        <div class="transfer-meta">
          <span>总成本 <strong>${{ tr.total_cost.toFixed(2) }}</strong></span>
          <span>总耗时 <strong>{{ tr.total_estimated_days }}天</strong> (运输{{ tr.total_days }}天 + 转运{{ tr.hop_count }}天)</span>
          <span v-if="typeof tr.score === 'number'">评分 <el-tag :type="tr.score >= 0.8 ? 'success' : tr.score >= 0.6 ? 'warning' : 'danger'" size="small">{{ tr.score.toFixed(3) }}</el-tag></span>
        </div>
        <div class="transfer-legs">
          <div v-for="(leg, k) in tr.legs" :key="'leg-' + k" class="leg-row">
            <span class="leg-label">第{{ k + 1 }}段</span>
            <span>{{ getPortName(leg.from_port) }} → {{ getPortName(leg.to_port) }}</span>
            <el-tag :type="leg.mode === 'AIR' ? 'primary' : 'success'" size="small" effect="plain">
              {{ leg.mode === 'AIR' ? '空运' : '陆运' }}
            </el-tag>
            <span>{{ leg.service_level === 'DTD' ? '门到门' : '门到港' }}</span>
            <span>{{ leg.carrier }}</span>
            <span class="leg-cost">${{ leg.total_cost.toFixed(2) }}</span>
            <span>{{ leg.transport_days }}天</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 次优推荐 (fallback) -->
    <div v-if="result.fallback_transfer && (!result.transfer_routes || result.transfer_routes.length === 0)" class="fallback-section">
      <div class="transfer-header">
        <el-tag type="danger" size="small" effect="dark">次优推荐</el-tag>
        <span class="transfer-hint">{{ result.fallback_reason || '当前条件下无可用方案，以下为最接近的选项' }}</span>
      </div>
      <div class="transfer-card fallback-card">
        <div class="transfer-path">
          <span v-for="(p, j) in result.fallback_transfer.path" :key="j">
            <el-tag size="small">{{ getPortName(p) }}</el-tag>
            <span v-if="j < result.fallback_transfer.path.length - 1" class="path-arrow">→</span>
          </span>
        </div>
        <div class="transfer-meta">
          <span>总成本 <strong>${{ result.fallback_transfer.total_cost.toFixed(2) }}</strong></span>
          <span>总耗时 <strong>{{ result.fallback_transfer.total_estimated_days }}天</strong></span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { getPortName } from '../utils/portUtils.js'

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

.transfer-section { margin-top: 20px; border-top: 2px solid #f59e0b; padding-top: 14px; }
.transfer-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.transfer-hint { color: #64748b; font-size: 13px; }
.transfer-card { background: #fffbeb; border: 1px solid #fcd34d; border-radius: 8px; padding: 14px; margin-bottom: 10px; }
.transfer-path { display: flex; align-items: center; gap: 4px; flex-wrap: wrap; margin-bottom: 10px; }
.path-arrow { color: #94a3b8; font-weight: 700; margin: 0 2px; }
.transfer-badge { color: #92400e; font-size: 12px; margin-left: 8px; }
.transfer-meta { display: flex; gap: 16px; flex-wrap: wrap; color: #64748b; font-size: 13px; margin-bottom: 10px; }
.transfer-meta strong { color: #0f766e; }
.transfer-legs { border-top: 1px dashed #fcd34d; padding-top: 8px; }
.leg-row { display: flex; align-items: center; gap: 10px; padding: 6px 0; font-size: 13px; color: #475569; }
.leg-label { background: #fef3c7; color: #92400e; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; }
.leg-cost { color: #0f766e; font-weight: 700; }

.fallback-section { margin-top: 20px; border-top: 2px solid #ef4444; padding-top: 14px; }
.fallback-card { background: #fef2f2; border-color: #fca5a5; }
</style>
