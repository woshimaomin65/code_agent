# PDF Reader Tool - 学术论文处理工具

## 概述

`PDFReaderTool` 是一个专为学术论文处理设计的工具类，能够提取、解析和格式化 PDF 文档内容，输出高质量的中文 Markdown 文档。

## 特性

### ✅ 已实现功能

1. **文本提取**
   - 按页或按范围提取文本
   - 保持段落完整性
   - 支持布局保留选项

2. **元数据识别**
   - 自动识别论文标题
   - 提取作者信息
   - 识别摘要（Abstract）部分

3. **章节提取**
   - 按章节名称提取内容
   - 支持常见学术论文结构（Abstract, Introduction, Conclusion 等）

4. **Markdown 格式化**
   - 自动转换为 Markdown 格式
   - 标题层级处理
   - 段落和列表格式化

5. **健壮性**
   - PDF 加密检测
   - 文件路径验证
   - 详细的错误日志
   - 异常处理机制

## 技术实现

### 核心库

- **PyMuPDF (fitz)**: 主要 PDF 处理库，支持复杂布局和公式提取
- **pdfplumber**: 备选库，提供额外的表格提取能力

### 架构设计

```
PDFReaderTool (继承 BaseTool)
├── execute()              # 主执行方法
├── _get_info()           # 获取 PDF 信息
├── _extract_text()       # 文本提取
├── _extract_metadata()   # 元数据提取
├── _extract_section()    # 章节提取
├── _extract_full_markdown() # 完整文档提取
└── 辅助方法
    ├── _extract_title()
    ├── _extract_authors()
    ├── _extract_abstract()
    └── _clean_text()
```

## 使用方法

### 1. 安装依赖

```bash
pip install PyMuPDF pdfplumber
```

### 2. 基本使用

```python
from tools.pdf_reader import PDFReaderTool
import asyncio

async def main():
    tool = PDFReaderTool()

    # 获取 PDF 信息
    result = await tool.execute(
        command="get_info",
        path="/path/to/paper.pdf"
    )
    print(result.output)

asyncio.run(main())
```

### 3. 支持的命令

#### `get_info` - 获取 PDF 信息

```python
result = await tool.execute(
    command="get_info",
    path="/path/to/paper.pdf"
)
```

输出示例:
```markdown
## PDF 信息

- **页数**: 12
- **是否加密**: False
- **是否可复制**: True
- **文件大小**: 1234.56 KB
- **标题**: Deep Learning for Natural Language Processing
- **作者**: John Doe, Jane Smith
```

#### `extract_text` - 提取文本

```python
result = await tool.execute(
    command="extract_text",
    path="/path/to/paper.pdf",
    start_page=0,      # 起始页（0-indexed）
    end_page=2,        # 结束页
    preserve_layout=True  # 保留布局
)
```

#### `extract_metadata` - 提取元数据

```python
result = await tool.execute(
    command="extract_metadata",
    path="/path/to/paper.pdf"
)
```

输出示例:
```markdown
## 论文元数据

### 标题
Deep Learning for Natural Language Processing

### 作者
John Doe, Jane Smith, Alice Johnson

### 摘要
This paper presents a novel approach to natural language processing using deep learning techniques...
```

#### `extract_section` - 提取特定章节

```python
result = await tool.execute(
    command="extract_section",
    path="/path/to/paper.pdf",
    section_name="Introduction"  # 或 "Abstract", "Conclusion" 等
)
```

#### `extract_full_markdown` - 提取完整文档

```python
result = await tool.execute(
    command="extract_full_markdown",
    path="/path/to/paper.pdf"
)

# 保存为 Markdown 文件
with open("paper_zh.md", "w", encoding="utf-8") as f:
    f.write(result.output)
```

## 与 AI Agent 集成

### 在 Planner 中使用

```python
# 在 agent/planner.py 的工具列表中添加
Available tools:
4. pdf_reader - For PDF processing
   - get_info: Get PDF information {"command": "get_info", "path": "/path"}
   - extract_metadata: Extract paper metadata {"command": "extract_metadata", "path": "/path"}
   - extract_full_markdown: Extract full paper as Markdown {"command": "extract_full_markdown", "path": "/path"}
```

### 与 LLM 结合翻译

```python
# 1. 提取英文内容
result = await pdf_tool.execute(
    command="extract_text",
    path="/path/to/paper.pdf",
    start_page=0,
    end_page=0
)

# 2. 发送给 LLM 翻译
if result.success:
    translation_prompt = f"""
    请将以下学术论文内容翻译成中文，保持专业术语的准确性：

    {result.output}
    """

    translated = await llm.ainvoke(translation_prompt)
    print(translated)
```

### 完整工作流示例

```python
async def process_academic_paper(pdf_path: str):
    """处理学术论文的完整工作流"""
    tool = PDFReaderTool()

    # Step 1: 获取 PDF 信息
    info = await tool.execute(command="get_info", path=pdf_path)
    print(f"论文信息:\n{info.output}")

    # Step 2: 提取元数据
    metadata = await tool.execute(command="extract_metadata", path=pdf_path)
    print(f"\n元数据:\n{metadata.output}")

    # Step 3: 提取完整内容
    full_content = await tool.execute(
        command="extract_full_markdown",
        path=pdf_path
    )

    if full_content.success:
        # Step 4: 保存原始 Markdown
        with open("paper_original.md", "w", encoding="utf-8") as f:
            f.write(full_content.output)

        # Step 5: 可选 - 发送给 LLM 进行翻译和总结
        # translation = await llm.translate(full_content.output)

        print("\n✓ 论文处理完成")
        return full_content.output
    else:
        print(f"\n✗ 处理失败: {full_content.error}")
        return None
```

## 错误处理

工具提供了完善的错误处理机制：

```python
result = await tool.execute(command="get_info", path="/path/to/paper.pdf")

if result.success:
    print(result.output)
else:
    # 处理错误
    if "not found" in result.error:
        print("PDF 文件不存在")
    elif "encrypted" in result.error:
        print("PDF 已加密，需要解密")
    else:
        print(f"其他错误: {result.error}")
```

## 限制与注意事项

### 当前限制

1. **扫描版 PDF**: 不支持 OCR，需要文本可提取的 PDF
2. **加密 PDF**: 需要先解密才能处理
3. **复杂布局**: 多栏布局可能需要手动调整
4. **数学公式**: 依赖 PDF 中的文本编码，复杂公式可能无法完美提取
5. **表格**: 基本支持，复杂表格可能需要额外处理

### 最佳实践

1. **预处理**: 确保 PDF 是文本可提取的（非扫描版）
2. **分页处理**: 对于大型文档，建议分页提取以提高性能
3. **验证输出**: 提取后检查关键内容的完整性
4. **备份原文**: 保留原始 PDF 以便对照
5. **人工审核**: 自动提取的元数据建议人工审核

## 扩展功能（未来计划）

- [ ] OCR 支持（扫描版 PDF）
- [ ] 表格提取和格式化
- [ ] 图片提取和描述
- [ ] LaTeX 公式识别和转换
- [ ] 参考文献解析
- [ ] 多语言支持
- [ ] PDF 批量处理
- [ ] 自定义模板输出

## 测试

运行测试套件：

```bash
python test/test_pdf_reader.py
```

测试覆盖：
- ✅ 工具初始化
- ✅ PDF 信息获取
- ✅ 元数据提取
- ✅ 文本提取
- ✅ 章节提取
- ✅ Markdown 格式化
- ✅ 错误处理

## 贡献

欢迎提交 Issue 和 Pull Request 来改进这个工具！

## 许可

与项目主体保持一致。
