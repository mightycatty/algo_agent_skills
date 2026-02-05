# Paper Reader - Usage Examples

本文档展示如何使用 `paper-reader` 技能通过 Gemini CLI 分析深度学习论文。

---

## 基础用法

### 1. 分析 ArXiv 论文

```bash
# 使用 ArXiv 链接分析论文
gemini -p "请使用 paper-reader 技能分析这篇论文：https://arxiv.org/abs/2307.09288"
```

### 2. 分析本地 PDF

```bash
# 分析本地 PDF 文件
gemini -p "请使用 paper-reader 技能分析这篇论文" -f ./llama2.pdf
```

### 3. 分析论文 + 源码实现

```bash
# 同时提供论文和 GitHub 源码
gemini -p "请使用 paper-reader 技能分析这篇论文，同时分析源码实现：
论文: https://arxiv.org/abs/1810.04805
源码: https://github.com/huggingface/transformers/tree/main/src/transformers/models/bert"
```

---

## 完整示例：分析 Llama 2 论文

### 命令

```bash
gemini -p "使用 paper-reader 技能，帮我分析 Llama 2 论文：https://arxiv.org/abs/2307.09288
请输出完整的结构化报告。"
```

### 预期输出结构

Agent 会生成一份遵循模板的报告，包含以下章节：

```markdown
# Llama 2: Open Foundation and Fine-Tuned Chat Models

**Authors:** Hugo Touvron, Louis Martin, et al.
**Institution:** Meta AI
**Published:** 2023

---

## TL;DR

Llama 2 是 Meta 开源的大语言模型系列（7B-70B 参数），
通过扩大预训练规模（2T tokens）和引入 RLHF 对齐技术，
在多项基准上超越开源竞品，同时保持安全性。

---

## §1 Problem Statement
...

## §2 Core Insights & Contributions
...

## §3 Data Curation & Processing
| Dataset | Domain | Scale | Notes |
|---------|--------|-------|-------|
| Pretraining | Web crawl | 2T tokens | ... |
...

## §4 Model Architecture
- **Base:** Transformer decoder-only
- **Context Length:** 4096 tokens
- **Key Innovations:** 
  - Grouped Query Attention (GQA) for 34B/70B
  - RMSNorm, SwiGLU activation
...

## §5 Training Recipe
| Stage | Method | Details |
|-------|--------|---------|
| Pre-training | Next-token prediction | 2T tokens, cosine LR |
| SFT | Supervised Fine-tuning | 27,540 samples |
| RLHF | PPO + Rejection Sampling | 1.4M annotations |
...

## §6 Metrics & Performance
| Benchmark | Llama 2 70B | GPT-3.5 | GPT-4 |
|-----------|-------------|---------|-------|
| MMLU | 68.9 | 70.0 | 86.4 |
...

## §7 Limitations & Future Work
...

## §8 Reproducibility
| Component | Available | Link |
|-----------|-----------|------|
| Weights | ✅ | https://ai.meta.com/llama/ |
| Training Code | ❌ | N/A |
...
```

---

## 高级用法

### 大型 PDF 分块处理

当论文过长（如 100+ 页）时：

```bash
# 先使用分块工具
python references/chunk_paper.py large_paper.pdf ./chunks/

# 然后让 Agent 分析
gemini -p "请使用 paper-reader 技能分析 ./chunks/ 目录中的论文分块，
按优先级处理：先读 P0 获取概览，再读 P1 获取技术细节。"
```

### 仅分析特定章节

```bash
gemini -p "使用 paper-reader 技能，仅分析这篇论文的 Training Recipe 部分：
https://arxiv.org/abs/2307.09288
输出 §5 Training Recipe 的详细信息。"
```

### 对比多篇论文

```bash
gemini -p "使用 paper-reader 技能分析以下两篇论文，并对比它们的训练策略：
1. Llama 2: https://arxiv.org/abs/2307.09288
2. Mistral 7B: https://arxiv.org/abs/2310.06825"
```

---

## 故障排除

### 下载失败

如果 PDF 下载失败（如代理问题），可以：

1. 手动下载 PDF 并传入：
   ```bash
   gemini -p "分析这篇论文" -f ./paper.pdf
   ```

2. 直接粘贴论文文本：
   ```bash
   gemini -p "使用 paper-reader 技能分析以下论文内容：
   [粘贴论文文本]"
   ```

### 输出不完整

如果报告缺少某些章节，可以追问：
```bash
gemini -p "请补充 §5 Training Recipe 中的超参数表格"
```

---

## 相关命令

```bash
# 查看可用技能
gemini -p "列出所有可用的技能"

# 查看技能详情
gemini -p "显示 paper-reader 技能的详细说明"
```
