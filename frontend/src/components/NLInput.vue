<template>
  <div class="nl-input-card">
    <div class="card-heading">
      <div>
        <h3 class="card-title">Agent 需求输入</h3>
        <p class="card-desc">用一句话描述运输需求，系统会解析、追问并触发比价。</p>
      </div>
      <div class="status-tags">
        <el-tag v-if="!connectionStatus.online" type="danger" effect="dark">
          ⚠ 网络未连接
        </el-tag>
        <el-tag v-else-if="!connectionStatus.llm" type="warning" effect="dark">
          ⚠ LLM未连接
        </el-tag>
        <el-tag v-if="parsing" type="primary" effect="plain">处理中</el-tag>
        <el-tag v-else-if="sessionId" type="warning" effect="plain">等待补充</el-tag>
        <el-tag v-else-if="connectionStatus.online && connectionStatus.llm" type="success" effect="plain">Agent 就绪</el-tag>
        <el-tag v-else type="info" effect="plain">本地解析模式</el-tag>
      </div>
    </div>

    <!-- 离线模式提示 -->
    <div v-if="!connectionStatus.online || !connectionStatus.llm" class="offline-notice">
      <span class="offline-icon">⚡</span>
      <span v-if="!connectionStatus.online">目前未有网络连接，已切换至本地解析模式（仅支持基本关键词识别）</span>
      <span v-else>LLM未连接，已切换至本地解析模式（仅支持基本关键词识别）</span>
    </div>

    <div class="input-area">
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="3"
        :placeholder="sessionId ? '请补充缺失的信息，例如：从大连出发' : '例如：从大连运100kg到厦门，越快越好'"
        :disabled="parsing"
      />
      <el-button
        type="primary"
        :loading="parsing"
        @click="handleParse"
        class="parse-btn"
      >
        {{ parsing ? '解析中...' : (sessionId ? '继续' : '智能解析') }}
      </el-button>
      <el-button
        v-if="sessionId"
        type="warning"
        @click="resetSession"
        class="reset-btn"
      >
        重新开始
      </el-button>
    </div>

    <div class="example-row">
      <button type="button" @click="inputText = '我要运到PORT09，100公斤'">缺起运港</button>
      <button type="button" @click="inputText = '从大连运100kg到厦门，越快越好'">时效优先</button>
      <button type="button" @click="inputText = '从PORT02到PORT99，50kg'">异常港口</button>
    </div>

    <div v-if="parsing" class="live-progress" aria-live="polite">
      <div class="progress-header">
        <span>{{ activeProgress.title }}</span>
        <strong>{{ activeProgress.percent }}%</strong>
      </div>
      <div class="progress-track">
        <span :style="{ width: activeProgress.percent + '%' }"></span>
      </div>
      <p>{{ activeProgress.desc }}</p>
      <div class="progress-skeleton">
        <span></span>
        <span></span>
        <span></span>
      </div>
    </div>

    <!-- Agent 反馈显示 -->
    <div v-if="agentMessage && replyType !== 'general'" class="cot-analysis">
      <div class="cot-header">
        <span class="cot-title">AI 反馈</span>
        <el-tag v-if="replyType === 'recommendation'" type="success" size="small">推荐</el-tag>
        <el-tag v-else-if="replyType === 'clarification'" type="warning" size="small">待补充</el-tag>
        <el-tag v-else-if="replyType === 'no_result'" type="danger" size="small">无结果</el-tag>
        <el-tag v-else :type="confidenceType" size="small">{{ confidenceLabel }}</el-tag>
      </div>
      <div class="cot-content">
        <div class="cot-step">
          <span class="step-value">{{ agentMessage }}</span>
        </div>
      </div>
    </div>

    <!-- 下一步建议 -->
    <div v-if="nextActions.length > 0" class="guidance-msg">
      <div class="guidance-header">下一步建议</div>
      <div class="guidance-content">
        <ul style="margin:0;padding-left:20px">
          <li v-for="(action, idx) in nextActions" :key="idx">{{ action }}</li>
        </ul>
      </div>
    </div>

    <!-- 解析结果预览 -->
    <div v-if="parsedData" class="parsed-preview">
      <div class="preview-header">
        <span class="preview-title">解析结果</span>
        <el-button type="success" size="small" @click="handleConfirm" :disabled="!isComplete">
          {{ isComplete ? '确认填充' : (routeInvalid ? '路线无效' : '信息不完整') }}
        </el-button>
      </div>
      <div class="preview-grid">
        <div class="preview-item" :class="{ 'missing': !parsedData.weight }">
          <span class="label">货物重量</span>
          <span class="value">{{ parsedData.weight ? parsedData.weight + ' kg' : '待补充' }}</span>
        </div>
        <div class="preview-item" :class="{ 'missing': !parsedData.orig_port }">
          <span class="label">起运港</span>
          <span class="value">{{ parsedData.orig_port || '待补充' }}</span>
        </div>
        <div class="preview-item" :class="{ 'missing': !parsedData.dest_port }">
          <span class="label">目的港</span>
          <span class="value">{{ parsedData.dest_port || '待补充' }}</span>
        </div>
        <div class="preview-item" :class="{ 'missing': !parsedData.max_days }">
          <span class="label">最大天数</span>
          <span class="value">{{ parsedData.max_days ? parsedData.max_days + ' 天' : '未指定' }}</span>
        </div>
        <div class="preview-item" :class="{ 'highlight': parsedData.priority }">
          <span class="label">优先模式</span>
          <span class="value">
            <el-tag v-if="parsedData.priority === 'time'" type="danger" size="small" effect="dark">
              时效优先
            </el-tag>
            <el-tag v-else-if="parsedData.priority === 'cost'" type="success" size="small" effect="dark">
              成本优先
            </el-tag>
            <el-tag v-else type="info" size="small">
              均衡模式
            </el-tag>
          </span>
        </div>
      </div>
    </div>

    <div v-if="routeInvalid" class="error-msg">
      起运港和目的港不能相同，请补充一个不同的起运港或目的港。
    </div>

    <!-- 错误提示 -->
    <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const props = defineProps({
  authHeaders: { type: Object, default: () => ({}) },
  connectionStatus: {
    type: Object,
    default: () => ({ online: true, llm: false, error: '' })
  },
})

const emit = defineEmits(['parsed', 'agent-update', 'processing'])

const inputText = ref('')
const parsing = ref(false)
const parsedData = ref(null)
const errorMsg = ref('')
const sessionId = ref(null)
const guidance = ref('')
const missingFields = ref([])
const replyType = ref('')
const agentMessage = ref('')
const nextActions = ref([])
const progressStage = ref(0)
const isOfflineMode = ref(false)
const offlineMessage = ref('')

const progressStages = [
  { title: '理解运输需求', desc: '正在识别重量、港口方向和时效偏好。', percent: 24 },
  { title: '校验必要字段', desc: '正在检查是否需要追问缺失信息。', percent: 48 },
  { title: '匹配费率数据', desc: '正在准备调用费率表和推荐规则。', percent: 72 },
  { title: '生成反馈', desc: '正在整理解释和下一步建议。', percent: 88 }
]

let progressTimer = null

const activeProgress = computed(() => progressStages[progressStage.value] || progressStages[0])

const confidenceType = computed(() => {
  if (missingFields.value.length === 0 && parsedData.value) return 'success'
  if (missingFields.value.length <= 1) return 'warning'
  return 'danger'
})

const confidenceLabel = computed(() => {
  if (missingFields.value.length === 0 && parsedData.value) return '完整'
  if (missingFields.value.length <= 1) return '缺字段'
  return '信息不足'
})

const isComplete = computed(() => {
  return parsedData.value &&
    parsedData.value.weight &&
    parsedData.value.orig_port &&
    parsedData.value.dest_port &&
    parsedData.value.orig_port !== parsedData.value.dest_port
})

const routeInvalid = computed(() => {
  return parsedData.value?.orig_port &&
    parsedData.value?.dest_port &&
    parsedData.value.orig_port === parsedData.value.dest_port
})

// 检测是否应该使用离线模式
const shouldUseOfflineMode = computed(() => {
  return !props.connectionStatus.online || !props.connectionStatus.llm
})

// 离线模式下的简单解析（使用正则表达式）
const parseOffline = (text) => {
  const result = {
    weight: null,
    orig_port: null,
    dest_port: null,
    max_days: null,
    priority: null
  }

  // 提取重量
  const weightMatch = text.match(/(\d+(?:\.\d+)?)\s*(?:kg|公斤|千克)/i)
  if (weightMatch) {
    result.weight = parseFloat(weightMatch[1])
  }

  const tonMatch = text.match(/(\d+(?:\.\d+)?)\s*(?:吨|tons?)/i)
  if (tonMatch) {
    result.weight = parseFloat(tonMatch[1]) * 1000
  }

  // 港口名称映射
  const portMap = {
    '上海': 'PORT02', '深圳': 'PORT03', '广州': 'PORT04',
    '宁波': 'PORT05', '青岛': 'PORT06', '天津': 'PORT07',
    '大连': 'PORT08', '厦门': 'PORT09', '香港': 'PORT10',
    '釜山': 'PORT11'
  }

  // 提取PORT代码
  const portCodes = text.match(/PORT\s*(\d{1,2})/gi)
  if (portCodes && portCodes.length >= 2) {
    result.orig_port = portCodes[0].toUpperCase().replace(/\s/g, '')
    result.dest_port = portCodes[1].toUpperCase().replace(/\s/g, '')
  } else if (portCodes && portCodes.length === 1) {
    // 根据方向词判断
    if (/到|运到|发到/.test(text)) {
      result.dest_port = portCodes[0].toUpperCase().replace(/\s/g, '')
    } else {
      result.orig_port = portCodes[0].toUpperCase().replace(/\s/g, '')
    }
  }

  // 提取中文港口名
  if (!result.orig_port || !result.dest_port) {
    const routeMatch = text.match(/从\s*(\S+)\s*(?:.*?到)\s*(\S+)/)
    if (routeMatch) {
      const origName = routeMatch[1]
      const destName = routeMatch[2]
      for (const [name, code] of Object.entries(portMap)) {
        if (origName.includes(name) && !result.orig_port) result.orig_port = code
        if (destName.includes(name) && !result.dest_port) result.dest_port = code
      }
    }

    // 单独匹配"到X"
    if (!result.dest_port) {
      const destMatch = text.match(/(?:运|发|送|寄)?到\s*(\S{2,})/)
      if (destMatch) {
        for (const [name, code] of Object.entries(portMap)) {
          if (destMatch[1].includes(name)) {
            result.dest_port = code
            break
          }
        }
      }
    }

    // 单独匹配"从X"
    if (!result.orig_port) {
      const origMatch = text.match(/从\s*(\S{2,})\s*(?:出发|发货|起运)?/)
      if (origMatch) {
        for (const [name, code] of Object.entries(portMap)) {
          if (origMatch[1].includes(name)) {
            result.orig_port = code
            break
          }
        }
      }
    }
  }

  // 提取天数
  const daysMatch = text.match(/(\d+)\s*(?:天|日)/)
  if (daysMatch) {
    result.max_days = parseInt(daysMatch[1])
  }

  // 识别优先级
  if (/尽快|越快越好|加急|紧急|最快/.test(text)) {
    result.priority = 'time'
  } else if (/最省钱|越便宜越好|成本优先|最便宜|省钱/.test(text)) {
    result.priority = 'cost'
  }

  return result
}

const handleParse = async () => {
  if (!inputText.value.trim()) {
    ElMessage.warning('请输入运输需求描述')
    return
  }

  parsing.value = true
  errorMsg.value = ''
  progressStage.value = 0
  isOfflineMode.value = false
  offlineMessage.value = ''
  emit('processing', true) // 通知父组件开始处理

  const userMsg = inputText.value.trim()
  emit('agent-update', {
    reply_type: 'processing',
    intent: sessionId.value ? 'compare_freight' : 'detecting',
    missing_fields: [],
    order: parsedData.value,
    message: sessionId.value ? '正在合并补充信息...' : '正在解析自然语言需求...',
    parse_source: null,
    feedback_source: null
  })
  progressTimer = window.setInterval(() => {
    if (progressStage.value < progressStages.length - 1) {
      progressStage.value += 1
    }
  }, 1400)

  // 检测网络和LLM状态，决定是否使用离线模式
  if (shouldUseOfflineMode.value) {
    // 离线模式：使用正则解析
    isOfflineMode.value = true
    if (!props.connectionStatus.online) {
      offlineMessage.value = '⚠ 目前未有网络连接，使用本地解析模式'
    } else {
      offlineMessage.value = '⚠ LLM未连接，使用本地解析模式'
    }

    // 模拟解析延迟
    await new Promise(resolve => setTimeout(resolve, 500))

    const offlineResult = parseOffline(userMsg)

    // 计算缺失字段
    const missing = []
    if (!offlineResult.weight) missing.push('weight')
    if (!offlineResult.orig_port) missing.push('orig_port')
    if (!offlineResult.dest_port) missing.push('dest_port')

    if (missing.length > 0) {
      // 信息不完整
      const fieldCn = { weight: '货物重量', orig_port: '起运港', dest_port: '目的港' }
      const missingCn = missing.map(f => fieldCn[f] || f)

      parsedData.value = offlineResult
      missingFields.value = missing
      replyType.value = 'clarification'
      agentMessage.value = `已识别部分信息。还需要补充：${missingCn.join('、')}。`
      nextActions.value = [`请提供${missingCn.join('、')}`]

      emit('agent-update', {
        reply_type: 'clarification',
        intent: 'compare_freight',
        missing_fields: missing,
        order: offlineResult,
        message: agentMessage.value,
        parse_source: 'offline_regex',
        feedback_source: null
      })

      ElMessage.warning(`信息不完整，缺少：${missingCn.join('、')}`)
    } else {
      // 信息完整
      parsedData.value = offlineResult
      missingFields.value = []
      replyType.value = 'recommendation'
      agentMessage.value = `已识别：${offlineResult.weight}kg，${offlineResult.orig_port} → ${offlineResult.dest_port}`
      nextActions.value = []

      if (offlineResult.priority === 'time') {
        agentMessage.value += '（时效优先）'
      } else if (offlineResult.priority === 'cost') {
        agentMessage.value += '（成本优先）'
      }

      emit('parsed', offlineResult)
      emit('agent-update', {
        reply_type: 'recommendation',
        intent: 'compare_freight',
        missing_fields: [],
        order: offlineResult,
        message: agentMessage.value,
        parse_source: 'offline_regex',
        feedback_source: null
      })

      ElMessage.success('解析完成（本地模式）')
    }

    parsing.value = false
    if (progressTimer) {
      window.clearInterval(progressTimer)
      progressTimer = null
    }
    inputText.value = ''
    return
  }

  try {
    const { data } = await axios.post('/api/agentic_chat', {
      message: inputText.value,
      session_id: sessionId.value || null
    }, { headers: props.authHeaders })
    emit('agent-update', { ...data, _userText: userMsg })

    const rt = data.reply_type

    if (rt === 'error') {
      errorMsg.value = data.message || '请求失败'
      ElMessage.error(data.message || '请求失败')
    } else if (rt === 'clarification') {
      // 缺字段 → 保存 session，显示追问
      sessionId.value = data.session_id || null
      parsedData.value = data.order || {}
      missingFields.value = data.missing_fields || []
      guidance.value = data.message || ''
      agentMessage.value = data.message || ''
      nextActions.value = data.next_actions || []
      replyType.value = 'clarification'

      // 将已解析的部分订单数据同步到表单（避免覆盖已有字段）
      if (data.order) {
        emit('parsed', data.order)
      }

      ElMessage.info('信息不完整，请补充缺失内容')
    } else if (rt === 'recommendation') {
      // 完整 → 清除 session，填充表单
      sessionId.value = null
      parsedData.value = data.order || {}
      missingFields.value = []
      guidance.value = ''
      agentMessage.value = data.message || ''
      nextActions.value = data.next_actions || []
      replyType.value = 'recommendation'

      emit('parsed', data.order || {})
      const priority = (data.order || {}).priority
      const priorityText = priority === 'time' ? '（时效优先）' :
                          priority === 'cost' ? '（成本优先）' : ''
      ElMessage.success(`解析完成，已填充到表单${priorityText}`)
    } else if (rt === 'no_result') {
      parsedData.value = data.order || {}
      missingFields.value = data.missing_fields || []
      guidance.value = data.message || ''
      agentMessage.value = data.message || ''
      nextActions.value = data.next_actions || []
      replyType.value = 'no_result'

      ElMessage.warning('未找到可用方案')
    } else {
      // general / 其他
      sessionId.value = data.session_id || null
      agentMessage.value = data.message || ''
      replyType.value = 'general'

      if ((data.order || {}).weight || (data.order || {}).orig_port || (data.order || {}).dest_port) {
        parsedData.value = data.order || {}
      }
    }
  } catch (err) {
    let errMsg = '解析失败'
    if (err.response?.data) {
      const errData = err.response.data
      if (typeof errData === 'string') {
        errMsg = errData
      } else if (errData.detail) {
        errMsg = typeof errData.detail === 'string' ? errData.detail : JSON.stringify(errData.detail)
      } else {
        errMsg = JSON.stringify(errData)
      }
    } else if (err.message) {
      errMsg = err.message
    }
    errorMsg.value = errMsg
  } finally {
    if (progressTimer) {
      window.clearInterval(progressTimer)
      progressTimer = null
    }
    parsing.value = false
    inputText.value = ''
    emit('processing', false) // 通知父组件处理完成
  }
}

const handleConfirm = () => {
  if (parsedData.value && isComplete.value) {
    emit('parsed', parsedData.value)
    const priorityText = parsedData.value.priority === 'time' ? '（时效优先）' :
                        parsedData.value.priority === 'cost' ? '（成本优先）' : ''
    ElMessage.success(`已填充到表单${priorityText}`)
    resetSession()
  } else {
    ElMessage.warning('请先补充完整信息')
  }
}

const resetSession = () => {
  sessionId.value = null
  parsedData.value = null
  guidance.value = ''
  missingFields.value = []
  errorMsg.value = ''
  replyType.value = ''
  agentMessage.value = ''
  nextActions.value = []
  emit('agent-update', null)
}
</script>

<style scoped>
.nl-input-card {
  background: #ffffff;
  border: 1px solid #d9e2ec;
  border-radius: 8px;
  padding: 18px;
}

.card-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.status-tags {
  display: flex;
  gap: 6px;
  flex-wrap: wrap;
  justify-content: flex-end;
}

.offline-notice {
  background: #fff7ed;
  border: 1px solid #fdba74;
  border-radius: 6px;
  padding: 10px 14px;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #c2410c;
}

.offline-icon {
  font-size: 16px;
}

.card-title {
  font-size: 18px;
  color: #1f2d3d;
  margin-bottom: 4px;
}

.card-desc {
  font-size: 14px;
  color: #909399;
  margin-bottom: 15px;
}

.input-area {
  display: flex;
  gap: 10px;
  align-items: flex-start;
}

.parse-btn {
  min-height: 76px;
  padding: 12px 22px;
}

.reset-btn {
  min-height: 76px;
}

.example-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
}

.example-row button {
  border: 1px solid #cbd5e1;
  background: #f8fafc;
  color: #475569;
  border-radius: 999px;
  padding: 5px 10px;
  font-size: 12px;
  cursor: pointer;
}

.live-progress {
  background: #f8fafc;
  border: 1px solid #dbeafe;
  border-radius: 8px;
  margin-top: 12px;
  padding: 12px;
}

.progress-header {
  align-items: center;
  color: #1e293b;
  display: flex;
  font-size: 13px;
  font-weight: 700;
  justify-content: space-between;
  margin-bottom: 8px;
}

.progress-header strong {
  color: #2563eb;
  font-size: 12px;
}

.progress-track {
  background: #e2e8f0;
  border-radius: 999px;
  height: 6px;
  overflow: hidden;
}

.progress-track span {
  background: #2563eb;
  border-radius: inherit;
  display: block;
  height: 100%;
  transition: width 240ms ease;
}

.live-progress p {
  color: #64748b;
  font-size: 12px;
  line-height: 1.5;
  margin-top: 8px;
}

.progress-skeleton {
  display: grid;
  gap: 6px;
  margin-top: 10px;
}

.progress-skeleton span {
  animation: pulse 1.2s ease-in-out infinite;
  background: linear-gradient(90deg, #e2e8f0, #f8fafc, #e2e8f0);
  background-size: 200% 100%;
  border-radius: 999px;
  height: 8px;
}

.progress-skeleton span:nth-child(2) {
  width: 82%;
}

.progress-skeleton span:nth-child(3) {
  width: 64%;
}

@keyframes pulse {
  from { background-position: 200% 0; }
  to { background-position: -200% 0; }
}

.parsed-preview {
  margin-top: 15px;
  padding: 15px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #dbeafe;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.preview-title {
  font-weight: bold;
  color: #2563eb;
}

.preview-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 10px;
}

.preview-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.preview-item .label {
  font-size: 12px;
  color: #909399;
}

.preview-item .value {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.preview-item.highlight {
  background: #fff7ed;
  padding: 8px;
  border-radius: 6px;
  border: 1px solid #ffd591;
}

.preview-item.highlight .label {
  color: #d46b08;
}

.error-msg {
  margin-top: 10px;
  padding: 10px;
  background: #fef0f0;
  border-radius: 4px;
  color: #f56c6c;
  font-size: 14px;
}

.cot-analysis {
  margin-top: 15px;
  padding: 15px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #dbeafe;
}

.cot-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.cot-title {
  font-weight: bold;
  color: #2563eb;
  font-size: 14px;
}

.cot-content {
  font-size: 13px;
  color: #606266;
}

.cot-step {
  margin-bottom: 8px;
}

.step-label {
  font-weight: bold;
  color: #909399;
}

.step-value {
  color: #303133;
}

.guidance-msg {
  margin-top: 10px;
  padding: 12px;
  background: #fff7ed;
  border-radius: 6px;
  border: 1px solid #faecd8;
}

.guidance-header {
  font-weight: bold;
  color: #e6a23c;
  margin-bottom: 6px;
  font-size: 14px;
}

.guidance-content {
  color: #606266;
  font-size: 13px;
  line-height: 1.5;
}

.preview-item.missing {
  background: #fef0f0;
  border-radius: 4px;
  padding: 4px;
}

.preview-item.missing .value {
  color: #f56c6c;
  font-style: italic;
}

@media (max-width: 720px) {
  .input-area {
    flex-direction: column;
  }

  .parse-btn,
  .reset-btn {
    width: 100%;
    min-height: 40px;
  }
}
</style>
