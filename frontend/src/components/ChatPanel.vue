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
        <el-icon @click="isOpen = false" class="close-btn"><Close /></el-icon>
      </div>

      <div class="chat-messages" ref="messagesRef">
        <div class="message welcome">
          <div class="message-content">
            您好！我是AI物流助手，可以帮您解答运输相关问题，或者帮您分析最优运输方案。
          </div>
        </div>
        <div
          v-for="(msg, index) in messages"
          :key="index"
          class="message"
          :class="msg.role"
        >
          <div class="message-content">{{ msg.content }}</div>
        </div>
        <div v-if="sending" class="message assistant">
          <div class="message-content loading">思考中...</div>
        </div>
      </div>

      <div class="chat-input">
        <el-input
          v-model="inputMsg"
          placeholder="输入消息..."
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
import { ChatDotRound, Close } from '@element-plus/icons-vue'

const isOpen = ref(false)
const inputMsg = ref('')
const messages = ref([])
const sending = ref(false)
const messagesRef = ref(null)

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
    const { data } = await axios.post('/api/chat', { message: userMsg })
    messages.value.push({
      role: 'assistant',
      content: data.response || '抱歉，暂时无法回答'
    })
  } catch (err) {
    messages.value.push({
      role: 'assistant',
      content: '请求失败：' + (err.response?.data?.detail || err.message)
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
  width: 380px;
  height: 500px;
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
  max-width: 80%;
  padding: 10px 14px;
  font-size: 14px;
  line-height: 1.5;
}

.message-content.loading {
  color: #909399;
}

.message.welcome .message-content {
  background: #f0f9ff;
  color: #409eff;
  border-radius: 12px;
  max-width: 100%;
}

.chat-input {
  padding: 12px;
  border-top: 1px solid #eee;
  display: flex;
  gap: 8px;
}
</style>
