<template>
  <div class="chat-panel" :class="{ open: isOpen }">
    <!-- 切换按钮 -->
    <div class="chat-toggle" @click="isOpen = !isOpen">
      <el-icon :size="24"><ChatDotRound /></el-icon>
      <span v-if="!isOpen">AI助手</span>
    </div>

    <!-- 聊天窗口 -->
    <div v-show="isOpen" class="chat-window">
      <div class="chat-header">
        <span>AI物流助手</span>
        <div class="header-actions">
          <el-icon @click="isOpen = false" class="close-btn"><Close /></el-icon>
        </div>
      </div>

      <div class="chat-messages" ref="messagesRef">
        <div class="message welcome">
          <div class="message-content">
            您好！我是AI物流助手，可以帮您：
            <ul>
              <li>查询运费和比价</li>
              <li>获取港口信息</li>
              <li>分析最优运输方案</li>
              <li>解释运费计算规则</li>
            </ul>
          </div>
        </div>
        <div
          v-for="(msg, index) in messages"
          :key="index"
          class="message"
          :class="msg.role"
        >
          <div class="message-content">
            <div v-if="msg.content" v-html="formatMessage(msg.content)"></div>
            <!-- 工具调用结果展示 -->
            <div v-if="msg.tool_results && msg.tool_results.length > 0" class="tool-results">
              <el-divider content-position="left">查询结果</el-divider>
              <div v-for="(result, idx) in msg.tool_results" :key="idx" class="tool-result">
                <div v-if="result.success && result.result">
                  <!-- 比价结果 -->
                  <div v-if="result.tool === 'compare_freight'" class="compare-result">
                    <p><strong>找到 {{ result.result.total_plans }} 个方案</strong></p>
                    <div v-if="result.result.recommendation" class="recommendation">
                      <p>推荐方案：</p>
                      <ul>
                        <li>承运商：{{ result.result.recommendation.carrier }}</li>
                        <li>运输天数：{{ result.result.recommendation.transport_days }}天</li>
                        <li>总成本：${{ result.result.recommendation.total_cost?.toFixed(2) }}</li>
                        <li>评分：{{ result.result.recommendation.score?.toFixed(3) }}</li>
                      </ul>
                      <p class="reason">{{ result.result.recommendation.reason }}</p>
                    </div>
                  </div>
                  <!-- 港口列表 -->
                  <div v-else-if="result.tool === 'get_ports'" class="ports-result">
                    <p><strong>可用港口：</strong></p>
                    <p>起运港：{{ result.result.orig_ports?.map(p => getPortName(p)).join(', ') }}</p>
                    <p>目的港：{{ result.result.dest_ports?.map(p => getPortName(p)).join(', ') }}</p>
                  </div>
                  <!-- 统计信息 -->
                  <div v-else-if="result.tool === 'get_statistics'" class="stats-result">
                    <p><strong>系统统计：</strong></p>
                    <ul>
                      <li>总记录数：{{ result.result.total_records }}</li>
                      <li>承运商数量：{{ result.result.total_carriers }}</li>
                      <li>运输方式：{{ result.result.transport_modes?.join(', ') }}</li>
                    </ul>
                  </div>
                  <!-- 成本解释 -->
                  <div v-else-if="result.tool === 'explain_cost'" class="cost-result">
                    <p><strong>费用计算：</strong></p>
                    <p>{{ result.result.explanation }}</p>
                  </div>
                  <!-- 通用结果 -->
                  <div v-else>
                    <pre>{{ JSON.stringify(result.result, null, 2) }}</pre>
                  </div>
                </div>
                <div v-else-if="!result.success" class="error">
                  <el-alert :title="result.error" type="error" show-icon :closable="false" />
                </div>
              </div>
            </div>
          </div>
        </div>
        <div v-if="sending" class="message assistant">
          <div class="message-content loading">
            <el-icon class="is-loading"><Loading /></el-icon>
            思考中...
          </div>
        </div>
      </div>

      <div class="chat-input">
        <el-input
          v-model="inputMsg"
          placeholder="输入查询需求，如：从大连运100kg到厦门"
          @keyup.enter="handleSend"
          :disabled="sending"
        />
        <el-button type="primary" @click="handleSend" :loading="sending">
          发送
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, watch } from 'vue'
import axios from 'axios'
import { ChatDotRound, Close, Loading } from '@element-plus/icons-vue'
import { getPortName } from '../utils/portUtils.js'

const props = defineProps({
  authHeaders: { type: Object, default: () => ({}) },
})

const isOpen = ref(false)
const inputMsg = ref('')
const messages = ref([])
const sending = ref(false)
const messagesRef = ref(null)

function formatMessage(text) {
  if (!text) return ''
  return text
    .replace(/\*\*(.+?)\*\*/g, '<b>$1</b>')
    .replace(/\n\n/g, '<br/><br/>')
}

const scrollToBottom = () => {
  nextTick(() => {
    if (messagesRef.value) {
      messagesRef.value.scrollTop = messagesRef.value.scrollHeight
    }
  })
}

watch(messages, scrollToBottom, { deep: true })

const handleSend = async () => {
  if (!inputMsg.value.trim() || sending.value) return

  const userMsg = inputMsg.value.trim()
  messages.value.push({ role: 'user', content: userMsg })
  inputMsg.value = ''
  sending.value = true

  try {
    const { data } = await axios.post('/api/agentic_chat', { message: userMsg }, { headers: props.authHeaders })

    const toolResults = []
    // compare_freight → 比价推荐
    if (data.recommendation || data.plans?.length > 0) {
      toolResults.push({
        success: true,
        tool: 'compare_freight',
        result: {
          total_plans: data.plans?.length || 0,
          recommendation: data.recommendation || null
        }
      })
    }
    // get_ports → 从 message 提取港口信息用于展示
    if (data.intent === 'get_ports' && data.tool_results?.length > 0) {
      const portsResult = data.tool_results.find(t => t.tool === 'get_ports')
      if (portsResult?.success) {
        toolResults.push({ ...portsResult, tool: 'get_ports' })
      }
    }
    // get_statistics → 同
    if (data.intent === 'get_statistics' && data.tool_results?.length > 0) {
      const statsResult = data.tool_results.find(t => t.tool === 'get_statistics')
      if (statsResult?.success) {
        toolResults.push({ ...statsResult, tool: 'get_statistics' })
      }
    }
    // explain_cost → 同
    if (data.tool_results?.length > 0) {
      const explainResult = data.tool_results.find(t => t.tool === 'explain_cost')
      if (explainResult?.success) {
        toolResults.push({ ...explainResult, tool: 'explain_cost' })
      }
    }
    // 如果 tool_results 已有其他工具结果但未被上述处理，兜底传入
    if (toolResults.length === 0 && data.tool_results?.length > 0) {
      toolResults.push(...data.tool_results)
    }

    const assistantMsg = {
      role: 'assistant',
      content: data.response || data.message || '抱歉，暂时无法回答',
      tool_calls: data.tool_calls || [],
      tool_results: toolResults
    }
    messages.value.push(assistantMsg)
  } catch (err) {
    messages.value.push({
      role: 'assistant',
      content: '请求失败：' + (err.response?.data?.detail || err.message),
      tool_calls: [],
      tool_results: []
    })
  } finally {
    sending.value = false
  }
}
</script>

<style scoped>
.chat-panel {
  position: fixed;
  bottom: 20px;
  right: 20px;
  z-index: 1000;
}

.chat-toggle {
  width: 60px;
  height: 60px;
  border-radius: 8px;
  background: #1e293b;
  color: white;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.22);
  transition: transform 0.3s;
  margin-left: auto;
}

.chat-toggle:hover {
  transform: translateY(-2px);
}

.chat-toggle span {
  font-size: 10px;
  margin-top: 2px;
}

.chat-window {
  position: absolute;
  bottom: 70px;
  right: 0;
  width: 420px;
  height: 550px;
  background: white;
  border: 1px solid #d9e2ec;
  border-radius: 8px;
  box-shadow: 0 20px 50px rgba(15, 23, 42, 0.18);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-header {
  padding: 15px;
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  color: #1f2937;
  font-weight: bold;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.close-btn {
  cursor: pointer;
}

.chat-messages {
  flex: 1;
  overflow-y: auto;
  padding: 15px;
}

.message {
  margin-bottom: 12px;
  display: flex;
}

.message.user {
  justify-content: flex-end;
}

.message.user .message-content {
  background: #2563eb;
  color: white;
  border-radius: 12px 12px 0 12px;
}

.message.assistant .message-content {
  background: #f8fafc;
  color: #334155;
  border-radius: 12px 12px 12px 0;
}

.message-content {
  max-width: 85%;
  padding: 10px 14px;
  font-size: 14px;
  line-height: 1.5;
}

.message-content.loading {
  color: #909399;
  display: flex;
  align-items: center;
  gap: 8px;
}

.message.welcome .message-content {
  background: #f0fdfa;
  color: #0f766e;
  border-radius: 12px;
  max-width: 100%;
}

.message.welcome ul {
  margin: 8px 0;
  padding-left: 20px;
}

.message.welcome li {
  margin: 4px 0;
}

.chat-input {
  padding: 12px;
  border-top: 1px solid #eee;
  display: flex;
  gap: 8px;
}

/* 工具结果样式 */
.tool-results {
  margin-top: 10px;
}

.tool-result {
  margin: 8px 0;
  padding: 8px;
  background: white;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
}

.compare-result p,
.ports-result p,
.stats-result p,
.cost-result p {
  margin: 4px 0;
}

.compare-result ul,
.stats-result ul {
  margin: 4px 0;
  padding-left: 20px;
}

.compare-result li,
.stats-result li {
  margin: 2px 0;
}

.recommendation {
  background: #f0fdfa;
  padding: 8px;
  border-radius: 6px;
  margin-top: 8px;
}

.reason {
  font-size: 12px;
  color: #0f766e;
  margin-top: 4px;
  font-style: italic;
}

.error {
  margin-top: 8px;
}

pre {
  font-size: 12px;
  overflow-x: auto;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
