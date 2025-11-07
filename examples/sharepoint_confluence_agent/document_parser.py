"""Document parsing utilities for various file formats."""

import os
import base64
from typing import Optional, Dict, Any
from io import BytesIO
from langchain_core.tools import tool


def _safe_import(module_name: str, package: Optional[str] = None):
    """Safely import a module with error handling."""
    try:
        if package:
            return __import__(module_name, fromlist=[package])
        return __import__(module_name)
    except ImportError as e:
        raise ImportError(
            f"Required package not installed: {module_name}. "
            f"Install it with: pip install {module_name}"
        ) from e


def _parse_pdf(file_path: str) -> Dict[str, Any]:
    """Parse a PDF file and extract text and images."""
    try:
        import PyPDF2
        from PIL import Image
    except ImportError:
        return {
            "error": "PDF parsing requires PyPDF2 and Pillow. Install with: pip install PyPDF2 Pillow"
        }

    result = {
        "type": "pdf",
        "pages": [],
        "total_pages": 0,
        "text": "",
        "images": [],
    }

    try:
        with open(file_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            result["total_pages"] = len(pdf_reader.pages)

            for page_num, page in enumerate(pdf_reader.pages):
                page_text = page.extract_text()
                result["pages"].append({
                    "page_number": page_num + 1,
                    "text": page_text,
                })
                result["text"] += f"\n--- Page {page_num + 1} ---\n{page_text}"

                # Extract images if available
                if "/XObject" in page["/Resources"]:
                    x_objects = page["/Resources"]["/XObject"].get_object()
                    for obj_name in x_objects:
                        obj = x_objects[obj_name]
                        if obj["/Subtype"] == "/Image":
                            result["images"].append({
                                "page": page_num + 1,
                                "name": obj_name,
                            })

        return result

    except Exception as e:
        return {"error": f"Error parsing PDF: {str(e)}"}


def _parse_docx(file_path: str) -> Dict[str, Any]:
    """Parse a Word document (DOCX) and extract text and images."""
    try:
        from docx import Document
        from docx.oxml.table import CT_Tbl
        from docx.oxml.text.paragraph import CT_P
        from docx.table import _Cell, Table
        from docx.text.paragraph import Paragraph
    except ImportError:
        return {
            "error": "DOCX parsing requires python-docx. Install with: pip install python-docx"
        }

    result = {
        "type": "docx",
        "text": "",
        "paragraphs": [],
        "tables": [],
        "images": [],
    }

    try:
        doc = Document(file_path)

        # Extract paragraphs
        for para in doc.paragraphs:
            if para.text.strip():
                result["paragraphs"].append(para.text)
                result["text"] += para.text + "\n"

        # Extract tables
        for table_num, table in enumerate(doc.tables):
            table_data = []
            for row in table.rows:
                row_data = [cell.text for cell in row.cells]
                table_data.append(row_data)
            result["tables"].append({
                "table_number": table_num + 1,
                "data": table_data,
            })

        # Extract images
        for rel in doc.part.rels.values():
            if "image" in rel.target_ref:
                result["images"].append({
                    "name": rel.target_ref,
                    "type": rel.target_ref.split(".")[-1],
                })

        return result

    except Exception as e:
        return {"error": f"Error parsing DOCX: {str(e)}"}


def _parse_pptx(file_path: str) -> Dict[str, Any]:
    """Parse a PowerPoint presentation (PPTX) and extract text and images."""
    try:
        from pptx import Presentation
    except ImportError:
        return {
            "error": "PPTX parsing requires python-pptx. Install with: pip install python-pptx"
        }

    result = {
        "type": "pptx",
        "slides": [],
        "total_slides": 0,
        "text": "",
        "images": [],
    }

    try:
        prs = Presentation(file_path)
        result["total_slides"] = len(prs.slides)

        for slide_num, slide in enumerate(prs.slides):
            slide_text = []
            slide_images = []

            # Extract text from shapes
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_text.append(shape.text)

                # Check for images
                if shape.shape_type == 13:  # Picture shape type
                    slide_images.append({
                        "name": shape.name,
                        "slide": slide_num + 1,
                    })

            slide_content = "\n".join(slide_text)
            result["slides"].append({
                "slide_number": slide_num + 1,
                "text": slide_content,
                "images": slide_images,
            })
            result["text"] += f"\n--- Slide {slide_num + 1} ---\n{slide_content}"
            result["images"].extend(slide_images)

        return result

    except Exception as e:
        return {"error": f"Error parsing PPTX: {str(e)}"}


def _parse_xlsx(file_path: str) -> Dict[str, Any]:
    """Parse an Excel spreadsheet (XLSX) and extract data."""
    try:
        import openpyxl
    except ImportError:
        return {
            "error": "XLSX parsing requires openpyxl. Install with: pip install openpyxl"
        }

    result = {
        "type": "xlsx",
        "sheets": [],
        "total_sheets": 0,
    }

    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)
        result["total_sheets"] = len(wb.sheetnames)

        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            sheet_data = []

            for row in sheet.iter_rows(values_only=True):
                sheet_data.append(list(row))

            result["sheets"].append({
                "name": sheet_name,
                "data": sheet_data,
                "rows": len(sheet_data),
                "columns": len(sheet_data[0]) if sheet_data else 0,
            })

        return result

    except Exception as e:
        return {"error": f"Error parsing XLSX: {str(e)}"}


def _parse_image(file_path: str) -> Dict[str, Any]:
    """Parse an image file and extract metadata."""
    try:
        from PIL import Image
    except ImportError:
        return {
            "error": "Image parsing requires Pillow. Install with: pip install Pillow"
        }

    result = {
        "type": "image",
        "format": None,
        "size": None,
        "mode": None,
        "base64": None,
    }

    try:
        with Image.open(file_path) as img:
            result["format"] = img.format
            result["size"] = img.size  # (width, height)
            result["mode"] = img.mode

            # Convert to base64 for multimodal LLM
            buffer = BytesIO()
            img.save(buffer, format=img.format)
            img_bytes = buffer.getvalue()
            result["base64"] = base64.b64encode(img_bytes).decode("utf-8")

        return result

    except Exception as e:
        return {"error": f"Error parsing image: {str(e)}"}


def _parse_text(file_path: str) -> Dict[str, Any]:
    """Parse a plain text file."""
    result = {
        "type": "text",
        "text": "",
        "encoding": "utf-8",
    }

    try:
        # Try different encodings
        encodings = ["utf-8", "latin-1", "cp1252"]
        for encoding in encodings:
            try:
                with open(file_path, "r", encoding=encoding) as f:
                    result["text"] = f.read()
                    result["encoding"] = encoding
                break
            except UnicodeDecodeError:
                continue

        return result

    except Exception as e:
        return {"error": f"Error parsing text file: {str(e)}"}


@tool
def parse_document(file_path: str, file_type: Optional[str] = None) -> str:
    """
    Parse a document and extract its content.

    Supports: PDF, Word (DOCX), PowerPoint (PPTX), Excel (XLSX), images (PNG, JPG, etc.), and text files.

    Args:
        file_path: Path to the document file
        file_type: Optional file type hint (pdf, docx, pptx, xlsx, image, text).
                  If not provided, will be inferred from file extension.

    Returns:
        Parsed document content including text, tables, images, etc.
    """
    if not os.path.exists(file_path):
        return f"Error: File not found: {file_path}"

    # Determine file type
    if not file_type:
        ext = os.path.splitext(file_path)[1].lower()
        type_map = {
            ".pdf": "pdf",
            ".docx": "docx",
            ".doc": "docx",
            ".pptx": "pptx",
            ".ppt": "pptx",
            ".xlsx": "xlsx",
            ".xls": "xlsx",
            ".png": "image",
            ".jpg": "image",
            ".jpeg": "image",
            ".gif": "image",
            ".bmp": "image",
            ".txt": "text",
            ".md": "text",
            ".csv": "text",
        }
        file_type = type_map.get(ext, "text")

    # Parse based on type
    parsers = {
        "pdf": _parse_pdf,
        "docx": _parse_docx,
        "pptx": _parse_pptx,
        "xlsx": _parse_xlsx,
        "image": _parse_image,
        "text": _parse_text,
    }

    parser = parsers.get(file_type, _parse_text)
    result = parser(file_path)

    # Format output
    if "error" in result:
        return result["error"]

    output = f"# Document: {os.path.basename(file_path)}\n\n"
    output += f"**Type:** {result['type']}\n"

    if result["type"] == "pdf":
        output += f"**Total Pages:** {result['total_pages']}\n"
        output += f"\n## Content\n{result['text'][:5000]}"  # Limit to first 5000 chars
        if result["images"]:
            output += f"\n\n**Images Found:** {len(result['images'])}"

    elif result["type"] == "docx":
        output += f"**Paragraphs:** {len(result['paragraphs'])}\n"
        output += f"**Tables:** {len(result['tables'])}\n"
        output += f"**Images:** {len(result['images'])}\n"
        output += f"\n## Content\n{result['text'][:5000]}"

    elif result["type"] == "pptx":
        output += f"**Total Slides:** {result['total_slides']}\n"
        output += f"**Images:** {len(result['images'])}\n"
        output += f"\n## Content\n{result['text'][:5000]}"

    elif result["type"] == "xlsx":
        output += f"**Total Sheets:** {result['total_sheets']}\n"
        for sheet in result["sheets"]:
            output += f"\n### Sheet: {sheet['name']}\n"
            output += f"**Rows:** {sheet['rows']}, **Columns:** {sheet['columns']}\n"
            # Show first few rows
            for i, row in enumerate(sheet["data"][:5]):
                output += f"{row}\n"
            if sheet["rows"] > 5:
                output += f"... ({sheet['rows'] - 5} more rows)\n"

    elif result["type"] == "image":
        output += f"**Format:** {result['format']}\n"
        output += f"**Size:** {result['size'][0]}x{result['size'][1]} pixels\n"
        output += f"**Mode:** {result['mode']}\n"
        output += f"\n**Base64 Data (first 200 chars):** {result['base64'][:200]}...\n"
        output += "\n*Note: Full base64 image data available for multimodal LLM processing*"

    elif result["type"] == "text":
        output += f"**Encoding:** {result['encoding']}\n"
        output += f"\n## Content\n{result['text'][:5000]}"

    return output


@tool
def extract_text_from_document(file_path: str) -> str:
    """
    Extract only text content from a document (simplified version of parse_document).

    Args:
        file_path: Path to the document file

    Returns:
        Extracted text content
    """
    result = parse_document.invoke({"file_path": file_path})

    # If it's a structured result, extract just the text
    if isinstance(result, dict) and "text" in result:
        return result["text"]

    return result


@tool
def get_image_for_llm(file_path: str) -> str:
    """
    Get an image in a format suitable for multimodal LLM processing.

    Args:
        file_path: Path to the image file

    Returns:
        Base64 encoded image data with metadata
    """
    if not os.path.exists(file_path):
        return f"Error: File not found: {file_path}"

    ext = os.path.splitext(file_path)[1].lower()
    if ext not in [".png", ".jpg", ".jpeg", ".gif", ".bmp"]:
        return f"Error: File is not an image: {file_path}"

    result = _parse_image(file_path)

    if "error" in result:
        return result["error"]

    return f"""Image: {os.path.basename(file_path)}
Format: {result['format']}
Size: {result['size'][0]}x{result['size'][1]} pixels
Mode: {result['mode']}

Base64 Data:
{result['base64']}
"""


# Export all tools
DOCUMENT_PARSER_TOOLS = [
    parse_document,
    extract_text_from_document,
    get_image_for_llm,
]
