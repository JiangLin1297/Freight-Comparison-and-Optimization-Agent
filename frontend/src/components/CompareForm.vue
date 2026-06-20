<template>
  <div class="card">
    <div class="card-header">
      <div>
        <p class="eyebrow">结构化订单</p>
        <h2>订单信息</h2>
      </div>
      <el-tag type="info" effect="plain">可手动调整</el-tag>
    </div>
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
          <el-option
            v-for="port in ports.orig_ports"
            :key="port.code"
            :label="port.name + ' (' + port.code + ')'"
            :value="port.code"
          />
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
          <el-option
            v-for="port in ports.dest_ports"
            :key="port.code"
            :label="port.name + ' (' + port.code + ')'"
            :value="port.code"
          />
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

    <div class="priority-display">
      <div
        class="priority-item"
        :class="{ active: form.priority === 'cost' }"
        @click="updateField('priority', 'cost')"
      >
        <div class="priority-icon">Cost</div>
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
        <div class="priority-icon">Time</div>
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
        <div class="priority-icon">Balanced</div>
        <div class="priority-label">均衡模式</div>
        <div class="priority-desc">综合考虑成本、时效、服务</div>
        <div class="priority-status">
          <el-tag v-if="!form.priority" type="primary" size="small" effect="dark">已启用</el-tag>
          <el-tag v-else type="info" size="small">点击启用</el-tag>
        </div>
      </div>
    </div>

    <div class="action-row">
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
  border: 1px solid #d9e2ec;
  border-radius: 8px;
  padding: 18px;
  box-shadow: 0 12px 30px rgba(15, 23, 42, 0.05);
}

.card-header {
  align-items: flex-start;
  display: flex;
  justify-content: space-between;
  margin-bottom: 16px;
}

.card h2 {
  color: #1f2937;
  font-size: 18px;
}

.eyebrow {
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
  margin-bottom: 4px;
}
.form-row { display: flex; gap: 20px; flex-wrap: wrap; }
.form-item { flex: 1; min-width: 200px; }
.form-item label {
  color: #475569;
  display: block;
  font-size: 13px;
  font-weight: 700;
  margin-bottom: 8px;
}
.btn-compare { width: 100%; height: 50px; font-size: 16px; }

.priority-display {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid #e2e8f0;
  display: flex;
  gap: 10px;
}

.priority-item {
  flex: 1;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  cursor: pointer;
  padding: 12px;
  text-align: left;
  transition: all 0.2s ease;
}

.priority-item.active {
  background: #eef6ff;
  border-color: #2563eb;
  box-shadow: inset 3px 0 0 #2563eb;
}

.priority-icon {
  color: #0f766e;
  font-size: 12px;
  font-weight: 800;
  margin-bottom: 6px;
  text-transform: uppercase;
}

.priority-label {
  color: #1f2937;
  font-weight: bold;
  font-size: 14px;
  margin-bottom: 4px;
}

.priority-desc {
  color: #64748b;
  font-size: 12px;
  line-height: 1.4;
}

.priority-status {
  margin-top: 8px;
}

.action-row {
  margin-top: 18px;
}

@media (max-width: 720px) {
  .priority-display {
    flex-direction: column;
  }
}
</style>
