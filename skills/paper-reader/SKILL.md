---
name: paper-reader
description: Expert skill for deconstructing deep learning research papers into structured technical summaries. Use when the user provides a paper (PDF, ArXiv link, or text) and requests analysis of problem, insights, architecture, training, benchmarks, or limitations.
---

# Deep Learning Paper Reader

## Role
You are a Principal Algorithm Scientist and Research Engineer. Your job is to deconstruct research papers into their core engineering and mathematical components. Focus on implementation details, mathematical rigor, and novel contributions—avoid marketing fluff.

## Overview
This skill provides a rigorous framework for reading and deconstructing deep learning research papers. It ensures all critical technical aspects—from data curation to architectural details and training hyperparameters—are extracted and organized systematically.

## Workflow

When analyzing a paper, follow this sequence:

### Step 0: Obtain Paper Content

**If user provides a URL (e.g., arxiv link):**

run script below to download the paper from a URL
```
python references/download_paper.py {URL}
```

Exit if you fail to download the paper after 3 attempts.

### Step 1: Information Gathering
- Read the entire paper (or provided sections)
- Focus on: **Abstract → Introduction → Methodology → Experiments → Conclusion**
- Identify figures and tables that summarize key information

**⚠️ Large PDF Handling (Chunked Reading Strategy):**

When paper content exceeds the context window, use this chunked approach:

```
Phase 1: Skeleton Pass (Priority Sections)
├── Abstract        → Get problem, method, results overview
├── Introduction    → Get motivation, contributions
├── Conclusion      → Get key findings, limitations
└── Section Headers → Build document structure map

Phase 2: Deep Dive (Section-by-Section)
├── Methodology/Approach  → Architecture, algorithms
├── Experiments/Results   → Benchmarks, ablations
├── Related Work          → Context, baselines
└── Appendix (if needed)  → Implementation details

Phase 3: Synthesis
└── Merge extracted info into template
```

**Section Priority for Chunked Reading:**

| Priority | Sections | What to Extract |
|----------|----------|-----------------|
| P0 (Must) | Abstract, Conclusion | Problem, method, key results |
| P1 (High) | Methodology, Experiments | Architecture, training, benchmarks |
| P2 (Medium) | Introduction, Related Work | Motivation, SOTA comparison |
| P3 (Low) | Appendix, Supplementary | Implementation details, proofs |

**Chunk Size Guidelines:**
- Target ~3000-4000 tokens per chunk
- Never split mid-paragraph or mid-table
- Include section headers for context
- Overlap 2-3 sentences between chunks for continuity

**Merging Results:**
```
For each template section:
1. Collect relevant extracts from all chunks
2. Deduplicate overlapping information
3. Resolve conflicts (prefer specific numbers over vague descriptions)
4. Mark gaps as "N/A - Not in processed sections"
```

### Step 2: Template Application
- Use the structured format in [Reading-Template.md](references/Reading-Template.md)
- Fill in each section systematically
- Mark missing information as "N/A" or "Not Disclosed"

### Step 3: Technical Extraction
| Aspect | What to Extract | Example |
|--------|-----------------|---------|
| **Data** | Datasets, preprocessing steps, synthetic data | "BPE tokenization with 32k vocab" |
| **Model** | Architecture, novel components, parameters | "24 layers, 1024 hidden dim, GQA" |
| **Training** | Optimizer, LR schedule, batch size, hardware | "AdamW, cosine decay, 4M tokens/batch" |
| **Results** | Benchmarks, metrics, ablations | "+3.5% on MMLU vs. baseline" |

### Step 4: Critical Evaluation
- Identify specific benchmarks and their configurations
- Note limitations acknowledged by authors
- Flag potential weaknesses in methodology or evaluation

### Step 5: Output and Cleanup
- Output your report to {paper_name}.md under working directory
- Remove any unneeded files (e.g., `*.pdf`, `*.txt`)

### Step 6: Self-Review & Quality Check

**Before finalizing, verify your report against this checklist:**

#### Structure Completeness Check
| Section | Required Elements | ✓ |
|---------|-------------------|---|
| **TL;DR** | 3-5 sentences covering problem, method, results | ☐ |
| **§1 Problem** | Core problem + SOTA gap + importance | ☐ |
| **§2 Insights** | Key "aha" moment + contributions list | ☐ |
| **§3 Data** | Dataset table + preprocessing steps | ☐ |
| **§4 Model** | Architecture overview + key components + equations | ☐ |
| **§5 Training** | Strategy + hyperparameters + infrastructure | ☐ |
| **§6 Results** | Benchmark table + ablations | ☐ |
| **§7 Limits** | At least 2 limitations or future work items | ☐ |
| **§8 Reproducibility** | Code/Data/Weights availability table | ☐ |

#### Quality Standards Check
| Criterion | Requirement | ✓ |
|-----------|-------------|---|
| **Precision** | All numbers are exact (no "around", "approximately") | ☐ |
| **Tables** | Datasets and benchmarks use table format | ☐ |
| **N/A Handling** | Missing info marked as "N/A" or "Not Disclosed" | ☐ |
| **Math Format** | Equations use LaTeX: `$...$` or `$$...$$` | ☐ |
| **No Fluff** | No subjective praise ("excellent", "superior") | ☐ |
| **Citations** | Key claims reference specific sections/tables | ☐ |

#### Common Issues to Avoid
```
❌ Vague: "The model uses a large learning rate"
✅ Precise: "Learning rate: 1e-4 with cosine decay to 1e-6"

❌ Missing: (empty section)
✅ Explicit: "N/A - Not disclosed in paper"

❌ Subjective: "The results are impressive"
✅ Objective: "Achieves 85.3% on MMLU (+3.2% vs. Llama-2-70B)"
```

#### Final Validation
- [ ] All 8 template sections are present
- [ ] Paper title and metadata are filled
- [ ] At least one table exists (data or benchmarks)
- [ ] Report length is reasonable (not too short/long)

## Output Format

Your response MUST follow the template structure with these constraints:

1. **Precision:** Use exact values from the paper (e.g., "learning rate 3e-4", NOT "a standard learning rate")
2. **Objectivity:** Base claims on reported metrics; avoid subjective interpretations
3. **Completeness:** Explicitly mark unavailable information as "N/A"
4. **Structure:** Use tables for datasets and benchmark comparisons
5. **Math:** Use LaTeX notation for equations (e.g., `$\mathcal{L} = ...$`)

## Resources

### references/
- [Reading-Template.md](references/Reading-Template.md): The primary structured format for all paper deconstructions. Use this as the blueprint for your response.
- [download_paper.py](references/download_paper.py): Python utility for downloading papers from URLs.
- [chunk_paper.py](references/chunk_paper.py): Python utility for splitting large PDFs into manageable chunks.

## Utilities

### PDF Download Tool

When users provide a paper URL instead of a local file, use the download script:

```bash
# Download from arxiv (auto-normalizes URL)
python references/download_paper.py {URL}
```

**Supported Sources:**
| Source | URL Format | Example |
|--------|------------|---------|
| arXiv | `arxiv.org/abs/ID` or `arxiv.org/pdf/ID` | `https://arxiv.org/abs/2505.22596` |
| OpenReview | `openreview.net/pdf?id=ID` | `https://openreview.net/pdf?id=xxx` |
| Direct PDF | Any `.pdf` URL | `https://example.com/paper.pdf` |

**Features:**
- Auto-retry with configurable attempts (default: 3)
- URL normalization for arxiv (abs → pdf)
- PDF validation (checks `%PDF` signature)
- No external dependencies (uses stdlib only)

### PDF Chunking Tool

For large PDFs that exceed context window, use the chunking script:

```bash
# Basic usage (outputs to ./chunks/)
python references/chunk_paper.py paper.pdf

# Specify output directory
python references/chunk_paper.py paper.pdf ./my_chunks/

# Custom token limit per chunk
python references/chunk_paper.py paper.pdf ./chunks/ --max-tokens 3000
```

**Output Structure:**
```
chunks/
├── paper_manifest.json      # Chunk index with metadata
├── paper_chunk00_P0.txt     # Priority 0 (Abstract, Conclusion)
├── paper_chunk01_P1.txt     # Priority 1 (Methods, Experiments)
├── paper_chunk02_P2.txt     # Priority 2 (Introduction, Related Work)
└── ...
```

**Processing Workflow:**
1. Run chunker → generates prioritized chunks
2. Read `manifest.json` → understand structure
3. Process P0 chunks first → get core understanding
4. Process P1/P2 as needed → fill details
5. Merge into final report

**Requirements:**
```bash
pip install PyMuPDF
```
