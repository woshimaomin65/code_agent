# PDF Reader Tool 使用示例

## 基本用法

```python
from tools.pdf_reader import PDFReaderTool
import asyncio

async def main():
    tool = PDFReaderTool()

    # 1. 获取 PDF 信息
    result = await tool.execute(
        command="get_info",
        path="/path/to/paper.pdf"
    )
    print(result.output)

    # 2. 提取元数据（标题、作者、摘要）
    result = await tool.execute(
        command="extract_metadata",
        path="/path/to/paper.pdf"
    )
    print(result.output)

    # 3. 提取指定页面文本
    result = await tool.execute(
        command="extract_text",
        path="/path/to/paper.pdf",
        start_page=0,
        end_page=2  # 提取前3页
    )
    print(result.output)

    # 4. 提取特定章节
    result = await tool.execute(
        command="extract_section",
        path="/path/to/paper.pdf",
        section_name="Introduction"
    )
    print(result.output)

    # 5. 提取完整 Markdown 文档
    result = await tool.execute(
        command="extract_full_markdown",
        path="/path/to/paper.pdf"
    )

    # 保存为 Markdown 文件
    with open("paper_zh.md", "w", encoding="utf-8") as f:
        f.write(result.output)

asyncio.run(main())
```

## 与 LLM 结合进行翻译

```python
# 提取文本后，可以发送给 LLM 进行翻译
result = await tool.execute(
    command="extract_text",
    path="/path/to/paper.pdf",
    start_page=0,
    end_page=0
)

if result.success:
    # 将提取的文本发送给 LLM 进行翻译
    translated = await llm.translate(
        text=result.output,
        target_language="Chinese"
    )
    print(translated)
```

## 支持的命令

- `get_info`: 获取 PDF 基本信息（页数、加密状态等）
- `extract_text`: 提取指定页面范围的文本
- `extract_metadata`: 自动识别标题、作者、摘要
- `extract_section`: 提取特定章节（如 Abstract, Introduction）
- `extract_full_markdown`: 提取完整文档并格式化为 Markdown

## 依赖安装

```bash
pip install PyMuPDF pdfplumber
```

## 注意事项

1. 加密的 PDF 需要先解密
2. 扫描版 PDF 需要 OCR 处理（当前版本不支持）
3. 复杂的多栏布局可能需要手动调整
4. 数学公式的提取依赖于 PDF 中的文本编码
