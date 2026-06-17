<template>
  <el-dialog
    v-model="visible"
    title="连接 Agent"
    width="480px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="settings-body">
      <!-- 当前状态 -->
      <div class="current-status" :class="isConnected ? 'status-connected' : 'status-default'">
        <span class="status-icon">{{ isConnected ? '🔗' : '🔌' }}</span>
        <div>
          <strong>{{ isConnected ? '已连接自定义 Agent' : '使用本地默认配置' }}</strong>
          <p v-if="isConnected" class="status-detail">{{ credentials.base_url }} · {{ credentials.model }}</p>
          <p v-else class="status-detail">当前使用服务器 .env 配置的 LLM 服务</p>
        </div>
      </div>

      <!-- 表单 -->
      <el-form :model="form" label-position="top" class="settings-form">
        <el-form-item label="API Base URL" required>
          <el-input
            v-model="form.base_url"
            placeholder="https://api.openai.com/v1"
            clearable
          >
            <template #prefix>
              <span>🌐</span>
            </template>
          </el-input>
          <p class="field-hint">兼容 OpenAI 接口的服务地址</p>
        </el-form-item>

        <el-form-item label="API Key" required>
          <el-input
            v-model="form.api_key"
            type="password"
            show-password
            placeholder="sk-..."
            clearable
          >
            <template #prefix>
              <span>🔑</span>
            </template>
          </el-input>
          <p class="field-hint">你的 API 密钥，仅存储在浏览器本地</p>
        </el-form-item>

        <el-form-item label="Model">
          <el-input
            v-model="form.model"
            placeholder="mimo-v2.5-pro"
            clearable
          >
            <template #prefix>
              <span>🤖</span>
            </template>
          </el-input>
          <p class="field-hint">留空则使用默认模型 mimo-v2.5-pro</p>
        </el-form-item>

        <el-divider />

        <el-form-item label="显示名称">
          <el-input
            v-model="form.label"
            placeholder="自定义 Agent"
            clearable
            maxlength="20"
            show-word-limit
          >
            <template #prefix>
              <span>✏️</span>
            </template>
          </el-input>
          <p class="field-hint">右上角徽章第一行显示的文字</p>
        </el-form-item>

        <el-form-item label="副标题">
          <el-input
            v-model="form.subtitle"
            placeholder="自定义接入"
            clearable
            maxlength="20"
            show-word-limit
          >
            <template #prefix>
              <span>📝</span>
            </template>
          </el-input>
          <p class="field-hint">右上角徽章第二行显示的文字</p>
        </el-form-item>
      </el-form>

      <!-- 测试结果 -->
      <div v-if="testResult" class="test-result" :class="testResult.success ? 'test-success' : 'test-fail'">
        <span>{{ testResult.success ? '✅' : '❌' }}</span>
        <span>{{ testResult.message }}</span>
        <span v-if="testResult.model" class="test-model">{{ testResult.model }}</span>
      </div>
    </div>

    <template #footer>
      <div class="dialog-footer">
        <div class="footer-left">
          <el-button
            v-if="isConnected"
            type="danger"
            plain
            size="small"
            @click="handleDisconnect"
          >
            断开连接
          </el-button>
        </div>
        <div class="footer-right">
          <el-button @click="handleTest" :loading="testing" :disabled="!canTest">
            测试连接
          </el-button>
          <el-button type="primary" @click="handleSave" :disabled="!canSave">
            保存
          </el-button>
        </div>
      </div>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  credentials: { type: Object, default: () => ({ api_key: '', base_url: '', model: '', label: '', subtitle: '' }) },
})

const emit = defineEmits(['update:modelValue', 'save', 'disconnect'])

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val),
})

const form = reactive({
  api_key: '',
  base_url: '',
  model: '',
  label: '',
  subtitle: '',
})

const testing = ref(false)
const testResult = ref(null)

const isConnected = computed(() => !!(props.credentials.api_key && props.credentials.base_url))

const canTest = computed(() => form.api_key.trim() && form.base_url.trim())
const canSave = computed(() => form.api_key.trim() && form.base_url.trim())

// 打开弹窗时回填表单
watch(visible, (val) => {
  if (val) {
    form.api_key = props.credentials.api_key || ''
    form.base_url = props.credentials.base_url || ''
    form.model = props.credentials.model || ''
    form.label = props.credentials.label || ''
    form.subtitle = props.credentials.subtitle || ''
    testResult.value = null
  }
})

async function handleTest() {
  if (!canTest.value) return
  testing.value = true
  testResult.value = null
  try {
    const res = await fetch('/api/test_llm', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        api_key: form.api_key.trim(),
        base_url: form.base_url.trim(),
        model: form.model.trim() || 'mimo-v2.5-pro',
      }),
    })
    testResult.value = await res.json()
  } catch (e) {
    testResult.value = { success: false, message: `网络错误: ${e.message}`, model: '' }
  } finally {
    testing.value = false
  }
}

function handleSave() {
  if (!canSave.value) return
  emit('save', {
    api_key: form.api_key.trim(),
    base_url: form.base_url.trim(),
    model: form.model.trim() || 'mimo-v2.5-pro',
    label: form.label.trim() || '自定义 Agent',
    subtitle: form.subtitle.trim() || '自定义接入',
  })
  ElMessage.success('Agent 配置已保存')
  visible.value = false
}

function handleDisconnect() {
  emit('disconnect')
  ElMessage.info('已断开自定义 Agent，恢复默认配置')
  visible.value = false
}

function handleClose() {
  testResult.value = null
}
</script>

<style scoped>
.settings-body {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.current-status {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
  background: #f9fafb;
}

.current-status.status-connected {
  border-color: #86efac;
  background: #f0fdf4;
}

.status-icon {
  font-size: 24px;
}

.current-status strong {
  display: block;
  font-size: 14px;
  color: #1f2937;
}

.status-detail {
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}

.settings-form {
  margin-top: 4px;
}

.field-hint {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 4px;
  line-height: 1.3;
}

.test-result {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  border-radius: 6px;
  font-size: 13px;
}

.test-success {
  background: #f0fdf4;
  border: 1px solid #86efac;
  color: #166534;
}

.test-fail {
  background: #fef2f2;
  border: 1px solid #fca5a5;
  color: #991b1b;
}

.test-model {
  margin-left: auto;
  font-size: 11px;
  opacity: 0.7;
}

.dialog-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.footer-left,
.footer-right {
  display: flex;
  gap: 8px;
}
</style>
