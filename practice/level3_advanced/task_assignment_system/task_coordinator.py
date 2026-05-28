from typing import Dict, Any, List
from .task_decomposer import TaskDecomposer
from .task_executor import TaskExecutor
from .task_monitor import TaskMonitor


class TaskCoordinator:
    """多 Agent 任务协调器"""
    
    def __init__(self, llm_client=None):
        self.decomposer = TaskDecomposer(llm_client)
        self.executor = TaskExecutor(llm_client)
        self.monitor = TaskMonitor(llm_client)
    
    def run_task(self, task: str) -> Dict[str, Any]:
        """执行完整的任务流程"""
        print("🚀 开始任务执行流程...")
        
        # 步骤1: 拆解任务
        print("🔪 TaskDecomposer 正在拆解任务...")
        decomposition = self.decomposer.execute(task)
        tasks = decomposition.get('tasks', [])
        
        # 步骤2: 按依赖顺序执行任务
        print("\n⚡ TaskExecutor 正在执行任务...")
        task_results = []
        completed_tasks = set()
        
        # 简单的拓扑排序执行
        while len(completed_tasks) < len(tasks):
            for subtask in tasks:
                task_id = subtask['id']
                if task_id in completed_tasks:
                    continue
                
                # 检查依赖是否都已完成
                dependencies = subtask.get('dependencies', [])
                if all(dep in completed_tasks for dep in dependencies):
                    print(f"  执行任务: {subtask['title']}")
                    result = self.executor.execute(subtask['description'], subtask)
                    result['task_id'] = task_id
                    result['title'] = subtask['title']
                    task_results.append(result)
                    completed_tasks.add(task_id)
        
        # 步骤3: 监控和总结
        print("\n📊 TaskMonitor 正在生成监控报告...")
        monitor_result = self.monitor.execute(task, {'tasks': task_results})
        
        return {
            "decomposition": decomposition,
            "execution_results": task_results,
            "monitor_report": monitor_result
        }
    
    def run_task_parallel(self, task: str) -> Dict[str, Any]:
        """并行执行任务（模拟）"""
        import threading
        import queue
        
        print("🚀 开始并行任务执行流程...")
        
        # 步骤1: 拆解任务
        print("🔪 TaskDecomposer 正在拆解任务...")
        decomposition = self.decomposer.execute(task)
        tasks = decomposition.get('tasks', [])
        
        # 步骤2: 并行执行独立任务
        print("\n⚡ TaskExecutor 正在并行执行任务...")
        task_results = []
        result_queue = queue.Queue()
        
        def execute_worker(subtask, queue):
            result = self.executor.execute(subtask['description'], subtask)
            result['task_id'] = subtask['id']
            result['title'] = subtask['title']
            queue.put(result)
        
        # 第一阶段：执行无依赖的任务
        threads = []
        for subtask in tasks:
            dependencies = subtask.get('dependencies', [])
            if not dependencies:
                thread = threading.Thread(
                    target=execute_worker,
                    args=(subtask, result_queue)
                )
                threads.append(thread)
                thread.start()
        
        for thread in threads:
            thread.join()
        
        while not result_queue.empty():
            task_results.append(result_queue.get())
        
        # 步骤3: 监控和总结
        print("\n📊 TaskMonitor 正在生成监控报告...")
        monitor_result = self.monitor.execute(task, {'tasks': task_results})
        
        return {
            "decomposition": decomposition,
            "execution_results": task_results,
            "monitor_report": monitor_result
        }
