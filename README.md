<p align="center">
<img width="311" height="248" alt="image" src="https://github.com/user-attachments/assets/0283356e-30ea-456e-9745-34e3e7623426" />
</p>

# MeasHalu: Mitigation of Scientific Measurement Hallucinations for Large Language Models with Enhanced Reasoning

[![ACL 2026 Findings](https://img.shields.io/badge/ACL%202026-Findings-blue)](https://aclanthology.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)


MeasHalu is a framework for mitigating scientific measurement hallucinations in large language models through fine-grained taxonomy, reasoning-aware fine-tuning, and progressive reward curriculum optimization.

---

## 📰 News

- **[2026.04]** 🎉 MeasHalu has been accepted to **ACL 2026 Findings**!

---


## 🎯 Overview

<p align="right">
  <img align="right" width="300" alt="motivation_01(2)" src="https://github.com/user-attachments/assets/0935d170-57b8-4a86-9cde-b86d2fac4c07" />
</p>

Accurate extraction of scientific measurements from literature is critical for AI4Science. However, LLMs frequently exhibit severe hallucinations when extracting metric information (quantities, units, modifiers, and relations), which significantly undermines the reliability of automated scientific document understanding.



**MeasHalu** addresses this problem through three key innovations:

1. **Fine-grained Hallucination Taxonomy**: We categorize measurement-specific hallucinations into four types — quantity errors, unit errors, modifier errors, and relation errors.
2. **Two-Stage Reasoning-Aware Fine-Tuning**: Process-based supervision with augmented scientific data to improve extraction faithfulness.
3. **Progressive Reward Curriculum**: Type-specific penalties that gradually increase in difficulty, substantially improving reasoning stability.
<img width="1920" height="1080" alt="meashalu-framework(2)_03(3)" src="https://github.com/user-attachments/assets/cff3e9aa-92e7-4799-89f2-ac8294a785f1" />

---

## 🏆 Key Results

### MeasEval Benchmark (Complex Quantitative Relation Extraction)

| Model | F1 Score |
|------|:--------:|
| **MeasHalu-7B** | **0.512** |
| LIORI (Competition Winner) | 0.519 |
| GPT-5 (w/ optimized prompting) | 0.406 |
| Gemini-2.5-Pro (w/ optimized prompting) | 0.440 |
| CONNER | 0.473 |
| Counts | 0.432 |

**MeasHalu-7B matches the competition winner and outperforms GPT-5 by over 10 F1 points**, demonstrating the necessity of quantitative domain alignment (SFT + composite reward optimization) for mitigating relational quantity hallucinations.

### Fine-grained Entropy Analysis

GRPO training substantially improves reasoning stability, especially for ambiguous relational reasoning:

| Semantic Role | Entropy Reduction | Spike Ratio Reduction |
|:-------------:|:-----------------:|:---------------------:|
| **Quantity** | ↓ 52.1% | Minimal fluctuation |
| **Relation** | ↓ 42.3% | ↓ 56.8% |

---

## 🤖 Embodied AI Application

To validate the practical value of fine-grained extraction for embodied AI, we adapt **OpenExp** to a **text-to-action generation** task. Models generate **executable chemical action sequences** (e.g., `ADD (100 mg)`, `HEAT (80°C)`) directly from unstructured experimental text, mimicking real-world automated laboratory scenarios.

```
Input:  "将100mg样品加入溶液，加热至80°C"
                ↓
        MeasHalu Extraction
                ↓
Output: ADD(100 mg)
        HEAT(80°C)
```

This demonstrates MeasHalu's capability to bridge scientific literature understanding and robotic execution.

---

## 📁 Repository Structure

```
MeasHalu/
├── data/                    # Dataset processing scripts
├── src/
│   ├── taxonomy/           # Fine-grained hallucination taxonomy
│   ├── training/           # SFT + GRPO training pipeline
│   ├── evaluation/         # MeasEval and MeasEval-Ext evaluators
│   └── embodied/           # OpenExp text-to-action adaptation
├── configs/                # Training and model configurations
├── experiments/            # Experiment logs and results
├── requirements.txt
└── README.md
```

---

## 🚀 Quick Start

### Installation

```bash
git clone https://github.com/Vimos/MeasHalu.git
cd MeasHalu
pip install -r requirements.txt
```

### Data Preparation

```bash
python data/prepare_measeval.py
python data/prepare_taxonomy.py
```

### Training

```bash
# Stage 1: SFT with reasoning-aware data
python src/training/sft.py --config configs/sft_config.yaml

# Stage 2: GRPO with progressive reward curriculum
python src/training/grpo.py --config configs/grpo_config.yaml
```

### Evaluation

```bash
python src/evaluation/eval_measeval.py --model_path checkpoints/meashalu_7b
```

### Embodied AI Demo

```bash
python src/embodied/openexp_demo.py --input "your_experimental_text.txt"
```

---

## 📊 MeasBench

MeasHalu will also serve as a core component of **MeasureMind**, a universal numerical reasoning enhancement framework. For the comprehensive benchmark (MeasBench), please stay tuned for our follow-up work.

---

## 📖 Citation

If you find this work useful, please consider citing:

```bibtex
@inproceedings{
anonymous2026meashalu,
title={MeasHalu: Mitigation of Scientific Measurement Hallucinations for Large Language Models with Enhanced Reasoning},
author={Ruijun Huang, Zhiqiao Kang, Yuxuan Zhu, Junxiong Li, Jiahao Zhao, Minghuan Tan, Feng Jiang, Min Yang},
booktitle={The 64th Annual Meeting of the Association for Computational Linguistics},
year={2026},
url={https://openreview.net/forum?id=bQJbqHcsPk}
}
```

---

## 🔗 Related Work

- **NUMCoT** (ACL 2024 Findings): Reveals LLM failures in numerical chain-of-thought reasoning

---

## 📧 Contact

For questions or collaborations, please open an issue or contact the authors.

---

*This project is part of our ongoing research on reliable numerical reasoning for AI4Science and embodied intelligence.*
