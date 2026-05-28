from .base_agent import BaseAgent
from typing import Dict, Any


class CodeReviewAgent(BaseAgent):
    """代码逻辑审查 Agent"""
    
    def __init__(self, llm_client=None):
        super().__init__("CodeReviewAgent", llm_client)
    
    def execute(self, code: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """审查代码逻辑正确性"""
        prompt = f"""
你是一个资深的 Python 开发者，请审查以下代码的逻辑正确性：

代码：
{code}

请从以下方面进行审查：
1. 逻辑正确性：代码是否实现了预期功能
2. 算法效率：是否有性能优化空间
3. 边界处理：是否考虑了异常情况
4. 潜在 Bug：是否存在逻辑缺陷

请以结构化的 JSON 格式返回结果：
{{
    "issues": [
        {{
            "severity": "high|medium|low",
            "line": 行号,
            "description": "问题描述",
            "suggestion": "修复建议"
        }}
    ],
    "overall_quality": "优秀|良好|一般|较差",
    "summary": "总结"
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
                "issues": [],
                "overall_quality": "良好",
                "summary": result
            }
