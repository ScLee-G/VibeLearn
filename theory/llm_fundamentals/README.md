# LLM 基础原理

## 一、什么是大语言模型（LLM）

大语言模型是基于Transformer架构的深度学习模型，能够理解和生成人类语言。

## 二、核心概念

### 1. Transformer 架构
- 自注意力机制（Self-Attention）
- 多头注意力（Multi-Head Attention）
- 位置编码（Positional Encoding）

### 2. 训练过程
- 预训练（Pre-training）：在海量文本上学习通用知识
- 微调（Fine-tuning）：在特定任务上进行调整
- 提示学习（Prompt Learning）：通过提示词引导模型行为

### 3. 关键能力
- 文本生成
- 理解推理
- 代码生成
- 多模态理解

## 三、主流模型对比

| 模型 | 发布时间 | 特点 |
|:---|:---|:---|
| GPT-3 | 2020 | 首次展示大模型能力 |
| GPT-4 | 2023 | 多模态能力、更强推理 |
| DeepSeek-V3 | 2024 | 开源、长上下文、代码能力强 |
| Qwen | 2023 | 阿里开源、中文支持好 |

## 四、学习资源

1. Attention is All You Need - 原始论文
2. OpenAI API 文档
3. Hugging Face Transformers