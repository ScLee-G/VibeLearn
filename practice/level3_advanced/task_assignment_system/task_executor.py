from .base_agent import BaseAgent
from typing import Dict, Any


class TaskExecutor(BaseAgent):
    """任务执行 Agent"""
    
    def __init__(self, llm_client=None):
        super().__init__("TaskExecutor", llm_client)
    
    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行具体任务"""
        prompt = f"""
你是一个高效的任务执行专家，请完成以下任务：

任务：{task}

任务上下文：{context or '无'}

请按照以下格式输出执行结果：
{{
    "status": "completed|in_progress|failed",
    "task_id": "任务ID",
    "output": "任务执行结果",
    "steps": ["步骤1", "步骤2", "步骤3"],
    "errors": ["错误信息列表"],
    "suggestion": "后续建议"
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
                "status": "completed",
                "task_id": "unknown",
                "output": result,
                "steps": [],
                "errors": [],
                "suggestion": ""
            }
