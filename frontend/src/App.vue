<template>
  <div class="container">
    <AppHeader />
    <StatisticsCard :statistics="statistics" />

    <!-- 智能语音输入 -->
    <NLInput @parsed="handleNLParsed" />

    <!-- 流程可视化 -->
    <FlowVisualization :step="flowStep" :result="result" :loading="loading" />

    <CompareForm
      v-model:form="form"
      :ports="ports"
      :loading="loading"
      @compare="handleCompare"
    />
    <ResultTable v-if="result" :result="result" />
    <RecommendCard v-if="result?.recommended_plan" :plan="result.recommended_plan" />
    <ExportCard
      v-if="result"
      :report="report"
      :exporting="exporting"
      @export="handleExport"
    />

    <!-- 聊天面板 -->
    <ChatPanel />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import AppHeader from './components/AppHeader.vue'
import StatisticsCard from './components/StatisticsCard.vue'
import CompareForm from './components/CompareForm.vue'
import ResultTable from './components/ResultTable.vue'
import RecommendCard from './components/RecommendCard.vue'
import ExportCard from './components/ExportCard.vue'
import NLInput from './components/NLInput.vue'
import FlowVisualization from './components/FlowVisualization.vue'
import ChatPanel from './components/ChatPanel.vue'

const form = ref({
  weight: 100,
  orig_port: 'PORT08',
  dest_port: 'PORT09',
  max_days: null,
  priority: null
})

const ports = ref({ orig_ports: [], dest_ports: [] })
const statistics = ref({})
const result = ref(null)
const report = ref('')
const loading = ref(false)
const exporting = ref(false)
const flowStep = ref(0)

const loadData = async () => {
  try {
    const [portsRes, statsRes] = await Promise.all([
      axios.get('/api/ports'),
      axios.get('/api/statistics')
    ])
    ports.value = portsRes.data
    statistics.value = statsRes.data
  } catch (e) {
    console.error('加载数据失败:', e)
  }
}

// 自然语言解析后填充表单
const handleNLParsed = (data) => {
  if (data.weight) form.value.weight = data.weight
  if (data.orig_port) form.value.orig_port = data.orig_port
  if (data.dest_port) form.value.dest_port = data.dest_port
  if (data.max_days) form.value.max_days = data.max_days
  if (data.priority) form.value.priority = data.priority
  flowStep.value = 1

  // 显示优先级提示
  if (data.priority === 'time') {
    ElMessage.info('已识别为时效优先模式，将优先推荐最快的方案')
  } else if (data.priority === 'cost') {
    ElMessage.info('已识别为成本优先模式，将优先推荐最便宜的方案')
  }

  // 如果信息完整，自动触发推荐
  if (data.weight && data.orig_port && data.dest_port) {
    setTimeout(() => {
      handleCompare()
    }, 500) // 延迟500ms，让用户看到优先级提示
  }
}

const handleCompare = async () => {
  if (!form.value.weight || !form.value.orig_port || !form.value.dest_port) {
    ElMessage.warning('请填写必填项')
    return
  }

  loading.value = true
  result.value = null
  report.value = ''
  flowStep.value = 2

  try {
    const requestData = {
      weight: form.value.weight,
      orig_port: form.value.orig_port,
      dest_port: form.value.dest_port,
      max_days: form.value.max_days || null,
      priority: form.value.priority || null
    }
    const res = await axios.post('/api/compare', requestData)
    result.value = res.data
    flowStep.value = 4

    // 显示推荐模式提示
    const priorityText = form.value.priority === 'time' ? '（时效优先）' :
                        form.value.priority === 'cost' ? '（成本优先）' : '（均衡模式）'
    ElMessage.success(`已为您推荐最优方案${priorityText}`)
  } catch (e) {
    ElMessage.error('推荐失败: ' + (e.response?.data?.detail || e.message))
    flowStep.value = 2
  } finally {
    loading.value = false
  }
}

const handleExport = async () => {
  exporting.value = true
  try {
    const res = await axios.post('/api/export', {
      weight: form.value.weight,
      orig_port: form.value.orig_port,
      dest_port: form.value.dest_port,
      max_days: form.value.max_days || null,
      priority: form.value.priority || null
    })
    report.value = res.data.report
    ElMessage.success('报告生成成功')
  } catch (e) {
    ElMessage.error('导出失败')
  } finally {
    exporting.value = false
  }
}

onMounted(loadData)
</script>

<style>
* { margin: 0; padding: 0; box-sizing: border-box; }
body { font-family: 'Microsoft YaHei', sans-serif; background: #f5f7fa; }
.container { max-width: 1200px; margin: 0 auto; padding: 20px; }
</style>
