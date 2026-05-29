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
          <el-tag v-if="useAgentic" type="success" size="small" effect="dark">Agent模式</el-tag>
          <el-tag v-else type="info" size="small">普通模式</el-tag>
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
            <el-switch
              v-model="useAgentic"
              size="small"
              active-text="Agent模式"
              inactive-text="普通模式"
              style="margin-top: 8px;"
            />
          </div>
        </div>
        <div
          v-for="(msg, index) in messages"
          :key="index"
          class="message"
          :class="msg.role"
        >
          <div class="message-content">
            <div v-if="msg.content">{{ msg.content }}</div>
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
                    <p>起运港：{{ result.result.orig_ports?.join(', ') }}</p>
                    <p>目的港：{{ result.result.dest_ports?.join(', ') }}</p>
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
          :placeholder="useAgentic ? '输入查询需求，如：从大连运100kg到厦门' : '输入消息...'"
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

const isOpen = ref(false)
const inputMsg = ref('')
const messages = ref([])
const sending = ref(false)
const messagesRef = ref(null)
const useAgentic = ref(true)  // 默认使用Agent模式

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
    const endpoint = useAgentic.value ? '/api/agentic_chat' : '/api/chat'
    const { data } = await axios.post(endpoint, { message: userMsg })

    const assistantMsg = {
      role: 'assistant',
      content: data.response || '抱歉，暂时无法回答',
      tool_calls: data.tool_calls || [],
      tool_results: data.tool_results || []
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
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
  transition: transform 0.3s;
  margin-left: auto;
}

.chat-toggle:hover {
  transform: scale(1.1);
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
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(0,0,0,0.15);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chat-header {
  padding: 15px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
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
  background: #667eea;
  color: white;
  border-radius: 12px 12px 0 12px;
}

.message.assistant .message-content {
  background: #f4f4f5;
  color: #303133;
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
  background: #f0f9ff;
  color: #409eff;
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
  border-radius: 8px;
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
  background: #f0f9eb;
  padding: 8px;
  border-radius: 6px;
  margin-top: 8px;
}

.reason {
  font-size: 12px;
  color: #67c23a;
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
