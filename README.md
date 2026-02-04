# 🤖 Algo Agent Skills

> A curated collection of specialized AI agent skills designed for Algorithm Developers. Enhance your AI coding assistants with domain-specific capabilities.

## 📦 Installation

### Gemini CLI

**Install all extensions from the gemini CLI:**
```bash
# Clone the repository
git clone https://github.com/mightycatty/algo_agent_skills.git

# Navigate to the directory
cd algo_agent_skills

# Link as Gemini extension
gemini extensions link .
```

**Install a specific extension:**

```bash
# e.g. install the paper reader skill
gemini skills install https://github.com/mightycatty/algo_agent_skills.git --path skills/paper-reader
```

### Other CLIs
TODO

## 🛠️ Available Skills

### 📄 [Paper Reader](./skills/paper-reader/SKILL.md)

**Deconstruct deep learning research papers into structured technical summaries.**

Transform complex ML papers into actionable insights with systematic extraction of:

| Component | What's Extracted |
|-----------|------------------|
| **Problem & Insights** | Core problem, SOTA gaps, key contributions |
| **Data** | Datasets, preprocessing, synthetic data pipelines |
| **Architecture** | Model design, novel components, mathematical formulations |
| **Training** | Hyperparameters, optimization, infrastructure |
| **Results** | Benchmarks, ablations, comparative analysis |
| **Reproducibility** | Code/data/weights availability |

**Key Features:**
- 🔗 Auto-download from ArXiv, OpenReview, and direct PDF links
- 📑 Chunked reading for large papers exceeding context limits
- ✅ Built-in quality checks ensuring template compliance
- 📊 Structured output with tables and LaTeX math support

**Quick Start:**
```bash
# Analyze a paper from ArXiv
gemini -p "break down the paper: https://arxiv.org/pdf/2505.22596" --yolo

# Analyze a local PDF
gemini -p "analyze this paper" --files paper.pdf --yolo
```



