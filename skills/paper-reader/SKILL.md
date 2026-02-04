---
name: paper-reader
description: Expert skill for deconstructing deep learning research papers into structured technical summaries. Use this skill when the user provides a paper (via PDF, ArXiv link, or text) and needs a detailed analysis of the problem, insights, data, model architecture, training, benchmarks, and limitations.
---

# Deep Learning Paper Reader

## Overview
This skill provides a rigorous framework for reading and deconstructing deep learning research papers. It ensures all critical technical aspects—from data curation to architectural details and training hyperparameters—are extracted and organized systematically.

## Workflow

When analyzing a paper, follow this sequence:

1. **Information Gathering**: Read the entire paper (or provided sections). Pay close attention to the Abstract, Introduction, Methodology, Experiments, and Conclusion.
2. **Template Application**: Use the structured format defined in [Reading-Template.md](references/Reading-Template.md) to organize the information.
3. **Technical Extraction**:
    - **Data**: Identify every dataset mentioned and the specific preprocessing steps (e.g., "normalized to [0, 1]", "BPE tokenization with 32k vocab").
    - **Model**: Describe the architecture layers, novel components, and parameters.
    - **Training**: Extract the exact optimizer, learning rate schedule, batch size, and hardware used.
4. **Critical Evaluation**: Identify not just the results, but the specific benchmarks used and any potential limitations noted by the authors or observed in the methodology.

## Resources

### references/
- [Reading-Template.md](references/Reading-Template.md): The primary structured format for all paper deconstructions. Use this as the blueprint for your response.