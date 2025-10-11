import json
import asyncio
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

@dataclass
class ScoringRubric:
    """评分细则数据类"""
    compilability_weight: float = 1      # 可编译性权重 20%
    correctness_weight: float = 1        # 正确性权重 50%
    code_quality_weight: float = 1       # 代码质量权重 20%
    readability_weight: float = 1        # 可读性权重 10%

@dataclass
class CodeContext:
    """代码上下文信息"""
    problem_description: str               # 题目描述
    recognized_code: str                   # OCR识别后的代码
    compile_log: str                       # 编译日志
    test_results: Dict[str, bool]         # 测试用例结果
    error_messages: List[str]              # 错误信息
    warning_messages: List[str]            # 警告信息

@dataclass
class LLMScore:
    """LLM评分结果"""
    scores: Dict[str, float]              # 各维度分数
    total_score: float                    # 总分
    rationale: str                        # 评分理由
    suggestions: List[str]                # 改进建议
    confidence: float                     # 置信度
    raw_response: Dict                    # 原始响应

class ScoringStrategy(Enum):
    RULE_BASED = "rule_based"
    LLM_ONLY = "llm_only"
    FUSION = "fusion"