from .base_agent import BaseAgent
from typing import Dict, Any


class SummarizerAgent(BaseAgent):
    """总结 Agent - 汇总所有审查结果"""
    
    def __init__(self, llm_client=None):
        super().__init__("SummarizerAgent", llm_client)
    
    def execute(self, code: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """汇总所有审查结果"""
        if not context:
            return {"summary": "没有审查结果需要汇总"}
        
        prompt = f"""
你是一个代码审查报告专家，请汇总以下代码审查结果：

原始代码：
{code}

审查结果：
{context}

请生成一份结构化的审查报告，包含：
1. 整体评估
2. 问题分类统计
3. 优先级排序的问题列表
4. 改进建议

请以结构化的 JSON 格式返回：
{{
    "overall_rating": "优秀|良好|一般|较差",
    "total_issues": 问题总数,
    "high_severity_count": 高优先级问题数,
    "summary": "整体总结",
    "recommendations": ["建议1", "建议2", "建议3"],
    "detailed_report": "详细报告文本"
}}
"""
        
        result = self.call_llm(prompt)
        return self._parse_result(result)
    
    def _parse_result(self, result: str) -> Dict[str, Any]:
        """解析 LLM 返回结果"""
        import json
        try:
            return json.loads(result)
        except:
            return {
                "overall_rating": "良好",
                "total_issues": 0,
                "high_severity_count": 0,
                "summary": result,
                "recommendations": [],
                "detailed_report": result
            }
