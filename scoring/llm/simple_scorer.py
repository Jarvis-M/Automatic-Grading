# scoring/llm/simple_scorer.py
from dataclasses import dataclass
from typing import Dict, List

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