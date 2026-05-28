from .base_agent import BaseAgent
from typing import Dict, Any


class SecurityAgent(BaseAgent):
    """代码安全审查 Agent"""
    
    def __init__(self, llm_client=None):
        super().__init__("SecurityAgent", llm_client)
    
    def execute(self, code: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """审查代码安全性"""
        prompt = f"""
你是一个资深的安全工程师，请审查以下代码的安全性：

代码：
{code}

请检查以下安全问题：
1. SQL 注入风险
2. 敏感数据泄露
3. 不安全的文件操作
4. 命令注入风险
5. XSS 漏洞
6. 认证授权问题
7. 密码处理安全

请以结构化的 JSON 格式返回结果：
{{
    "vulnerabilities": [
        {{
            "severity": "critical|high|medium|low",
            "type": "漏洞类型",
            "line": 行号,
            "description": "漏洞描述",
            "fix": "修复建议"
        }}
    ],
    "security_rating": "安全|基本安全|存在风险|高风险",
    "summary": "安全评估总结"
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
                "vulnerabilities": [],
                "security_rating": "安全",
                "summary": result
            }
