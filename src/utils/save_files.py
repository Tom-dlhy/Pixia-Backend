"""
Document export utilities for courses.

Handles conversion and storage of generated content to Markdown and PDF formats
with styling, logos, and generation metadata.
"""

import base64
import logging
import os
import re
import tempfile
from datetime import datetime
from io import BytesIO
from pathlib import Path
from typing import Optional

import markdown
from fastapi.responses import Response
from xhtml2pdf import pisa

from src.models.cours_models import CourseOutput

logger = logging.getLogger(__name__)

ASSETS_DIR = Path(__file__).parent.parent / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"
LOGO_SIZE = 140  # Logo width in pixels


def course_output_to_markdown(course: CourseOutput) -> str:
    """
    Convert CourseOutput to Markdown format.

    Args:
        course: CourseOutput with title and sections

    Returns:
        Formatted Markdown content
    """
    md_content = f"# {course.title}\n\n"

    for idx, part in enumerate(course.parts, 1):
        md_content += f"## {idx}. {part.title}\n\n"
        md_content += f"{part.content}\n\n"

        if part.img_base64:
            md_content += f"### Diagram - {part.title}\n\n"
            if part.schema_description:
                md_content += f"*{part.schema_description}*\n\n"
            md_content += f"![Diagram {idx}](data:image/png;base64,{part.img_base64})\n\n"

        if idx < len(course.parts):
            md_content += "---\n\n"

    return md_content


def save_markdown_to_file(markdown_content: str, output_path: Optional[str] = None) -> str:
    """
    Save Markdown content to file.

    Args:
        markdown_content: Content to save
        output_path: Output file path (auto-generated if not provided)

    Returns:
        Path to created file
    """
    if output_path is None:
        fd, output_path = tempfile.mkstemp(suffix=".md", prefix="course_")
        os.close(fd)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(markdown_content)

    logger.info(f"[SAVE_FILES] ✅ Markdown saved: {output_path}")
    return output_path


def _build_html_template(markdown_content: str, add_logo: bool = True) -> str:
    """
    Build complete HTML template with CSS styling from Markdown content.

    Args:
        markdown_content: Markdown to convert
        add_logo: Include Pixia logo if True

    Returns:
        Complete HTML document string
    """
    generation_date = datetime.now().strftime("%d/%m/%Y à %H:%M")
    html_content = markdown.markdown(
        markdown_content,
        extensions=['extra', 'tables', 'fenced_code', 'nl2br']
    )

    generation_info = f"""
    <div class="generation-info" style="text-align: center; margin-bottom: 30px;">
        <p style="color: #7f8c8d; font-size: 9pt; font-style: italic; margin: 0;">
            Generated on {generation_date}
        </p>
    </div>
    """

    logo_base64 = ""
    page_template = ""

    if add_logo and LOGO_PATH.exists():
        with open(LOGO_PATH, "rb") as img_file:
            logo_base64 = base64.b64encode(img_file.read()).decode('utf-8')

        page_template = f"""
        <div id="header_content" style="position: absolute; top: 0; right: 0; width: 100%; text-align: right; padding: 10px 20px;">
            <img src="data:image/png;base64,{logo_base64}" alt="Pixia" style="width: {LOGO_SIZE}px; height: auto; opacity: 0.7;" />
        </div>
        """

    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            @page {{
                size: A4;
                margin: 2.5cm 2cm 2cm 2cm;

                @frame header {{
                    -pdf-frame-content: header_content;
                    top: 0.5cm;
                    margin-left: 2cm;
                    margin-right: 2cm;
                    height: 2cm;
                }}
            }}

            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                font-size: 11pt;
            }}

            h1 {{
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                font-size: 24pt;
                font-weight: 700;
                margin-top: 20px;
                page-break-after: avoid;
            }}

            h2 {{
                color: #34495e;
                margin-top: 30px;
                font-size: 18pt;
                font-weight: 600;
                page-break-after: avoid;
            }}

            h3 {{
                color: #7f8c8d;
                font-size: 14pt;
                font-weight: 600;
                page-break-after: avoid;
            }}

            code {{
                background-color: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: 'Courier New', monospace;
                font-size: 9pt;
            }}

            pre {{
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 15px;
                overflow-x: auto;
                page-break-inside: avoid;
            }}

            pre code {{
                background-color: transparent;
                padding: 0;
            }}

            img {{
                max-width: 100%;
                height: auto;
                display: block;
                margin: 20px auto;
                page-break-inside: avoid;
            }}

            hr {{
                border: none;
                border-top: 2px solid #ecf0f1;
                margin: 30px 0;
            }}

            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 20px 0;
                page-break-inside: avoid;
            }}

            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}

            th {{
                background-color: #3498db;
                color: white;
                font-weight: 600;
            }}

            blockquote {{
                border-left: 4px solid #3498db;
                padding-left: 20px;
                margin-left: 0;
                color: #555;
                font-style: italic;
            }}

            p {{
                margin: 10px 0;
                text-align: justify;
            }}

            ul, ol {{
                margin: 10px 0;
                padding-left: 30px;
            }}

            li {{
                margin: 5px 0;
            }}
        </style>
    </head>
    <body>
        {page_template}
        {generation_info}
        {html_content}
    </body>
    </html>
    """

    return full_html


def markdown_to_pdf(
    markdown_content: str,
    output_pdf_path: Optional[str] = None,
    add_logo: bool = True
) -> str:
    """
    Convert Markdown to PDF with optional Pixia logo header.

    Args:
        markdown_content: Content to convert
        output_pdf_path: Output file path (auto-generated if not provided)
        add_logo: Include Pixia logo if True

    Returns:
        Path to created PDF file
    """
    if output_pdf_path is None:
        fd, output_pdf_path = tempfile.mkstemp(suffix=".pdf", prefix="course_")
        os.close(fd)

    full_html = _build_html_template(markdown_content, add_logo)

    with open(output_pdf_path, "wb") as pdf_file:
        pisa.CreatePDF(src=full_html, dest=pdf_file, encoding='utf-8')

    logger.info(f"[SAVE_FILES] ✅ PDF generated: {output_pdf_path}")
    return output_pdf_path


def save_course_as_pdf(
    course: CourseOutput,
    output_pdf_path: Optional[str] = None,
    keep_markdown: bool = False
) -> tuple[str, Optional[str]]:
    """
    Convert CourseOutput to complete PDF with Pixia logo.

    Args:
        course: CourseOutput to convert
        output_pdf_path: Output file path (auto-generated if not provided)
        keep_markdown: Keep temporary Markdown file if True

    Returns:
        Tuple with (pdf_path, markdown_path_or_none)
    """
    logger.info(f"[SAVE_FILES] 📄 Generating PDF for course: {course.title}")

    markdown_content = course_output_to_markdown(course)
    md_path = save_markdown_to_file(markdown_content)
    pdf_path = markdown_to_pdf(markdown_content, output_pdf_path)

    if not keep_markdown:
        try:
            os.unlink(md_path)
            md_path = None
        except Exception as e:
            logger.warning(f"[SAVE_FILES] ⚠️ Failed to delete temporary Markdown: {e}")

    return pdf_path, md_path


def sanitize_filename(filename: str) -> str:
    """
    Clean filename for compatibility with all systems.

    Removes invalid characters, limits length, and trims whitespace.

    Args:
        filename: Filename to clean

    Returns:
        Sanitized filename
    """
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = filename[:200]
    filename = filename.strip()
    return filename


def generate_course_pdf_response(course: CourseOutput) -> Response:
    """
    Generate in-memory PDF from CourseOutput and return as FastAPI Response.

    PDF is created in memory with no disk writes.

    Args:
        course: CourseOutput to convert

    Returns:
        FastAPI Response with PDF content and download headers
    """
    logger.info(f"[SAVE_FILES] 📄 Generating PDF for frontend: {course.title}")

    markdown_content = course_output_to_markdown(course)
    full_html = _build_html_template(markdown_content, add_logo=True)

    pdf_buffer = BytesIO()
    pisa.CreatePDF(src=full_html, dest=pdf_buffer, encoding='utf-8')

    pdf_bytes = pdf_buffer.getvalue()
    filename = sanitize_filename(course.title) + ".pdf"

    logger.info(f"[SAVE_FILES] ✅ PDF generated in memory: {filename} ({len(pdf_bytes)} bytes)")

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )
