from .base_agent import BaseAgent
from typing import Dict, Any


class StyleAgent(BaseAgent):
    """代码风格审查 Agent"""
    
    def __init__(self, llm_client=None):
        super().__init__("StyleAgent", llm_client)
    
    def execute(self, code: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """审查代码风格"""
        prompt = f"""
你是一个资深的代码规范专家，请根据 PEP 8 规范审查以下 Python 代码的风格：

代码：
{code}

请检查以下方面：
1. 命名规范：变量、函数、类的命名
2. 缩进：4 空格缩进
3. 空行：适当的空行分隔
4. 注释：代码注释的完整性
5. 行长度：每行不超过 79 字符
6. 导入顺序：标准库、第三方库、本地模块
7. 代码可读性：变量命名是否清晰

请以结构化的 JSON 格式返回结果：
{{
    "style_issues": [
        {{
            "type": "问题类型",
            "line": 行号,
            "description": "问题描述",
            "suggestion": "优化建议"
        }}
    ],
    "style_score": 0-100,
    "summary": "风格评估总结"
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
                "style_issues": [],
                "style_score": 80,
                "summary": result
            }
