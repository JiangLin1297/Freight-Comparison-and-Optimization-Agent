<template>
  <header class="header">
    <div>
      <p class="kicker">Freight Optimization Agent</p>
      <h1>运输方案比价与优化智能体</h1>
      <p>自然语言解析、多轮补全、费率匹配与多维评分的一体化工作台。</p>
    </div>
    <div class="header-badge">
      <span>Agent v2</span>
      <strong>LLM + Rules</strong>
    </div>
  </header>
</template>

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
