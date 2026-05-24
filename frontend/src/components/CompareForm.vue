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
    <div style="margin-top: 20px">
      <el-button type="primary" class="btn-compare" @click="$emit('compare')" :loading="loading">
        开始比价
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
</style>
