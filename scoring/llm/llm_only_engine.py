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
你是一个严谨的C++编程作业助教。请对以下C++代码进行评分并提供改进建议。

评分细则：
- 可编译性（20分）：代码能否一次编译通过，错误类型与数量
- 正确性（50分）：代码是否能完成题目要求，逻辑正确性
- 代码质量（20分）：命名规范、代码结构、复杂度、冗余度，无需异常处理
- 文档与可读性（10分）：注释质量、代码清晰度

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