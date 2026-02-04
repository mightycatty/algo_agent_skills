# Deep Learning Paper Analysis Template

Use this template to deconstruct deep learning papers into a structured format. Keep narratives concise and precise.

> **Constraints:**
> - **Precision:** Extract exact values (e.g., "learning rate 3e-4", not "a standard learning rate").
> - **Objectivity:** Rely on reported metrics; avoid subjective claims unless substantiated.
> - **Completeness:** If information is not disclosed, explicitly mark as "N/A" or "Not Disclosed".

**Paper Title:** {title of the paper}
**Publication Date:** {year/month when the paper is published}
**Authors/Affiliation:** {author names and institutions}

---

## TL;DR
> {3-5 sentences summarizing: What problem does this paper solve? What is the key method? What are the main results?}

---

## 1. Problem Definition
- **What is the core problem?**
- **Why is it important/challenging?**
- **What are the limitations of existing solutions (SOTA gap)?**

## 2. Main Insights & Contributions
- **What are the key ideas or "aha" moments?**
- **What are the primary contributions (theoretical, empirical, or architectural)?**

## 3. Data Summary, Curation & Processing

| Dataset | Domain | Scale | Source |
|---------|--------|-------|--------|
| {name}  | {type} | {size}| {link} |

- **Curation process:** How was the data collected/filtered?
- **Processing procedures:**
  - Tokenization (for NLP) / Augmentation (for CV)
  - Normalization and cleaning steps
  - Synthetic data generation (if applicable)

## 4. Model Design
- **Architecture Overview:** (e.g., Transformer-based, CNN, Diffusion)
- **Architecture Diagram:** (describe or draw the model structure)
- **Key Components:** Detailed description of novel blocks, layers, or loss functions.
- **Mathematical Formulation:** Key equations defining the model behavior.
  - Use LaTeX format: $\mathcal{L} = ...$

## 5. Detailed Training Procedures
- **Workflow Diagram:** (describe the training pipeline stages)
- **Training Strategy:** (e.g., pre-training → SFT → RLHF)
- **Optimizer & Hyperparameters:**
  - Optimizer: (e.g., AdamW with $\beta_1=0.9$, $\beta_2=0.999$)
  - Learning Rate: (max/min, schedule type, warmup steps)
  - Batch Size: (global batch size in tokens/sequences)
  - Weight Decay / Dropout / Gradient Clipping
- **Infrastructure:**
  - Hardware: (e.g., 2048 H100 GPUs)
  - Training Duration: (e.g., 14 days, 2T tokens)
  - Framework: (e.g., PyTorch, JAX)

## 6. Benchmark Results

| Benchmark | Metric | This Work | Baseline | Δ |
|-----------|--------|-----------|----------|---|
| {name}    | {metric}| {score}  | {score}  |{+/-}|

- **Evaluation Metrics:** (e.g., Accuracy, F1, Perplexity, FID)
- **Comparative Analysis:** Performance vs. SOTA models.
- **Ablation Studies:** Which components contribute most to the performance?

## 7. Limitations & Future Work
- **Computational Cost:** Inference latency, training resource requirements.
- **Generalization:** Performance on edge cases or OOD data.
- **Safety & Bias:** Any noted ethical concerns or biases in the model/data.
- **Complexity vs. Gains:** Is the method overly complex compared to the improvements?
- **Open Questions:** What did the authors leave for future research?

## 8. Reproducibility

| Aspect | Status | Details |
|--------|--------|---------|
| **Code** | {✅ Available / ❌ Not Released} | {GitHub link or N/A} |
| **Data** | {✅ Public / ⚠️ Partial / ❌ Proprietary} | {Dataset link or access info} |
| **Weights** | {✅ Available / ❌ Not Released} | {HuggingFace/Model link or N/A} |

- **Sufficient Details:** Are hyperparameters, configurations, and training steps fully disclosed?
- **Hardware Requirements:** What compute is needed to reproduce? (e.g., "8× A100 for fine-tuning")
- **Reproducibility Notes:** Any caveats or known issues with reproduction?

---

## Section Completion Criteria

> Use this checklist to verify each section meets the quality bar before submission.

| Section | Minimum Requirements | Quality Indicators |
|---------|---------------------|-------------------|
| **TL;DR** | 3-5 complete sentences | Covers problem, method, and quantitative result |
| **§1 Problem** | All 3 bullet points answered | Specific SOTA gap identified with citations |
| **§2 Insights** | At least 1 key insight + 2 contributions | "Aha" moment clearly articulated |
| **§3 Data** | Table with ≥1 dataset row | Preprocessing steps listed |
| **§4 Model** | Architecture type + ≥1 equation | Novel components explained in detail |
| **§5 Training** | Optimizer + LR + batch size filled | Infrastructure section complete |
| **§6 Results** | Table with ≥2 benchmark rows | Ablation findings summarized |
| **§7 Limits** | ≥2 limitations listed | Future work mentioned |
| **§8 Reproducibility** | All 3 table rows filled | Hardware requirements specified |

### Acceptable "N/A" Usage

Mark as "N/A" or "Not Disclosed" **only** when:
- Information is genuinely not present in the paper
- After checking: Abstract, Methods, Experiments, Appendix, and Supplementary materials

**Do NOT use N/A for:**
- Information you haven't looked for yet
- Sections you skipped due to time constraints
- Details that require inference but are derivable from context
