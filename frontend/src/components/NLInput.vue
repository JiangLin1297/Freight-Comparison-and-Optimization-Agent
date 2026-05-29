<template>
  <div class="nl-input-card">
    <h3 class="card-title">智能语音输入</h3>
    <p class="card-desc">用自然语言描述您的运输需求，AI将自动解析为订单信息</p>

    <div class="input-area">
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="3"
        :placeholder="sessionId ? '请补充缺失的信息...' : '例如：从上海运输100公斤货物到深圳，希望5天内到达（支持中文港口名或PORT代码，支持天/周/月/工作日等时间格式）'"
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

    <!-- 帮助提示 -->
    <div class="help-tips">
      <p><strong>支持的时间格式：</strong></p>
      <ul>
        <li>基本格式：3天、5日、7天</li>
        <li>带修饰词：最大3天、最多5天、不超过7天</li>
        <li>带后缀：3天内、5天以内、3天内到达</li>
        <li>工作日：3个工作日、5个工作日</li>
        <li>周格式：1周、2周（自动转换为7天、14天）</li>
        <li>中文数字月：半个月、一个月（自动转换为15天、30天）</li>
        <li>模糊表达：尽快、加急（默认3天）；普通、常规（默认14天）</li>
      </ul>
    </div>

    <!-- CoT分析过程显示 -->
    <div v-if="cotAnalysis" class="cot-analysis">
      <div class="cot-header">
        <span class="cot-title">🧠 AI分析过程</span>
        <el-tag :type="confidenceType" size="small">{{ confidenceLabel }}</el-tag>
      </div>
      <div class="cot-content">
        <div class="cot-step">
          <span class="step-label">问题分析：</span>
          <span class="step-value">{{ cotAnalysis }}</span>
        </div>
      </div>
    </div>

    <!-- 引导提示 -->
    <div v-if="guidance" class="guidance-msg">
      <div class="guidance-header">💡 信息补充建议</div>
      <div class="guidance-content">{{ guidance }}</div>
    </div>

    <!-- 解析结果预览 -->
    <div v-if="parsedData" class="parsed-preview">
      <div class="preview-header">
        <span class="preview-title">解析结果</span>
        <el-button type="success" size="small" @click="handleConfirm" :disabled="!isComplete">
          {{ isComplete ? '确认填充' : '信息不完整' }}
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
              ⚡ 时效优先
            </el-tag>
            <el-tag v-else-if="parsedData.priority === 'cost'" type="success" size="small" effect="dark">
              💰 成本优先
            </el-tag>
            <el-tag v-else type="info" size="small">
              ⚖️ 均衡模式
            </el-tag>
          </span>
        </div>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const emit = defineEmits(['parsed'])

const inputText = ref('')
const parsing = ref(false)
const parsedData = ref(null)
const errorMsg = ref('')
const sessionId = ref(null)
const cotAnalysis = ref('')
const confidence = ref('')
const guidance = ref('')
const missingFields = ref([])

// 计算属性
const confidenceType = computed(() => {
  switch (confidence.value) {
    case 'high': return 'success'
    case 'medium': return 'warning'
    case 'low': return 'danger'
    default: return 'info'
  }
})

const confidenceLabel = computed(() => {
  switch (confidence.value) {
    case 'high': return '高置信度'
    case 'medium': return '中置信度'
    case 'low': return '低置信度'
    default: return ''
  }
})

const isComplete = computed(() => {
  return parsedData.value &&
    parsedData.value.weight &&
    parsedData.value.orig_port &&
    parsedData.value.dest_port
})

const handleParse = async () => {
  if (!inputText.value.trim()) {
    ElMessage.warning('请输入运输需求描述')
    return
  }

  parsing.value = true
  errorMsg.value = ''

  try {
    let response
    if (sessionId.value) {
      // 继续多轮对话
      response = await axios.post('/api/continue', {
        session_id: sessionId.value,
        message: inputText.value
      })
    } else {
      // 新的解析请求
      response = await axios.post('/api/parse', {
        text: inputText.value,
        session_id: sessionId.value
      })
    }

    const { data } = response

    if (data.error) {
      // 确保错误信息是字符串
      errorMsg.value = typeof data.error === 'string' ? data.error : JSON.stringify(data.error)
    } else {
      // 更新解析结果
      parsedData.value = {
        weight: data.data.weight,
        orig_port: data.data.orig_port,
        dest_port: data.data.dest_port,
        max_days: data.data.max_days,
        priority: data.data.priority || null
      }

      // 更新CoT分析信息
      cotAnalysis.value = data.data.analysis || ''
      confidence.value = data.data.confidence || 'high'
      guidance.value = data.data.guidance || ''
      missingFields.value = data.data.missing_fields || []

      // 更新会话ID
      if (data.data.session_id) {
        sessionId.value = data.data.session_id
      }

      // 根据置信度给出提示
      if (confidence.value === 'high') {
        ElMessage.success('解析成功，请确认信息')
      } else if (confidence.value === 'medium') {
        ElMessage.warning('部分信息模糊，建议补充')
      } else {
        ElMessage.info('信息不完整，请补充缺失内容')
      }
    }
  } catch (err) {
    // 处理各种错误格式
    let errMsg = '解析失败'
    if (err.response?.data) {
      const errData = err.response.data
      if (typeof errData === 'string') {
        errMsg = errData
      } else if (typeof errData.detail === 'string') {
        errMsg = errData.detail
      } else if (typeof errData.detail === 'object') {
        errMsg = JSON.stringify(errData.detail)
      } else {
        errMsg = JSON.stringify(errData)
      }
    } else if (err.message) {
      errMsg = err.message
    }
    errorMsg.value = errMsg
  } finally {
    parsing.value = false
    inputText.value = ''
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
  cotAnalysis.value = ''
  confidence.value = ''
  guidance.value = ''
  missingFields.value = []
  errorMsg.value = ''
}
</script>

<style scoped>
.nl-input-card {
  background: white;
  border-radius: 10px;
  padding: 25px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}

.card-title {
  font-size: 18px;
  color: #303133;
  margin-bottom: 8px;
  padding-bottom: 10px;
  border-bottom: 2px solid #667eea;
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
  height: auto;
  padding: 12px 24px;
}

.help-tips {
  margin-top: 10px;
  padding: 10px 15px;
  background: #f5f7fa;
  border-radius: 6px;
  font-size: 12px;
  color: #606266;
}

.help-tips p {
  margin: 0 0 8px 0;
  font-weight: bold;
  color: #409eff;
}

.help-tips ul {
  margin: 0;
  padding-left: 20px;
}

.help-tips li {
  margin-bottom: 4px;
  line-height: 1.4;
}

.parsed-preview {
  margin-top: 15px;
  padding: 15px;
  background: #f0f9ff;
  border-radius: 8px;
  border: 1px solid #b3d8ff;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.preview-title {
  font-weight: bold;
  color: #409eff;
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
  background: linear-gradient(135deg, #fff7e6 0%, #ffe7ba 100%);
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
  background: #f0f9ff;
  border-radius: 8px;
  border: 1px solid #b3d8ff;
}

.cot-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.cot-title {
  font-weight: bold;
  color: #409eff;
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
  background: #fdf6ec;
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
</style>
