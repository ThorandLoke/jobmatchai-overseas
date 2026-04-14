#!/usr/bin/env python3
"""PDF 文本提取工具 - 使用 pdfminer.six"""

import sys
import json
from io import BytesIO
from pdfminer.high_level import extract_text

def extract_pdf_text(pdf_path: str) -> str:
    """从 PDF 提取文本"""
    try:
        text = extract_text(pdf_path)
        return text.strip()
    except Exception as e:
        return f"ERROR: {str(e)}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No PDF path provided"}))
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    text = extract_pdf_text(pdf_path)
    
    if text.startswith("ERROR:"):
        print(json.dumps({"error": text.replace("ERROR: ", "")}))
    else:
        print(json.dumps({"success": True, "text": text, "textLength": len(text)}))
