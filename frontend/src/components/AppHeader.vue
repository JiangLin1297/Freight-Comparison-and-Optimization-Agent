<template>
  <header class="header">
    <div>
      <p class="kicker">Freight Optimization Agent</p>
      <h1>运输方案比价与优化智能体</h1>
      <p>自然语言解析、多轮补全、费率匹配与多维评分的一体化工作台。</p>
    </div>
    <div
      class="header-badge"
      :class="{ 'badge--custom': hasCustomAgent }"
      @click="$emit('open-settings')"
    >
      <span>{{ hasCustomAgent ? (customLabel || '自定义 Agent') : 'Agent v2' }}</span>
      <strong>{{ hasCustomAgent ? (customSubtitle || '自定义接入') : 'LLM + Rules' }}</strong>
      <div class="llm-status">
        <span class="status-dot" :class="llmConnected ? 'connected' : 'disconnected'"></span>
        <span class="status-text">{{ llmConnected ? 'LLM 已连接' : 'LLM 未连接' }}</span>
        <span v-if="displayModel" class="status-model">{{ displayModel }}</span>
      </div>
      <span class="badge-hint">{{ hasCustomAgent ? '点击修改配置' : '点击接入你的 Agent' }}</span>
    </div>
  </header>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const props = defineProps({
  hasCustomAgent: { type: Boolean, default: false },
  customModel: { type: String, default: '' },
  customLabel: { type: String, default: '' },
  customSubtitle: { type: String, default: '' },
})

defineEmits(['open-settings'])

const llmConnected = ref(false)
const serverModel = ref('')

const displayModel = computed(() => {
  if (props.hasCustomAgent && props.customModel) return props.customModel
  return serverModel.value || ''
})

const checkStatus = async () => {
  try {
    const res = await fetch('/api/status')
    const data = await res.json()
    llmConnected.value = data.llm_configured === true
    serverModel.value = data.llm_model || ''
  } catch {
    llmConnected.value = false
    serverModel.value = ''
  }
}

onMounted(checkStatus)
setInterval(checkStatus, 30000)
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
