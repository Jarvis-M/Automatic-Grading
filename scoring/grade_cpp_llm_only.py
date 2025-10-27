# import asyncio
# import sys
# import os
# import logging

# # 添加当前目录到Python路径
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# from llm.deepseek_scorer import CodeContext
# from llm.llm_only_engine import LLMOnlyScoringEngine

# # 设置日志
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger(__name__)

# async def grade_cpp_file_llm_only(problem_description: str, cpp_file_path: str,
#                                  compile_log: str = "", test_results: dict = None,
#                                  error_messages: list = None, warning_messages: list = None):
#     """
#     对CPP文件进行纯LLM评分

#     Args:
#         problem_description: 题目描述
#         cpp_file_path: CPP文件路径
#         compile_log: 编译日志
#         test_results: 测试结果字典 {测试用例名: 是否通过}
#         error_messages: 错误信息列表
#         warning_messages: 警告信息列表
#     """

#     try:
#         # 读取CPP文件内容
#         with open(cpp_file_path, 'r', encoding='utf-8') as f:
#             code_content = f.read()

#         # 构建代码上下文
#         context = CodeContext(
#             problem_description=problem_description,
#             recognized_code=code_content,
#             compile_log=compile_log or "",
#             test_results=test_results or {},
#             error_messages=error_messages or [],
#             warning_messages=warning_messages or []
#         )

#         # 初始化纯LLM评分引擎
#         api_key = "sk-lszpP34FkMmgW6JyZURgKpRx9G6ld9zJJNTDiDHEpU9AMBzX"  # 你的API密钥
        
#         if not api_key:
#             return {
#                 "final_score": 0,
#                 "strategy": "error",
#                 "error": "API密钥未设置",
#                 "success": False
#             }

#         engine = LLMOnlyScoringEngine(api_key)
#         result = await engine.score(context)
#         return result

#     except FileNotFoundError:
#         logger.error(f"文件未找到: {cpp_file_path}")
#         return {
#             "final_score": 0,
#             "strategy": "error",
#             "error": f"文件未找到: {cpp_file_path}",
#             "success": False
#         }
#     except Exception as e:
#         logger.error(f"评分过程中发生错误: {e}")
#         return {
#             "final_score": 0,
#             "strategy": "error",
#             "error": str(e),
#             "success": False
#         }

# def print_llm_result(result):
#     """打印LLM评分结果"""
#     print("=" * 60)
#     print("LLM评分结果:")
#     print("=" * 60)

#     if not result.get("success", False):
#         print(f"❌ 评分失败: {result.get('error', '未知错误')}")
#         return

#     print(f"✅ 最终分数: {result['final_score']:.2f}")
#     print(f"📋 评分策略: {result['strategy']}")
#     print(f"🔍 需要人工复核: {result['needs_manual_review']}")
    
#     if result['needs_manual_review']:
#         print(f"📝 复核原因: {result['review_reason']}")

#     # 打印详细评分
#     if result.get('score_breakdown'):
#         breakdown = result['score_breakdown']
#         print("\n📊 详细评分:")
#         print("-" * 40)
        
#         scores = breakdown.get('scores', {})
#         print(f"• 可编译性: {scores.get('compilability', 0):.2f}/20")
#         print(f"• 正确性: {scores.get('correctness', 0):.2f}/50")
#         print(f"• 代码质量: {scores.get('code_quality', 0):.2f}/20")
#         print(f"• 可读性: {scores.get('readability', 0):.2f}/10")
#         print(f"• 总分: {breakdown.get('total', 0):.2f}/100")
#         print(f"• 置信度: {breakdown.get('confidence', 0):.2f}")

#         # 显示评分理由
#         rationale = breakdown.get('rationale', '')
#         if rationale:
#             print(f"\n💡 评分理由:")
#             print(f"  {rationale}")

#         # 显示改进建议
#         suggestions = breakdown.get('suggestions', [])
#         if suggestions:
#             print(f"\n🎯 改进建议:")
#             for i, suggestion in enumerate(suggestions, 1):
#                 print(f"  {i}. {suggestion}")

# async def main():
#     """示例用法"""
#     # 示例参数
#     problem_desc = "编写一个C++程序，计算两个整数的和"
#     cpp_file = r"E:\VScode\Python\recognition_c\Automatic-Grading\scoring\example.cpp"  # 替换为你的CPP文件路径

#     # 可选参数
#     # compile_log = "编译成功，无错误"
#     # error_messages = []
#     # warning_messages = ["变量命名不规范"]

#     print("🚀 开始LLM评分...")
    
#     try:
#         result = await grade_cpp_file_llm_only(
#             problem_desc, cpp_file
#             # , compile_log,
#             # test_results, error_messages, warning_messages
#         )

#         print_llm_result(result)

#     except Exception as e:
#         print(f"❌ 评分失败: {e}")

# if __name__ == "__main__":
#     asyncio.run(main())

import asyncio
import sys
import os
import logging
import json
from typing import Dict, Any

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from llm.deepseek_scorer import CodeContext
from llm.llm_only_engine import LLMOnlyScoringEngine

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 定义JSON文件保存路径
SCORING_RESULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scoring_result.json")

async def grade_cpp_file_llm_only(problem_description: str, cpp_file_path: str,
                                 compile_log: str = "", test_results: dict = None,
                                 error_messages: list = None, warning_messages: list = None) -> Dict[str, Any]:
    """
    对CPP文件进行纯LLM评分

    Args:
        problem_description: 题目描述
        cpp_file_path: CPP文件路径
        compile_log: 编译日志
        test_results: 测试结果字典 {测试用例名: 是否通过}
        error_messages: 错误信息列表
        warning_messages: 警告信息列表

    Returns:
        JSON格式的评分结果
    """

    try:
        # 读取CPP文件内容
        with open(cpp_file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()

        # 构建代码上下文
        context = CodeContext(
            problem_description=problem_description,
            recognized_code=code_content,
            compile_log=compile_log or "",
            test_results=test_results or {},
            error_messages=error_messages or [],
            warning_messages=warning_messages or []
        )

        # 初始化纯LLM评分引擎
        api_key = "sk-lszpP34FkMmgW6JyZURgKpRx9G6ld9zJJNTDiDHEpU9AMBzX"  # 你的API密钥
        
        if not api_key:
            error_result = {
                "success": False,
                "error": "API密钥未设置",
                "final_score": 0,
                "strategy": "error"
            }
            save_result_to_json(error_result)
            return error_result

        engine = LLMOnlyScoringEngine(api_key)
        result = await engine.score(context)
        print("11111")
        print(result)
        print("11111")
        # 保存结果到指定路径
        save_result_to_json(result)
        
        return result
    

    except FileNotFoundError:
        logger.error(f"文件未找到: {cpp_file_path}")
        error_result = {
            "success": False,
            "error": f"文件未找到: {cpp_file_path}",
            "final_score": 0,
            "strategy": "error"
        }
        save_result_to_json(error_result)
        return error_result
        
    except Exception as e:
        logger.error(f"评分过程中发生错误: {e}")
        error_result = {
            "success": False,
            "error": str(e),
            "final_score": 0,
            "strategy": "error"
        }
        save_result_to_json(error_result)
        return error_result

def format_llm_result_for_api(result: Dict[str, Any]) -> Dict[str, Any]:
    """
    将LLM评分结果格式化为API响应格式
    
    Args:
        result: LLM评分结果
        
    Returns:
        API响应格式的字典
    """
    if not result.get("success", False):
        return {
            "success": False,
            "error": result.get("error", "未知错误"),
            "final_score": 0
        }

    # 构建标准化的API响应
    api_response = {
        "success": True,
        "final_score": result.get("final_score", 0),
        "strategy": result.get("strategy", "llm_only"),
        "needs_manual_review": result.get("needs_manual_review", False),
        "review_reason": result.get("review_reason", "")
    }

    # 添加详细的评分分解
    if result.get('score_breakdown'):
        breakdown = result['score_breakdown']
        
        # 分数详情
        scores = breakdown.get('scores', {})
        score_details = {
            "compilability": scores.get('compilability', 0),
            "correctness": scores.get('correctness', 0),
            "code_quality": scores.get('code_quality', 0),
            "readability": scores.get('readability', 0),
            "total": breakdown.get('total', 0),
            "confidence": breakdown.get('confidence', 0)
        }
        
        api_response["score_breakdown"] = score_details
        
        # 评分理由
        rationale = breakdown.get('rationale', '')
        if rationale:
            api_response["rationale"] = rationale
        
        # 改进建议
        suggestions = breakdown.get('suggestions', [])
        if suggestions:
            api_response["suggestions"] = suggestions

    return api_response

def save_result_to_json(result: Dict[str, Any], filename: str = None):
    """
    将评分结果保存为JSON文件到指定路径
    
    Args:
        result: 评分结果
        filename: 保存的文件名，如果为None则使用默认路径
    """
    try:
        if filename is None:
            filepath = SCORING_RESULT_PATH
        else:
            # 如果提供了相对路径，转换为绝对路径
            if not os.path.isabs(filename):
                filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)
            else:
                filepath = filename
        
        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        logger.info(f"评分结果已保存到: {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"保存JSON文件失败: {e}")
        return None

def print_llm_result(result):
    """打印LLM评分结果（用于命令行调试）"""
    print("=" * 60)
    print("LLM评分结果:")
    print("=" * 60)

    if not result.get("success", False):
        print(f"❌ 评分失败: {result.get('error', '未知错误')}")
        return

    print(f"✅ 最终分数: {result['final_score']:.2f}")
    print(f"📋 评分策略: {result['strategy']}")
    print(f"🔍 需要人工复核: {result['needs_manual_review']}")
    
    if result['needs_manual_review']:
        print(f"📝 复核原因: {result['review_reason']}")

    # 打印详细评分
    if result.get('score_breakdown'):
        breakdown = result['score_breakdown']
        print("\n📊 详细评分:")
        print("-" * 40)
        
        scores = breakdown.get('scores', {})
        print(f"• 可编译性: {scores.get('compilability', 0):.2f}/20")
        print(f"• 正确性: {scores.get('correctness', 0):.2f}/50")
        print(f"• 代码质量: {scores.get('code_quality', 0):.2f}/20")
        print(f"• 可读性: {scores.get('readability', 0):.2f}/10")
        print(f"• 总分: {breakdown.get('total', 0):.2f}/100")
        print(f"• 置信度: {breakdown.get('confidence', 0):.2f}")

        # 显示评分理由
        rationale = breakdown.get('rationale', '')
        if rationale:
            print(f"\n💡 评分理由:")
            print(f"  {rationale}")

        # 显示改进建议
        suggestions = breakdown.get('suggestions', [])
        if suggestions:
            print(f"\n🎯 改进建议:")
            for i, suggestion in enumerate(suggestions, 1):
                print(f"  {i}. {suggestion}")

async def main():
    """示例用法（用于测试）"""
    # 示例参数
    problem_desc = "编写一个C++程序，计算两个整数的和"
    cpp_file = r"E:\VScode\Python\recognition_c\Automatic-Grading\scoring\example.cpp"

    print("🚀 开始LLM评分...")
    
    try:
        # 获取评分结果
        result = await grade_cpp_file_llm_only(problem_desc, cpp_file)
        
        # 格式化为API响应格式
        api_response = format_llm_result_for_api(result)
        
        # 打印结果（用于调试）
        print_llm_result(result)
        
        # 打印JSON格式（用于查看API响应）
        print("\n📄 JSON格式响应:")
        print(json.dumps(api_response, ensure_ascii=False, indent=2))
        
        # 打印保存路径
        print(f"\n💾 结果已保存到: {SCORING_RESULT_PATH}")

    except Exception as e:
        print(f"❌ 评分失败: {e}")

if __name__ == "__main__":
    asyncio.run(main())