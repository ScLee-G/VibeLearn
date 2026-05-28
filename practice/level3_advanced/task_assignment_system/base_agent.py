from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import openai
import os


class BaseAgent(ABC):
    """Agent 基类"""
    
    def __init__(self, name: str, llm_client: Optional[Any] = None):
        self.name = name
        self.llm_client = llm_client or self._create_default_client()
    
    def _create_default_client(self):
        """创建默认的 LLM 客户端"""
        return openai.OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_BASE_URL")
        )
    
    @abstractmethod
    def execute(self, task: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """执行 Agent 任务"""
        pass
    
    def call_llm(self, prompt: str, model: str = "deepseek-chat") -> str:
        """调用 LLM"""
        response = self.llm_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()
