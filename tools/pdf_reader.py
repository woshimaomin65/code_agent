"""PDF Reader tool for academic paper processing."""
import logging
import re
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from .base import BaseTool, ToolResult

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


class PDFReaderTool(BaseTool):
    """Tool for reading and processing academic PDF papers."""

    def __init__(self):
        self.name = "pdf_reader"
        self.description = """PDF reader tool for academic paper processing.
Commands:
- extract_text: Extract text from PDF (with optional page range)
- extract_metadata: Extract paper metadata (title, author, abstract)
- extract_section: Extract specific section by name
- get_info: Get PDF information (page count, encryption status)
- extract_full_markdown: Extract full paper as Markdown format
"""
        self.parameters = {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "enum": ["extract_text", "extract_metadata", "extract_section",
                            "get_info", "extract_full_markdown"],
                    "description": "Command to execute"
                },
                "path": {
                    "type": "string",
                    "description": "Path to PDF file"
                },
                "start_page": {
                    "type": "integer",
                    "description": "Start page number (0-indexed, optional)"
                },
                "end_page": {
                    "type": "integer",
                    "description": "End page number (0-indexed, optional)"
                },
                "section_name": {
                    "type": "string",
                    "description": "Section name to extract (e.g., 'Abstract', 'Introduction')"
                },
                "preserve_layout": {
                    "type": "boolean",
                    "description": "Whether to preserve layout (default: True)"
                }
            },
            "required": ["command", "path"]
        }
        self.logger = logging.getLogger("code_agent.pdf_reader")

    async def execute(self, **kwargs) -> ToolResult:
        """Execute PDF reader command."""
        command = kwargs.get("command")
        path = kwargs.get("path")

        # Validate PDF library availability
        if not PYMUPDF_AVAILABLE and not PDFPLUMBER_AVAILABLE:
            return ToolResult(
                success=False,
                error="Neither PyMuPDF nor pdfplumber is installed. Please install: pip install PyMuPDF pdfplumber"
            )

        # Validate path
        pdf_path = Path(path)
        if not pdf_path.exists():
            return ToolResult(
                success=False,
                error=f"PDF file not found: {path}"
            )

        if not pdf_path.suffix.lower() == '.pdf':
            return ToolResult(
                success=False,
                error=f"File is not a PDF: {path}"
            )

        try:
            if command == "get_info":
                return await self._get_info(pdf_path)
            elif command == "extract_text":
                start_page = kwargs.get("start_page", 0)
                end_page = kwargs.get("end_page")
                preserve_layout = kwargs.get("preserve_layout", True)
                return await self._extract_text(pdf_path, start_page, end_page, preserve_layout)
            elif command == "extract_metadata":
                return await self._extract_metadata(pdf_path)
            elif command == "extract_section":
                section_name = kwargs.get("section_name")
                if not section_name:
                    return ToolResult(success=False, error="section_name is required")
                return await self._extract_section(pdf_path, section_name)
            elif command == "extract_full_markdown":
                return await self._extract_full_markdown(pdf_path)
            else:
                return ToolResult(
                    success=False,
                    error=f"Unknown command: {command}"
                )

        except Exception as e:
            self.logger.error(f"PDF processing error: {str(e)}", exc_info=True)
            return ToolResult(
                success=False,
                error=f"PDF processing failed: {str(e)}"
            )

    async def _get_info(self, pdf_path: Path) -> ToolResult:
        """Get PDF information."""
        try:
            if PYMUPDF_AVAILABLE:
                doc = fitz.open(pdf_path)
                info = {
                    "页数": doc.page_count,
                    "是否加密": doc.is_encrypted,
                    "是否可复制": not doc.is_encrypted,
                    "文件大小": f"{pdf_path.stat().st_size / 1024:.2f} KB"
                }
                metadata = doc.metadata
                if metadata:
                    if metadata.get("title"):
                        info["标题"] = metadata["title"]
                    if metadata.get("author"):
                        info["作者"] = metadata["author"]
                doc.close()

                output = "## PDF 信息\n\n"
                for key, value in info.items():
                    output += f"- **{key}**: {value}\n"

                return ToolResult(success=True, output=output)
            else:
                return ToolResult(success=False, error="PyMuPDF not available")

        except Exception as e:
            return ToolResult(success=False, error=f"Failed to get PDF info: {str(e)}")

    async def _extract_text(self, pdf_path: Path, start_page: int = 0,
                           end_page: Optional[int] = None,
                           preserve_layout: bool = True) -> ToolResult:
        """Extract text from PDF pages."""
        try:
            if PYMUPDF_AVAILABLE:
                doc = fitz.open(pdf_path)

                if doc.is_encrypted:
                    doc.close()
                    return ToolResult(success=False, error="PDF is encrypted")

                total_pages = doc.page_count
                if end_page is None:
                    end_page = total_pages - 1

                # Validate page range
                if start_page < 0 or start_page >= total_pages:
                    doc.close()
                    return ToolResult(success=False, error=f"Invalid start_page: {start_page}")
                if end_page < start_page or end_page >= total_pages:
                    doc.close()
                    return ToolResult(success=False, error=f"Invalid end_page: {end_page}")

                extracted_text = []
                for page_num in range(start_page, end_page + 1):
                    page = doc[page_num]
                    if preserve_layout:
                        text = page.get_text("text")
                    else:
                        text = page.get_text("text")
                    extracted_text.append(f"### 第 {page_num + 1} 页\n\n{text}\n")

                doc.close()

                output = f"## 提取文本 (第 {start_page + 1}-{end_page + 1} 页)\n\n"
                output += "\n".join(extracted_text)

                return ToolResult(success=True, output=output)
            else:
                return ToolResult(success=False, error="PyMuPDF not available")

        except Exception as e:
            return ToolResult(success=False, error=f"Text extraction failed: {str(e)}")

    async def _extract_metadata(self, pdf_path: Path) -> ToolResult:
        """Extract paper metadata (title, author, abstract)."""
        try:
            if not PYMUPDF_AVAILABLE:
                return ToolResult(success=False, error="PyMuPDF not available")

            doc = fitz.open(pdf_path)

            if doc.is_encrypted:
                doc.close()
                return ToolResult(success=False, error="PDF is encrypted")

            # Extract first page text for metadata detection
            first_page = doc[0]
            text = first_page.get_text("text")

            # Try to extract title (usually the largest text on first page)
            title = self._extract_title(text, doc.metadata.get("title"))

            # Try to extract authors
            authors = self._extract_authors(text)

            # Try to extract abstract
            abstract = self._extract_abstract(text)

            doc.close()

            # Format as Markdown
            output = "## 论文元数据\n\n"
            if title:
                output += f"### 标题\n{title}\n\n"
            if authors:
                output += f"### 作者\n{authors}\n\n"
            if abstract:
                output += f"### 摘要\n{abstract}\n\n"

            if not title and not authors and not abstract:
                output += "未能自动识别元数据，请手动检查PDF前几页。\n"

            return ToolResult(success=True, output=output)

        except Exception as e:
            return ToolResult(success=False, error=f"Metadata extraction failed: {str(e)}")

    def _extract_title(self, text: str, metadata_title: Optional[str]) -> Optional[str]:
        """Extract paper title from text."""
        # First try metadata
        if metadata_title and len(metadata_title) > 5:
            return metadata_title

        # Try to find title in first few lines (usually largest font)
        lines = text.split('\n')
        for line in lines[:10]:
            line = line.strip()
            # Title is usually 10-200 characters, not all caps
            if 10 < len(line) < 200 and not line.isupper():
                # Check if it looks like a title (not a URL, email, etc.)
                if not re.search(r'@|http|www', line.lower()):
                    return line

        return None

    def _extract_authors(self, text: str) -> Optional[str]:
        """Extract authors from text."""
        # Look for common author patterns
        lines = text.split('\n')
        author_lines = []

        for line in lines[:30]:
            line = line.strip()
            # Authors often have specific patterns
            if re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+', line):
                # Check if line contains email or affiliation markers
                if '@' in line or 'University' in line or 'Institute' in line:
                    continue
                # Check if it's a reasonable length for author names
                if 5 < len(line) < 100:
                    author_lines.append(line)
                    if len(author_lines) >= 3:  # Limit to first few author lines
                        break

        return ', '.join(author_lines) if author_lines else None

    def _extract_abstract(self, text: str) -> Optional[str]:
        """Extract abstract from text."""
        # Look for abstract section
        abstract_pattern = r'(?:Abstract|ABSTRACT)\s*[:\-]?\s*(.*?)(?=\n\n|\n[A-Z][a-z]+:|\nIntroduction|\nINTRODUCTION|\n1\.|\Z)'
        match = re.search(abstract_pattern, text, re.DOTALL | re.IGNORECASE)

        if match:
            abstract = match.group(1).strip()
            # Clean up the abstract
            abstract = re.sub(r'\s+', ' ', abstract)
            # Limit length
            if len(abstract) > 50:
                return abstract[:1000] + "..." if len(abstract) > 1000 else abstract

        return None

    async def _extract_section(self, pdf_path: Path, section_name: str) -> ToolResult:
        """Extract specific section from PDF."""
        try:
            if not PYMUPDF_AVAILABLE:
                return ToolResult(success=False, error="PyMuPDF not available")

            doc = fitz.open(pdf_path)

            if doc.is_encrypted:
                doc.close()
                return ToolResult(success=False, error="PDF is encrypted")

            # Extract all text
            full_text = ""
            for page in doc:
                full_text += page.get_text("text") + "\n"

            doc.close()

            # Find section
            section_pattern = rf'(?:^|\n)({re.escape(section_name)})\s*[:\-]?\s*(.*?)(?=\n\n[A-Z]|\n\d+\.|\Z)'
            match = re.search(section_pattern, full_text, re.DOTALL | re.IGNORECASE)

            if match:
                section_content = match.group(2).strip()
                output = f"## {section_name}\n\n{section_content}"
                return ToolResult(success=True, output=output)
            else:
                return ToolResult(
                    success=False,
                    error=f"Section '{section_name}' not found in PDF"
                )

        except Exception as e:
            return ToolResult(success=False, error=f"Section extraction failed: {str(e)}")

    async def _extract_full_markdown(self, pdf_path: Path) -> ToolResult:
        """Extract full paper as Markdown format."""
        try:
            if not PYMUPDF_AVAILABLE:
                return ToolResult(success=False, error="PyMuPDF not available")

            doc = fitz.open(pdf_path)

            if doc.is_encrypted:
                doc.close()
                return ToolResult(success=False, error="PDF is encrypted")

            # Extract metadata first
            first_page_text = doc[0].get_text("text")
            title = self._extract_title(first_page_text, doc.metadata.get("title"))
            authors = self._extract_authors(first_page_text)
            abstract = self._extract_abstract(first_page_text)

            # Build Markdown document
            markdown = "# 论文文档\n\n"

            if title:
                markdown += f"## 标题\n{title}\n\n"
            if authors:
                markdown += f"## 作者\n{authors}\n\n"
            if abstract:
                markdown += f"## 摘要\n{abstract}\n\n"

            markdown += "---\n\n## 正文内容\n\n"

            # Extract text from all pages
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text = page.get_text("text")

                # Clean up text
                text = self._clean_text(text)

                if text.strip():
                    markdown += f"### 第 {page_num + 1} 页\n\n{text}\n\n"

            doc.close()

            return ToolResult(success=True, output=markdown)

        except Exception as e:
            return ToolResult(success=False, error=f"Full markdown extraction failed: {str(e)}")

    def _clean_text(self, text: str) -> str:
        """Clean extracted text."""
        # Remove excessive whitespace
        text = re.sub(r'\n\s*\n\s*\n+', '\n\n', text)
        # Remove page numbers (simple heuristic)
        text = re.sub(r'^\s*\d+\s*$', '', text, flags=re.MULTILINE)
        return text.strip()

