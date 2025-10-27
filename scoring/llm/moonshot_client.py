import os
import time
import json
import logging
from typing import Dict, Any
from openai import OpenAI
from scoring.llm.deepseek_scorer import LLMScore

logger = logging.getLogger(__name__)

class MoonshotClient:

    """Moonshot API客户端（使用OpenAI SDK）"""
    
    def __init__(self, api_key: str, base_url: str = "https://api.moonshot.cn/v1"):
        self.client = OpenAI(
            api_key="sk-lszpP34FkMmgW6JyZURgKpRx9G6ld9zJJNTDiDHEpU9AMBzX",  # 替换为你的API密钥
            base_url=base_url,
        )
        self.model = "moonshot-v1-8k"  # 使用支持的模型
    
    def score_code(self, prompt: str, max_retries: int = 3) -> LLMScore:
        """调用Moonshot进行代码评分"""
        
        # 检查提示词是否为空
        if not prompt or not prompt.strip():
            raise ValueError("提示词不能为空")
        
        for attempt in range(max_retries):
            try:
                # 构建消息历史
                messages = [
                    {
                        "role": "system", 
                        "content": "你是严谨的C++编程作业助教。请基于评分细则对C++作业给出分项评分与改进建议，并输出严格的JSON格式。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
                
                logger.info(f"发送请求到Moonshot API，提示词长度: {len(prompt)}")
                
                completion = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=0.1,  # 低温度保证稳定性
                    max_tokens=2000,
                )
                
                content = completion.choices[0].message.content
                logger.info(f"收到API响应，内容长度: {len(content)}")
                
                # 解析JSON响应
                score_data = self._parse_llm_response(content)
                return LLMScore(**score_data, raw_response=completion.to_dict())
                
            except Exception as e:
                logger.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                # 指数退避
                wait_time = 2 ** attempt
                time.sleep(wait_time)
        
        raise Exception("Max retries exceeded")
    
    def _parse_llm_response(self, content: str) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            # 尝试提取JSON部分（可能LLM会在JSON前后添加其他文本）
            json_start = content.find('{')
            json_end = content.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                content = content[json_start:json_end]
            
            data = json.loads(content)

            # 验证必需字段
            required_fields = ["scores", "total", "rationale", "suggestions"]
            if not all(field in data for field in required_fields):
                raise ValueError("Missing required fields in LLM response")

            # 验证分数范围
            if not 0 <= data["total"] <= 100:
                raise ValueError("Total score out of range")

            return {
                "scores": data["scores"],
                "total_score": data["total"],
                "rationale": data["rationale"],
                "suggestions": data["suggestions"],
                "confidence": data.get("confidence", 0.8)
            }

        except (json.JSONDecodeError, ValueError) as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.error(f"Raw response content: {content}")
            # 返回默认错误响应
            return {
                "scores": {"compilability": 0, "correctness": 0, "code_quality": 0, "readability": 0},
                "total_score": 0,
                "rationale": "解析评分响应失败",
                "suggestions": ["请检查代码格式和完整性"],
                "confidence": 0.1
            }