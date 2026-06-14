<template>
  <div class="history-panel">
    <div class="history-header">
      <div>
        <p class="eyebrow">操作记录</p>
        <h2>历史查询</h2>
      </div>
      <el-button
        v-if="items.length > 0"
        type="danger"
        size="small"
        plain
        @click="handleClear"
      >
        清空
      </el-button>
    </div>

    <div v-if="items.length === 0" class="history-empty">
      <el-icon :size="36" color="#cbd5e1"><Clock /></el-icon>
      <p>暂无查询记录</p>
      <span>输入运输需求后，历史将显示在这里</span>
    </div>

    <div v-else class="history-list" ref="listRef">
      <div
        v-for="(item, index) in items"
        :key="item.id"
        class="history-item"
        :class="{ active: activeId === item.id }"
        @click="handleClick(item)"
      >
        <div class="item-top">
          <el-tag
            :type="tagType(item.replyType)"
            size="small"
            effect="plain"
          >
            {{ tagLabel(item.replyType) }}
          </el-tag>
          <span class="item-time">{{ formatTime(item.timestamp) }}</span>
        </div>

        <p class="item-summary">{{ item.summary }}</p>

        <div v-if="item.result" class="item-result">
          <span>{{ item.result }}</span>
        </div>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      title="查询详情"
      width="420px"
      :append-to-body="true"
    >
      <div v-if="selectedItem" class="detail-content">
        <div class="detail-row">
          <span class="detail-label">查询时间</span>
          <span>{{ formatTimeFull(selectedItem.timestamp) }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">用户输入</span>
          <span>{{ selectedItem.userInput }}</span>
        </div>
        <div class="detail-row">
          <span class="detail-label">系统回复</span>
          <span>{{ selectedItem.message }}</span>
        </div>
        <div v-if="selectedItem.order" class="detail-row">
          <span class="detail-label">订单信息</span>
          <span>{{ formatOrder(selectedItem.order) }}</span>
        </div>
        <div v-if="selectedItem.result" class="detail-row">
          <span class="detail-label">查询结果</span>
          <span>{{ selectedItem.result }}</span>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, watch, nextTick, onMounted } from 'vue'
import { Clock } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'

const STORAGE_KEY = 'freight_history_items'
const MAX_ITEMS = 50

const props = defineProps({
  items: { type: Array, default: () => [] }
})

const emit = defineEmits(['clear', 'click-item'])

const listRef = ref(null)
const dialogVisible = ref(false)
const selectedItem = ref(null)
const activeId = ref(null)

// localStorage 持久化
const loadFromStorage = () => {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (raw) {
      const parsed = JSON.parse(raw)
      if (Array.isArray(parsed)) return parsed
    }
  } catch { /* ignore */ }
  return []
}

const saveToStorage = (items) => {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(items))
  } catch { /* ignore */ }
}

// 初始化时从 storage 恢复
onMounted(() => {
  const stored = loadFromStorage()
  if (stored.length > 0 && props.items.length === 0) {
    emit('clear') // 触发父组件同步
    // 通过 emit 无法直接设置，需要父组件配合
    // 这里改为直接暴露方法
  }
})

// 监听 items 变化自动保存
watch(
  () => props.items,
  (val) => {
    saveToStorage(val)
    nextTick(() => {
      if (listRef.value) {
        listRef.value.scrollTop = 0
      }
    })
  },
  { deep: true }
)

// 暴露给父组件的方法
defineExpose({
  loadFromStorage,
  saveToStorage
})

const tagType = (replyType) => {
  if (replyType === 'recommendation') return 'success'
  if (replyType === 'clarification') return 'warning'
  if (replyType === 'no_result') return 'danger'
  return 'info'
}

const tagLabel = (replyType) => {
  if (replyType === 'recommendation') return '已推荐'
  if (replyType === 'clarification') return '待补充'
  if (replyType === 'no_result') return '无结果'
  return '查询'
}

const formatTime = (ts) => {
  if (!ts) return ''
  const d = new Date(ts)
  const h = String(d.getHours()).padStart(2, '0')
  const m = String(d.getMinutes()).padStart(2, '0')
  return `${h}:${m}`
}

const formatTimeFull = (ts) => {
  if (!ts) return ''
  const d = new Date(ts)
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const h = String(d.getHours()).padStart(2, '0')
  const m = String(d.getMinutes()).padStart(2, '0')
  const s = String(d.getSeconds()).padStart(2, '0')
  return `${month}-${day} ${h}:${m}:${s}`
}

const formatOrder = (order) => {
  if (!order) return ''
  const parts = []
  if (order.weight) parts.push(`${order.weight}kg`)
  if (order.orig_port) parts.push(order.orig_port)
  if (order.dest_port) parts.push(`→ ${order.dest_port}`)
  if (order.max_days) parts.push(`${order.max_days}天内`)
  return parts.join('，') || '-'
}

const handleClick = (item) => {
  selectedItem.value = item
  activeId.value = item.id
  dialogVisible.value = true
}

const handleClear = async () => {
  try {
    await ElMessageBox.confirm('确定清空所有历史记录？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    emit('clear')
  } catch { /* cancelled */ }
}
</script>

<style scoped>
.history-panel {
  background: #ffffff;
  border: 1px solid #d9e2ec;
  border-radius: 8px;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.05);
  display: flex;
  flex-direction: column;
  max-height: calc(100vh - 180px);
  position: sticky;
  top: 16px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 18px 18px 14px;
  border-bottom: 1px solid #e2e8f0;
}

.history-header h2 {
  color: #1f2937;
  font-size: 18px;
  line-height: 1.25;
}

.eyebrow {
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 4px;
}

.history-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  text-align: center;
}

.history-empty p {
  color: #94a3b8;
  font-size: 14px;
  margin-top: 12px;
}

.history-empty span {
  color: #cbd5e1;
  font-size: 12px;
  margin-top: 4px;
}

.history-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.history-list::-webkit-scrollbar {
  width: 4px;
}

.history-list::-webkit-scrollbar-thumb {
  background: #e2e8f0;
  border-radius: 999px;
}

.history-item {
  padding: 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
  border: 1px solid transparent;
  margin-bottom: 4px;
}

.history-item:hover {
  background: #f8fafc;
  border-color: #e2e8f0;
}

.history-item.active {
  background: #eff6ff;
  border-color: #bfdbfe;
}

.item-top {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}

.item-time {
  color: #94a3b8;
  font-size: 11px;
  font-variant-numeric: tabular-nums;
}

.item-summary {
  color: #334155;
  font-size: 13px;
  line-height: 1.5;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.item-result {
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px dashed #e2e8f0;
}

.item-result span {
  color: #64748b;
  font-size: 12px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

/* 详情弹窗 */
.detail-content {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.detail-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.detail-label {
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
}

.detail-row > span:last-child {
  color: #1e293b;
  font-size: 14px;
  line-height: 1.6;
}
</style>
