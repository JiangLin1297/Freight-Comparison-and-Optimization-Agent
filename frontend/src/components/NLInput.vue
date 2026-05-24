<template>
  <div class="nl-input-card">
    <h3 class="card-title">智能语音输入</h3>
    <p class="card-desc">用自然语言描述您的运输需求，AI将自动解析为订单信息</p>

    <div class="input-area">
      <el-input
        v-model="inputText"
        type="textarea"
        :rows="3"
        placeholder="例如：从上海运输100公斤货物到深圳，希望5天内到达（支持中文港口名或PORT代码，支持天/周/月/工作日等时间格式）"
        :disabled="parsing"
      />
      <el-button
        type="primary"
        :loading="parsing"
        @click="handleParse"
        class="parse-btn"
      >
        {{ parsing ? '解析中...' : '智能解析' }}
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

    <!-- 解析结果预览 -->
    <div v-if="parsedData" class="parsed-preview">
      <div class="preview-header">
        <span class="preview-title">解析结果</span>
        <el-button type="success" size="small" @click="handleConfirm">确认填充</el-button>
      </div>
      <div class="preview-grid">
        <div class="preview-item" v-if="parsedData.weight">
          <span class="label">货物重量</span>
          <span class="value">{{ parsedData.weight }} kg</span>
        </div>
        <div class="preview-item" v-if="parsedData.orig_port">
          <span class="label">起运港</span>
          <span class="value">{{ parsedData.orig_port }}</span>
        </div>
        <div class="preview-item" v-if="parsedData.dest_port">
          <span class="label">目的港</span>
          <span class="value">{{ parsedData.dest_port }}</span>
        </div>
        <div class="preview-item" v-if="parsedData.max_days">
          <span class="label">最大天数</span>
          <span class="value">{{ parsedData.max_days }} 天</span>
        </div>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="errorMsg" class="error-msg">{{ errorMsg }}</div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const emit = defineEmits(['parsed'])

const inputText = ref('')
const parsing = ref(false)
const parsedData = ref(null)
const errorMsg = ref('')

const handleParse = async () => {
  if (!inputText.value.trim()) {
    ElMessage.warning('请输入运输需求描述')
    return
  }

  parsing.value = true
  errorMsg.value = ''
  parsedData.value = null

  try {
    const { data } = await axios.post('/api/parse', { text: inputText.value })
    if (data.error) {
      errorMsg.value = data.error
    } else {
      parsedData.value = data.data
      ElMessage.success('解析成功，请确认信息')
    }
  } catch (err) {
    errorMsg.value = '解析失败：' + (err.response?.data?.detail || err.message)
  } finally {
    parsing.value = false
  }
}

const handleConfirm = () => {
  if (parsedData.value) {
    emit('parsed', parsedData.value)
    ElMessage.success('已填充到表单')
  }
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

.error-msg {
  margin-top: 10px;
  padding: 10px;
  background: #fef0f0;
  border-radius: 4px;
  color: #f56c6c;
  font-size: 14px;
}
</style>
