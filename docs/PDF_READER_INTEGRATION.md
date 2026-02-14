# PDF Reader Tool 集成到 Agent 的示例

## 在 Planner 中添加 PDF Reader 工具

### 1. 更新 Executor 初始化

在 `agent/executor.py` 中添加 PDF Reader 工具:

```python
from tools import FileEditorTool, PythonExecutorTool, BashExecutorTool, PDFReaderTool

class Executor:
    def __init__(self, llm_config: LLMConfig = None):
        self.tools = {
            "file_editor": FileEditorTool(),
            "python_executor": PythonExecutorTool(),
            "bash_executor": BashExecutorTool(),
            "pdf_reader": PDFReaderTool(),  # 新增
        }
        # ... 其他初始化代码
```

### 2. 更新 Planner 的系统提示

在 `agent/planner.py` 的 `create_plan` 方法中更新系统提示:

```python
system_prompt = """You are a planning assistant. Given a user request, create a detailed step-by-step plan.

Available tools:
1. file_editor - For file operations
   - view: View entire file or with range {"command": "view", "path": "/path", "view_range": [start, end]}
   - create: Create new file {"command": "create", "path": "/path", "content": "..."}
   - str_replace: Replace string {"command": "str_replace", "path": "/path", "old_str": "...", "new_str": "..."}
   - insert: Insert at line {"command": "insert", "path": "/path", "insert_line": 10, "content": "..."}
   - delete: Delete file {"command": "delete", "path": "/path"}

2. python_executor - For executing Python code {"code": "python code"}

3. bash_executor - For executing bash commands {"command": "bash command"}

4. pdf_reader - For PDF processing and academic paper analysis
   - get_info: Get PDF information {"command": "get_info", "path": "/path/to/paper.pdf"}
   - extract_text: Extract text from pages {"command": "extract_text", "path": "/path", "start_page": 0, "end_page": 2}
   - extract_metadata: Extract paper metadata {"command": "extract_metadata", "path": "/path"}
   - extract_section: Extract specific section {"command": "extract_section", "path": "/path", "section_name": "Abstract"}
   - extract_full_markdown: Extract full paper as Markdown {"command": "extract_full_markdown", "path": "/path"}

Return a JSON array of steps...
"""
```

## 使用场景示例

### 场景 1: 翻译学术论文

用户请求: "请帮我翻译这篇论文 /papers/deep_learning.pdf 的摘要部分"

Agent 生成的计划:

```json
[
  {
    "id": 1,
    "description": "获取 PDF 基本信息",
    "tool": "pdf_reader",
    "tool_params": {
      "command": "get_info",
      "path": "/papers/deep_learning.pdf"
    },
    "dependencies": []
  },
  {
    "id": 2,
    "description": "提取论文摘要部分",
    "tool": "pdf_reader",
    "tool_params": {
      "command": "extract_section",
      "path": "/papers/deep_learning.pdf",
      "section_name": "Abstract"
    },
    "dependencies": [1]
  },
  {
    "id": 3,
    "description": "将摘要翻译成中文并保存",
    "tool": "file_editor",
    "tool_params": {
      "command": "create",
      "path": "/papers/deep_learning_abstract_zh.md",
      "content": "[翻译后的内容]"
    },
    "dependencies": [2]
  }
]
```

### 场景 2: 总结论文要点

用户请求: "总结 /papers/nlp_survey.pdf 这篇综述论文的主要内容"

Agent 生成的计划:

```json
[
  {
    "id": 1,
    "description": "提取论文元数据（标题、作者、摘要）",
    "tool": "pdf_reader",
    "tool_params": {
      "command": "extract_metadata",
      "path": "/papers/nlp_survey.pdf"
    },
    "dependencies": []
  },
  {
    "id": 2,
    "description": "提取完整论文内容为 Markdown",
    "tool": "pdf_reader",
    "tool_params": {
      "command": "extract_full_markdown",
      "path": "/papers/nlp_survey.pdf"
    },
    "dependencies": [1]
  },
  {
    "id": 3,
    "description": "保存提取的 Markdown 文档",
    "tool": "file_editor",
    "tool_params": {
      "command": "create",
      "path": "/papers/nlp_survey_extracted.md",
      "content": "[步骤2的输出]"
    },
    "dependencies": [2]
  }
]
```

### 场景 3: 批量处理论文

用户请求: "处理 /papers 目录下的所有 PDF，提取摘要并翻译"

Agent 生成的计划:

```json
[
  {
    "id": 1,
    "description": "列出 papers 目录下的所有 PDF 文件",
    "tool": "bash_executor",
    "tool_params": {
      "command": "find /papers -name '*.pdf' -type f"
    },
    "dependencies": []
  },
  {
    "id": 2,
    "description": "创建 Python 脚本批量处理 PDF",
    "tool": "python_executor",
    "tool_params": {
      "code": "import asyncio\nfrom tools.pdf_reader import PDFReaderTool\n\nasync def process_pdfs():\n    tool = PDFReaderTool()\n    pdf_files = [...]  # 从步骤1获取\n    for pdf in pdf_files:\n        result = await tool.execute(\n            command='extract_metadata',\n            path=pdf\n        )\n        print(f'Processed: {pdf}')\n\nasyncio.run(process_pdfs())"
    },
    "dependencies": [1]
  }
]
```

## 完整的工作流示例

```python
# 在 main.py 中使用
async def main():
    # 初始化 Agent
    agent = create_agent()

    # 用户请求
    user_request = "请帮我翻译 /papers/attention_is_all_you_need.pdf 这篇论文"

    # Agent 执行
    initial_state = {
        "user_request": user_request,
        "plan": [],
        "messages": [],
        "needs_replan": False,
        "iteration_count": 0,
        "failed_steps": []
    }

    final_state = await agent.ainvoke(initial_state)

    # 输出结果
    print("执行完成!")
    for message in final_state["messages"]:
        print(f"{message['role']}: {message['content']}")
```

## 预期输出示例

```
执行完成!

assistant: Created plan with 4 steps

assistant: Step 1 completed: 获取 PDF 信息
## PDF 信息
- **页数**: 15
- **是否加密**: False
- **标题**: Attention Is All You Need
- **作者**: Ashish Vaswani, et al.

assistant: Step 2 completed: 提取论文元数据
## 论文元数据
### 标题
Attention Is All You Need

### 作者
Ashish Vaswani, Noam Shazeer, Niki Parmar, Jakob Uszkoreit, Llion Jones, Aidan N. Gomez, Łukasz Kaiser, Illia Polosukhin

### 摘要
The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...

assistant: Step 3 completed: 提取完整论文内容
已提取 15 页内容，共 45000 字符

assistant: Step 4 completed: 保存翻译后的中文文档
已保存到: /papers/attention_is_all_you_need_zh.md

assistant: 任务完成！论文已成功翻译并保存。
```

## 与 LLM 的集成模式

### 模式 1: 直接翻译

```python
# 在 Executor 中
async def execute_step(self, step: PlanStep):
    if step.tool == "pdf_reader":
        result = await self.tools["pdf_reader"].execute(**step.tool_params)

        if result.success and "translate" in step.description.lower():
            # 自动调用 LLM 翻译
            translated = await self.llm.ainvoke(
                f"请将以下内容翻译成中文:\n\n{result.output}"
            )
            result.output = translated

        return result
```

### 模式 2: 分步处理

```python
# 步骤 1: 提取
result1 = await pdf_tool.execute(
    command="extract_section",
    path="/paper.pdf",
    section_name="Abstract"
)

# 步骤 2: 翻译
if result1.success:
    translation = await llm.ainvoke(
        f"Translate to Chinese:\n{result1.output}"
    )

# 步骤 3: 保存
await file_tool.execute(
    command="create",
    path="/paper_abstract_zh.md",
    content=translation
)
```

## 最佳实践

1. **分页处理大文档**: 避免一次性处理过大的 PDF
2. **缓存提取结果**: 避免重复提取相同内容
3. **错误恢复**: 提取失败时提供降级方案
4. **进度反馈**: 处理大文档时提供进度信息
5. **质量检查**: 翻译后进行人工审核

## 总结

PDF Reader Tool 已完全集成到 Agent 框架中，可以:

✅ 在 Planner 中自动生成 PDF 处理计划
✅ 在 Executor 中执行 PDF 提取任务
✅ 与 LLM 无缝集成进行翻译
✅ 支持复杂的多步骤工作流
✅ 提供完善的错误处理和日志

工具已准备好投入生产使用！
