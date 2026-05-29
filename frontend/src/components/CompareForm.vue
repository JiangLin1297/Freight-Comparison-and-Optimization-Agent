<template>
  <div class="card">
    <h2>订单信息输入</h2>
    <div class="form-row">
      <div class="form-item">
        <label>货物总重量 (kg) *</label>
        <el-input-number
          :model-value="form.weight"
          @update:model-value="updateField('weight', $event)"
          :min="0.01"
          :precision="2"
          placeholder="请输入重量"
          style="width: 100%"
        />
      </div>
      <div class="form-item">
        <label>起运港 *</label>
        <el-select
          :model-value="form.orig_port"
          @update:model-value="updateField('orig_port', $event)"
          placeholder="请选择起运港"
          style="width: 100%"
        >
          <el-option v-for="port in ports.orig_ports" :key="port" :label="port" :value="port" />
        </el-select>
      </div>
      <div class="form-item">
        <label>目的港 *</label>
        <el-select
          :model-value="form.dest_port"
          @update:model-value="updateField('dest_port', $event)"
          placeholder="请选择目的港"
          style="width: 100%"
        >
          <el-option v-for="port in ports.dest_ports" :key="port" :label="port" :value="port" />
        </el-select>
      </div>
      <div class="form-item">
        <label>最大运输天数 (可选)</label>
        <el-input-number
          :model-value="form.max_days"
          @update:model-value="updateField('max_days', $event)"
          :min="0"
          :max="365"
          placeholder="不限"
          style="width: 100%"
        />
      </div>
    </div>

    <!-- 优先级选择（三列，可点击切换） -->
    <div class="priority-display">
      <div
        class="priority-item"
        :class="{ active: form.priority === 'cost' }"
        @click="updateField('priority', 'cost')"
      >
        <div class="priority-icon">💰</div>
        <div class="priority-label">成本优先</div>
        <div class="priority-desc">优先推荐最便宜的方案</div>
        <div class="priority-status">
          <el-tag v-if="form.priority === 'cost'" type="success" size="small" effect="dark">已启用</el-tag>
          <el-tag v-else type="info" size="small">点击启用</el-tag>
        </div>
      </div>
      <div
        class="priority-item"
        :class="{ active: form.priority === 'time' }"
        @click="updateField('priority', 'time')"
      >
        <div class="priority-icon">⚡</div>
        <div class="priority-label">时效优先</div>
        <div class="priority-desc">优先推荐最快的方案</div>
        <div class="priority-status">
          <el-tag v-if="form.priority === 'time'" type="danger" size="small" effect="dark">已启用</el-tag>
          <el-tag v-else type="info" size="small">点击启用</el-tag>
        </div>
      </div>
      <div
        class="priority-item"
        :class="{ active: !form.priority }"
        @click="updateField('priority', null)"
      >
        <div class="priority-icon">⚖️</div>
        <div class="priority-label">均衡模式</div>
        <div class="priority-desc">综合考虑成本、时效、服务</div>
        <div class="priority-status">
          <el-tag v-if="!form.priority" type="primary" size="small" effect="dark">已启用</el-tag>
          <el-tag v-else type="info" size="small">点击启用</el-tag>
        </div>
      </div>
    </div>

    <div style="margin-top: 20px">
      <el-button type="primary" class="btn-compare" @click="$emit('compare')" :loading="loading">
        推荐方案
      </el-button>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  form: { type: Object, required: true },
  ports: { type: Object, default: () => ({ orig_ports: [], dest_ports: [] }) },
  loading: { type: Boolean, default: false }
})

const emit = defineEmits(['update:form', 'compare'])

const updateField = (field, value) => {
  emit('update:form', { ...props.form, [field]: value })
}
</script>

<style scoped>
.card {
  background: white;
  border-radius: 10px;
  padding: 25px;
  margin-bottom: 20px;
  box-shadow: 0 2px 12px rgba(0,0,0,0.08);
}
.card h2 {
  font-size: 18px;
  color: #303133;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 2px solid #667eea;
}
.form-row { display: flex; gap: 20px; flex-wrap: wrap; }
.form-item { flex: 1; min-width: 200px; }
.form-item label { display: block; margin-bottom: 8px; font-weight: bold; color: #606266; }
.btn-compare { width: 100%; height: 50px; font-size: 16px; }

.priority-display {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px dashed #dcdfe6;
  display: flex;
  gap: 15px;
}

.priority-item {
  flex: 1;
  padding: 15px;
  background: #f5f7fa;
  border-radius: 8px;
  text-align: center;
  border: 2px solid transparent;
  transition: all 0.3s ease;
}

.priority-item.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.priority-icon {
  font-size: 24px;
  margin-bottom: 8px;
}

.priority-label {
  font-weight: bold;
  font-size: 14px;
  margin-bottom: 8px;
}

.priority-item.active .priority-label {
  color: white;
}

.priority-status {
  margin-top: 5px;
}
</style>
