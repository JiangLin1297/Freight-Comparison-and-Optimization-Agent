<template>
  <div class="flow-card" v-if="visible">
    <h3 class="card-title">处理流程</h3>
    <el-steps :active="activeStep" finish-status="success" align-center>
      <el-step title="用户输入" description="订单信息或自然语言" />
      <el-step title="LLM解析" description="提取结构化数据" />
      <el-step title="数据匹配" description="筛选承运商方案" />
      <el-step title="成本计算" description="计算运输费用" />
      <el-step title="推荐方案" description="生成最优推荐" />
    </el-steps>

    <div class="step-detail" v-if="stepInfo">
      <div class="detail-icon" :class="stepInfo.status">
        <el-icon v-if="stepInfo.status === 'success'" :size="20"><Check /></el-icon>
        <el-icon v-else-if="stepInfo.status === 'process'" :size="20"><Loading /></el-icon>
        <el-icon v-else :size="20"><Clock /></el-icon>
      </div>
      <div class="detail-text">
        <span class="detail-title">{{ stepInfo.title }}</span>
        <span class="detail-desc">{{ stepInfo.description }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { Check, Loading, Clock } from '@element-plus/icons-vue'

const props = defineProps({
  step: { type: Number, default: 0 },
  result: { type: Object, default: null },
  loading: { type: Boolean, default: false }
})

const visible = ref(false)
const activeStep = ref(0)

const steps = [
  { title: '用户输入', description: '已获取订单信息', status: 'success' },
  { title: 'LLM解析', description: '自然语言已解析为结构化数据', status: 'success' },
  { title: '数据匹配', description: '正在筛选承运商方案...', status: 'process' },
  { title: '成本计算', description: '正在计算运输费用...', status: 'process' },
  { title: '推荐方案', description: '正在生成最优推荐...', status: 'process' }
]

const stepInfo = computed(() => {
  if (activeStep.value >= 0 && activeStep.value < steps.length) {
    const info = { ...steps[activeStep.value] }
    if (activeStep.value <= props.step) {
      info.status = 'success'
      if (activeStep.value === 2 && props.result) {
        info.description = `已找到 ${props.result.total_plans_found} 个方案`
      }
      if (activeStep.value === 4 && props.result?.recommended_plan) {
        info.description = `推荐 ${props.result.recommended_plan.plan.carrier}`
      }
    }
    return info
  }
  return null
})

watch(() => props.step, (val) => {
  visible.value = true
  activeStep.value = val
})

watch(() => props.loading, (val) => {
  if (val) {
    visible.value = true
  }
})
</script>

<style scoped>
.flow-card {
  background: white;
  border-radius: 10px;
  padding: 25px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}

.card-title {
  font-size: 18px;
  color: #303133;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid #667eea;
}

.step-detail {
  margin-top: 20px;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.detail-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.detail-icon.success {
  background: #67c23a;
  color: white;
}

.detail-icon.process {
  background: #409eff;
  color: white;
  animation: spin 1s linear infinite;
}

.detail-icon.wait {
  background: #909399;
  color: white;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.detail-text {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-title {
  font-weight: bold;
  color: #303133;
}

.detail-desc {
  font-size: 14px;
  color: #606266;
}
</style>
