from .base_agent import BaseAgent
from typing import Dict, Any, List


class TaskDecomposer(BaseAgent):
    """任务拆解 Agent"""
    
    def __init__(self, llm_client=None):
        super().__init__("TaskDecomposer", llm_client)
    
    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """将复杂任务拆解为子任务"""
        prompt = f"""
你是一个资深的项目管理专家，请将以下任务拆解为可执行的子任务：

任务：{task}

请按照以下格式输出：
{{
    "total_tasks": 子任务总数,
    "tasks": [
        {{
            "id": "任务ID",
            "title": "子任务标题",
            "description": "任务描述",
            "priority": "high|medium|low",
            "dependencies": ["依赖的任务ID列表"],
            "estimated_time": "预计时间",
            "agent_type": "适合执行此任务的Agent类型"
        }}
    ],
    "summary": "拆解总结"
}}

请确保：
1. 子任务之间的依赖关系清晰
2. 优先级合理分配
3. 每个子任务都是可执行的单元
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
                "total_tasks": 1,
                "tasks": [{
                    "id": "T1",
                    "title": task,
                    "description": task,
                    "priority": "high",
                    "dependencies": [],
                    "estimated_time": "1小时",
                    "agent_type": "通用"
                }],
                "summary": result
            }
