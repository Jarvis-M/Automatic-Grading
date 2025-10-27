# scoring/llm/llm_only_engine.py
import logging
import asyncio
from typing import Dict, Any
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from scoring.llm.deepseek_scorer import LLMScore, CodeContext
from scoring.llm.moonshot_client import MoonshotClient

class LLMOnlyScoringEngine:
    """纯LLM评分引擎"""

    def __init__(self, api_key: str):
        self.llm_client = MoonshotClient(api_key)
        logging.info("LLM客户端初始化成功")

    async def score(self, context: CodeContext) -> Dict[str, Any]:
        """执行纯LLM评分"""
        try:
            prompt = self._build_scoring_prompt(context)
            logging.info(f"构建的提示词长度: {len(prompt)}")
            
            llm_score = await self._get_llm_score(prompt)
            return self._format_result(llm_score)

        except Exception as e:
            logging.error(f"LLM评分失败: {e}")
            return self._format_error_result(str(e))

    async def _get_llm_score(self, prompt: str) -> LLMScore:
        """获取LLM评分"""
        # 由于MoonshotClient是同步的，使用线程池执行
        return await asyncio.get_event_loop().run_in_executor(
            None, self.llm_client.score_code, prompt
        )

    def _build_scoring_prompt(self, context: CodeContext) -> str:
        """构建评分提示词"""
        
        # 构建测试结果摘要
        if context.test_results:
            passed = sum(context.test_results.values())
            total = len(context.test_results)
            test_summary = f"通过 {passed}/{total} 个测试用例"
        else:
            test_summary = "无测试用例"

        prompt = f"""
你是一个严谨的C++编程助教。由于代码来自OCR识别，可能存在字符识别错误。请以宽容的态度对以下代码进行评分：

评分原则：
1. 重点关注代码的整体结构和逻辑意图，忽略明显的OCR识别错误
2. 对于疑似识别错误的字符，尝试推断原本的正确代码
3. 评分时考虑"如果代码完整正确应该能得多少分"，然后适当扣分
4. 即使代码不完整，也要肯定其中正确的部分

评分维度（宽松标准）：
- 可编译性（20分）：能看出基本框架就给基础分10分
- 正确性（50分）：根据逻辑完整性给分，有主要结构就给30分起
- 代码质量（20分）：有基本结构就给15分起  
- 可读性（10分）：有代码结构就给8分起

请先分析代码中可能的OCR识别错误，然后给出鼓励性的评分和改进建议。

题目描述：
{context.problem_description}

学生代码：
```cpp
{context.recognized_code}
编译信息：{context.compile_log or '无编译错误'}
测试结果：{test_summary}

请严格按照以下JSON格式返回结果：
{{
"scores": {{
"compilability": 分数（0-20）,
"correctness": 分数（0-50）,
"code_quality": 分数（0-20）,
"readability": 分数（0-10）
}},
"total": 总分（0-100）,
"rationale": "详细的评分理由",
"suggestions": ["改进建议1", "改进建议2", "..."],
"confidence": 置信度（0.0-1.0）
}}

请确保总分等于各分项分数之和，并提供具体、可操作的改进建议。
"""
        return prompt
    
    def _format_result(self, llm_score: LLMScore) -> Dict[str, Any]:
        return {
            "final_score": llm_score.total_score,
            "strategy": "llm_only",
            "score_breakdown": {
                "scores": llm_score.scores,
                "total": llm_score.total_score,
                "rationale": llm_score.rationale,
                "suggestions": llm_score.suggestions,
                "confidence": llm_score.confidence
            },
            "needs_manual_review": llm_score.confidence < 0.7,
            "review_reason": "置信度较低，建议人工复核" if llm_score.confidence < 0.7 else "",
            "success": True
        }

    def _format_error_result(self, error_message: str) -> Dict[str, Any]:
        """格式化错误结果"""
        return {
            "final_score": 0,
            "strategy": "error",
            "score_breakdown": None,
            "needs_manual_review": True,
            "review_reason": f"评分失败: {error_message}",
            "success": False,
            "error": error_message
        }