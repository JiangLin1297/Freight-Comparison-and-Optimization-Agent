<template>
  <div class="container">
    <AppHeader />
    <StatisticsCard :statistics="statistics" />
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

const form = ref({
  weight: 100,
  orig_port: 'PORT08',
  dest_port: 'PORT09',
  max_days: null
})

const ports = ref({ orig_ports: [], dest_ports: [] })
const statistics = ref({})
const result = ref(null)
const report = ref('')
const loading = ref(false)
const exporting = ref(false)

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

const handleCompare = async () => {
  if (!form.value.weight || !form.value.orig_port || !form.value.dest_port) {
    ElMessage.warning('请填写必填项')
    return
  }

  loading.value = true
  result.value = null
  report.value = ''

  try {
    const res = await axios.post('/api/compare', {
      weight: form.value.weight,
      orig_port: form.value.orig_port,
      dest_port: form.value.dest_port,
      max_days: form.value.max_days || null
    })
    result.value = res.data
    ElMessage.success(`找到 ${res.data.total_plans_found} 个可用方案`)
  } catch (e) {
    ElMessage.error('比价失败: ' + (e.response?.data?.detail || e.message))
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
      max_days: form.value.max_days || null
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
