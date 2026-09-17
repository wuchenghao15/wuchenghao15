# English Coreference Module

该目录是英文指代消解的规则式实现（与中文实现对齐：实体跟踪 + 代词分类 + 保守策略）。

## 快速开始
1. 安装依赖（推荐 spaCy）：
   - `pip install spacy`
   - `python -m spacy download en_core_web_sm`
2. 运行评测：
   - `python english_coreference/eval_round1.py`

## 结构
- `tokenizer.py`：英文分句/分词/NP 抽取
- `ner_adapter.py`：NER 结果归一化
- `coreference.py`：核心指代消解逻辑
- `eval_round1.py`：自测脚本
