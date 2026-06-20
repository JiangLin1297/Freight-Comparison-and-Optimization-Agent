<template>
  <header class="header">
    <div>
      <p class="kicker">Freight Optimization Agent</p>
      <h1>运输方案比价与优化智能体</h1>
      <p>自然语言解析、多轮补全、费率匹配与多维评分的一体化工作台。</p>
    </div>
    <div
      class="header-badge"
      :class="{
        'badge--custom': hasCustomAgent,
        'badge--disconnected': !isFullyConnected
      }"
      @click="$emit('open-settings')"
      :title="statusTip"
    >
      <span>{{ hasCustomAgent ? (customLabel || '自定义 Agent') : 'Agent v2' }}</span>
      <strong>{{ hasCustomAgent ? (customSubtitle || '自定义接入') : 'LLM + Rules' }}</strong>
      <div class="llm-status">
        <span class="status-dot" :class="isFullyConnected ? 'connected' : 'disconnected'"></span>
        <span class="status-text" :class="{ 'text-error': !isFullyConnected }">
          {{ statusText }}
        </span>
        <span v-if="displayModel && isFullyConnected" class="status-model">{{ displayModel }}</span>
      </div>
      <span v-if="!isOnline" class="badge-error">⚠ 目前未有网络连接</span>
      <span v-else-if="!llmConnected" class="badge-error">⚠ LLM未连接</span>
      <span v-else class="badge-hint">{{ hasCustomAgent ? '点击修改配置' : '点击接入你的 Agent' }}</span>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  hasCustomAgent: { type: Boolean, default: false },
  customModel: { type: String, default: '' },
  customLabel: { type: String, default: '' },
  customSubtitle: { type: String, default: '' },
  authHeaders: { type: Object, default: () => ({}) },
  isProcessing: { type: Boolean, default: false }, // 是否正在处理请求
})

const emit = defineEmits(['open-settings', 'update:connection-status'])

const llmConnected = ref(false)
const isOnline = ref(navigator.onLine)
const serverModel = ref('')
const connectionError = ref('')

const displayModel = computed(() => {
  if (props.hasCustomAgent && props.customModel) return props.customModel
  return serverModel.value || ''
})

// 综合连接状态：网络和LLM都连接才算已连接
const isFullyConnected = computed(() => {
  return isOnline.value && llmConnected.value
})

// 状态文本
const statusText = computed(() => {
  if (!isOnline.value) return '网络未连接'
  if (!llmConnected.value) return 'LLM 未连接'
  return 'LLM 已连接'
})

// 状态提示
const statusTip = computed(() => {
  if (!isOnline.value) return '目前未有网络连接，请检查网络设置'
  if (!llmConnected.value) return 'LLM服务未配置或连接失败'
  return ''
})

const checkStatus = async () => {
  // 先检查网络状态
  if (!navigator.onLine) {
    isOnline.value = false
    llmConnected.value = false
    connectionError.value = '目前未有网络连接'
    emit('update:connection-status', { online: false, llm: false, error: connectionError.value })
    return
  }

  isOnline.value = true

  try {
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 5000) // 5秒超时

    const res = await fetch('/api/status', {
      signal: controller.signal,
      headers: props.authHeaders
    })
    clearTimeout(timeoutId)

    const data = await res.json()
    llmConnected.value = data.llm_configured === true
    serverModel.value = data.llm_model || ''
    connectionError.value = ''
  } catch (err) {
    // 如果正在处理请求，不要将状态更新为断开连接
    if (!props.isProcessing) {
      llmConnected.value = false
      serverModel.value = ''
      if (err.name === 'AbortError') {
        connectionError.value = '连接超时'
      } else {
        connectionError.value = '无法连接到服务器'
      }
    }
  }

  emit('update:connection-status', {
    online: isOnline.value,
    llm: llmConnected.value,
    error: connectionError.value
  })
}

// 监听网络状态变化
const handleOnline = () => {
  isOnline.value = true
  checkStatus()
}

const handleOffline = () => {
  isOnline.value = false
  llmConnected.value = false
  connectionError.value = '目前未有网络连接'
  emit('update:connection-status', { online: false, llm: false, error: connectionError.value })
}

onMounted(() => {
  checkStatus()
  // 每30秒检测一次
  const statusInterval = setInterval(checkStatus, 30000)

  // 监听网络状态变化
  window.addEventListener('online', handleOnline)
  window.addEventListener('offline', handleOffline)

  // 清理定时器
  onUnmounted(() => {
    clearInterval(statusInterval)
    window.removeEventListener('online', handleOnline)
    window.removeEventListener('offline', handleOffline)
  })
})
</script>

<style scoped>
.header {
  align-items: center;
  background: #ffffff;
  border: 1px solid #d9e2ec;
  border-radius: 10px;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.05);
  color: #1f2937;
  display: flex;
  justify-content: space-between;
  margin: 0 auto;
  max-width: 1440px;
  padding: 22px 24px;
}

.kicker {
  color: #0f766e;
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 6px;
  text-transform: uppercase;
}

.header h1 {
  font-size: 26px;
  line-height: 1.2;
  margin-bottom: 8px;
}

.header p {
  color: #64748b;
  font-size: 14px;
}

.header-badge {
  background: #f8fafc;
  border: 1px solid #dbe3ee;
  border-radius: 8px;
  color: #475569;
  min-width: 140px;
  padding: 12px 14px;
  text-align: right;
  cursor: pointer;
  transition: all 0.2s;
  user-select: none;
}

.header-badge:hover {
  border-color: #0f766e;
  background: #f0fdfa;
  box-shadow: 0 2px 8px rgba(15, 118, 110, 0.1);
}

.header-badge.badge--custom {
  border-color: #0f766e;
  background: #f0fdfa;
}

.header-badge.badge--disconnected {
  border-color: #ef4444;
  background: #fef2f2;
}

.header-badge.badge--disconnected:hover {
  border-color: #dc2626;
  background: #fee2e2;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.1);
}

.text-error {
  color: #ef4444 !important;
  font-weight: 600;
}

.badge-error {
  display: block !important;
  font-size: 11px !important;
  color: #ef4444;
  margin-top: 4px;
  margin-bottom: 0 !important;
}

.header-badge span {
  display: block;
  font-size: 12px;
  margin-bottom: 4px;
}

.header-badge strong {
  color: #0f766e;
  font-size: 15px;
}

.llm-status {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 8px;
  justify-content: flex-end;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-dot.connected {
  background: #22c55e;
  box-shadow: 0 0 6px rgba(34, 197, 94, 0.5);
}

.status-dot.disconnected {
  background: #ef4444;
  box-shadow: 0 0 6px rgba(239, 68, 68, 0.5);
}

.status-text {
  font-size: 12px;
  color: #64748b;
}

.status-model {
  font-size: 11px;
  color: #94a3b8;
  background: #f1f5f9;
  padding: 1px 6px;
  border-radius: 4px;
}

.badge-hint {
  display: block !important;
  font-size: 11px !important;
  color: #94a3b8;
  margin-top: 4px;
  margin-bottom: 0 !important;
}

@media (max-width: 720px) {
  .header {
    align-items: flex-start;
    flex-direction: column;
    gap: 12px;
  }

  .header-badge {
    text-align: left;
  }
}
</style>
