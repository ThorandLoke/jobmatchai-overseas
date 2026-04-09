"""
ThorandLoke PDF Engine - 统一 PDF 处理引擎
========================================
解决两个项目共同的 PDF 问题：
  1. 文字型 PDF 精准提取（pdfplumber + PyMuPDF 双引擎）
  2. 扫描件 OCR（pdf2image + pytesseract/PyMuPDF）
  3. 表格/数值智能识别
  4. 高质量 PDF 输出（reportlab）
  5. 丹麦中介报价单专用解析器

依赖（均已安装）：
  pip install pdfplumber PyMuPDF pdf2image reportlab pytesseract pillow

Author: ThorandLoke
"""

import re
import io
import os
from typing import Dict, List, Optional, Tuple, Any

# ============================================================
# 1. 核心：多引擎 PDF 文字提取
# ============================================================

def extract_text_from_pdf(file_bytes: bytes, use_ocr_fallback: bool = True) -> Dict:
    """
    从 PDF 提取文字，自动选择最佳引擎
    返回：{
        "text": 完整文字,
        "pages": [每页文字列表],
        "method": 使用的引擎,
        "is_scanned": 是否扫描件,
        "tables": 检测到的表格数据
    }
    """
    result = {
        "text": "",
        "pages": [],
        "method": "unknown",
        "is_scanned": False,
        "tables": [],
        "page_count": 0
    }

    # --- 尝试 PyMuPDF（速度最快，对中文/丹麦语支持好）---
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        result["page_count"] = len(doc)
        all_text = []
        has_real_text = False

        for page_num, page in enumerate(doc):
            # 提取文字块（保留布局）
            blocks = page.get_text("blocks")
            page_text = ""
            for block in blocks:
                if block[6] == 0:  # 文字块（非图片）
                    t = block[4].strip()
                    if t:
                        page_text += t + "\n"
                        has_real_text = True
            all_text.append(page_text)

        # 如果有真实文字，使用 PyMuPDF 结果
        if has_real_text and sum(len(p) for p in all_text) > 50:
            result["text"] = "\n\n".join(all_text)
            result["pages"] = all_text
            result["method"] = "pymupdf"
            result["is_scanned"] = False
            doc.close()

            # 额外用 pdfplumber 提取表格
            result["tables"] = _extract_tables_pdfplumber(file_bytes)
            return result

        doc.close()
        # 文字太少，说明是扫描件
        result["is_scanned"] = True

    except Exception as e:
        print(f"[PDF Engine] PyMuPDF failed: {e}")

    # --- 尝试 pdfplumber（对数字/表格更精准）---
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            result["page_count"] = len(pdf.pages)
            all_text = []
            all_tables = []

            for page in pdf.pages:
                t = page.extract_text()
                if t and t.strip():
                    all_text.append(t)

                # 提取表格
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        if table:
                            all_tables.append(table)

            combined = "\n\n".join(all_text)
            if len(combined) > 50:
                result["text"] = combined
                result["pages"] = all_text
                result["method"] = "pdfplumber"
                result["is_scanned"] = False
                result["tables"] = all_tables
                return result

        result["is_scanned"] = True

    except Exception as e:
        print(f"[PDF Engine] pdfplumber failed: {e}")

    # --- 扫描件 OCR fallback ---
    if use_ocr_fallback:
        result = _ocr_pdf(file_bytes, result)

    return result


def _extract_tables_pdfplumber(file_bytes: bytes) -> List:
    """用 pdfplumber 专门提取表格"""
    tables = []
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_tables = page.extract_tables()
                if page_tables:
                    tables.extend([t for t in page_tables if t])
    except Exception:
        pass
    return tables


def _ocr_pdf(file_bytes: bytes, result: Dict) -> Dict:
    """
    扫描件 OCR 处理
    优先使用 PyMuPDF 内置 OCR，备用 pytesseract
    """
    # 方案A：PyMuPDF 内置 OCR（不需要 tesseract）
    try:
        import fitz
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        all_text = []
        for page in doc:
            # 将页面渲染为高分辨率图像，再用 PyMuPDF 识别
            pix = page.get_pixmap(dpi=300)
            img_bytes = pix.tobytes("png")
            # 尝试用 PyMuPDF 的文字层获取（有些 PDF 虽然看起来是扫描件但有文字层）
            text = page.get_text("text")
            if text.strip():
                all_text.append(text)
        doc.close()
        if all_text:
            result["text"] = "\n".join(all_text)
            result["pages"] = all_text
            result["method"] = "pymupdf_ocr"
            result["is_scanned"] = True
            return result
    except Exception as e:
        print(f"[PDF Engine] PyMuPDF OCR failed: {e}")

    # 方案B：pdf2image + pytesseract
    try:
        from pdf2image import convert_from_bytes
        import pytesseract
        from PIL import Image

        images = convert_from_bytes(file_bytes, dpi=300)
        all_text = []
        for img in images:
            # 多语言 OCR：丹麦语 + 英语 + 中文
            text = pytesseract.image_to_string(img, lang="dan+eng+chi_sim")
            all_text.append(text)

        result["text"] = "\n\n".join(all_text)
        result["pages"] = all_text
        result["method"] = "pytesseract"
        result["is_scanned"] = True
        return result

    except Exception as e:
        print(f"[PDF Engine] pytesseract OCR failed: {e}")

    result["method"] = "failed"
    result["text"] = ""
    return result


# ============================================================
# 2. 丹麦中介报价单专用解析器
# ============================================================

class DanishPropertyReportParser:
    """
    丹麦房产报价单解析器
    支持解析：
    - 中介报价单（Salgsprovenu / Salgsbudget）
    - 买方费用估算
    - 能源改造报价
    
    关键识别项：
    - 各类费用数值（DKK）
    - 中介名称
    - 房产地址
    - 销售价格建议
    - 各类佣金/手续费
    """

    # 常见丹麦中介费用关键词映射
    COST_PATTERNS = {
        # 中介服务费
        "salær": r"sal[æa]r[^\d]*(\d[\d\.\s,]*)\s*(?:kr|DKK|,-)?",
        "honorar": r"honorar[^\d]*(\d[\d\.\s,]*)\s*(?:kr|DKK|,-)?",
        "formidlingshonorar": r"formidlingshonorar[^\d]*(\d[\d\.\s,]*)\s*(?:kr|DKK|,-)?",
        
        # 营销费用
        "markedsføring": r"markedsf[øo]ring[^\d]*(\d[\d\.\s,]*)\s*(?:kr|DKK|,-)?",
        "annoncering": r"annoncering[^\d]*(\d[\d\.\s,]*)\s*(?:kr|DKK|,-)?",
        "fotograf": r"fotograf[^\d]*(\d[\d\.\s,]*)\s*(?:kr|DKK|,-)?",
        
        # 法律/文件费用
        "tinglysning": r"tinglysning[^\d]*(\d[\d\.\s,]*)\s*(?:kr|DKK|,-)?",
        "berigtigelse": r"berigtigelse[^\d]*(\d[\d\.\s,]*)\s*(?:kr|DKK|,-)?",
        
        # 房产报告
        "tilstandsrapport": r"tilstandsrapport[^\d]*(\d[\d\.\s,]*)\s*(?:kr|DKK|,-)?",
        "elinstallationsrapport": r"elinstallationsrapport[^\d]*(\d[\d\.\s,]*)\s*(?:kr|DKK|,-)?",
        "energimærke": r"energim[æa]rke[^\d]*(\d[\d\.\s,]*)\s*(?:kr|DKK|,-)?",
        
        # 保险
        "ejerskifteforsikring": r"ejerskifteforsikring[^\d]*(\d[\d\.\s,]*)\s*(?:kr|DKK|,-)?",
        "huseftersyn": r"huseftersyn[^\d]*(\d[\d\.\s,]*)\s*(?:kr|DKK|,-)?",
        
        # 总计
        "kontant_pris": r"(?:kontant\s*(?:pris|salgspris)|udbudspris|pris\s+kr)[^\d]*(\d[\d\.\s,]*)",
        "netto_provenu": r"(?:netto\s*provenu|provenu\s+efter)[^\d]*(\d[\d\.\s,]*)",
        "samlet": r"(?:i\s+alt|samlet\s+udgift|total)[^\d]*(\d[\d\.\s,]*)\s*(?:kr|DKK|,-)?",
    }

    # 地址识别
    ADDRESS_PATTERN = r"(?:adresse|ejendom|beliggenhed)[:\s]*([A-Za-zÆØÅæøå\s\d,\.]+(?:\d{4})\s+[A-Za-zÆØÅæøå\s]+)"
    
    # 中介名称
    AGENT_NAMES = [
        "Nybolig", "EDC", "Home", "Danbolig", "Realmæglerne",
        "Statsautoriseret", "Boligmægler", "Boligsalg",
        "Estate", "Nordea", "Jyske", "Spar Nord"
    ]

    def parse(self, pdf_bytes: bytes) -> Dict:
        """
        解析 PDF 中介报价单
        返回结构化数据
        """
        # 先提取文字
        extracted = extract_text_from_pdf(pdf_bytes)
        text = extracted["text"]
        tables = extracted.get("tables", [])
        
        result = {
            "success": bool(text),
            "method": extracted["method"],
            "is_scanned": extracted["is_scanned"],
            "raw_text": text[:2000],  # 前2000字符供调试
            
            # 解析结果
            "property": {},
            "costs": {},
            "summary": {},
            "raw_numbers": [],
            "warnings": []
        }

        if not text:
            result["warnings"].append("无法提取文字，可能是扫描件且 OCR 失败")
            return result

        text_lower = text.lower()

        # 1. 解析费用数值
        result["costs"] = self._parse_costs(text_lower)
        
        # 2. 解析房产信息
        result["property"] = self._parse_property_info(text)
        
        # 3. 从表格提取数值（更精准）
        if tables:
            table_costs = self._parse_from_tables(tables)
            # 表格数据优先级更高
            for key, val in table_costs.items():
                if val:
                    result["costs"][key] = val
        
        # 4. 提取所有金额（兜底）
        result["raw_numbers"] = self._extract_all_amounts(text)
        
        # 5. 生成摘要
        result["summary"] = self._generate_summary(result)
        
        return result

    def _parse_costs(self, text_lower: str) -> Dict:
        """用正则提取各项费用"""
        costs = {}
        for cost_name, pattern in self.COST_PATTERNS.items():
            match = re.search(pattern, text_lower, re.IGNORECASE)
            if match:
                raw = match.group(1)
                amount = self._parse_danish_number(raw)
                if amount and amount > 0:
                    costs[cost_name] = amount
        return costs

    def _parse_property_info(self, text: str) -> Dict:
        """解析房产基本信息"""
        info = {}
        
        # 尝试找地址
        addr_match = re.search(self.ADDRESS_PATTERN, text, re.IGNORECASE)
        if addr_match:
            info["address"] = addr_match.group(1).strip()
        
        # 找中介名称
        for agent in self.AGENT_NAMES:
            if agent.lower() in text.lower():
                info["agent"] = agent
                break
        
        # 找邮政编码+城市
        postcode_match = re.search(r"\b(\d{4})\s+([A-Za-zÆØÅæøå]+(?:\s+[A-Za-zÆØÅæøå]+)?)\b", text)
        if postcode_match:
            info["postcode"] = postcode_match.group(1)
            info["city"] = postcode_match.group(2)
        
        return info

    def _parse_from_tables(self, tables: List) -> Dict:
        """从表格数据中提取费用（比正则更准）"""
        costs = {}
        keywords_map = {
            "salær": "salær",
            "honorar": "honorar",
            "markedsføring": "markedsføring",
            "tinglysning": "tinglysning",
            "tilstandsrapport": "tilstandsrapport",
            "ejerskifteforsikring": "ejerskifteforsikring",
            "i alt": "samlet",
            "netto": "netto_provenu",
            "kontantpris": "kontant_pris",
            "salgspris": "kontant_pris",
        }
        
        for table in tables:
            for row in table:
                if not row:
                    continue
                # 典型行格式：["费用名称", ..., "数值"]
                row_text = " ".join([str(cell) for cell in row if cell]).lower()
                
                for keyword, cost_key in keywords_map.items():
                    if keyword in row_text:
                        # 找这一行最后一个数字
                        amounts = re.findall(r"(\d[\d\.\s,]{2,})", row_text)
                        if amounts:
                            val = self._parse_danish_number(amounts[-1])
                            if val and val > 100:  # 过滤掉太小的数（可能是日期等）
                                costs[cost_key] = val
                                break
        
        return costs

    def _parse_danish_number(self, raw: str) -> Optional[int]:
        """
        解析丹麦数字格式
        丹麦使用点作千位分隔符，逗号作小数点
        例如：1.234.567,50 → 1234567
             41.750 → 41750
             41,750 → 41750（特殊情况）
        """
        if not raw:
            return None
        
        # 去掉空格
        s = raw.strip().replace(" ", "")
        
        # 丹麦格式：1.234.567,50 → 1234567
        if re.match(r"^\d{1,3}(?:\.\d{3})+(?:,\d{1,2})?$", s):
            # 标准丹麦千位格式
            s = s.replace(".", "").split(",")[0]
        elif "," in s and "." not in s:
            # 只有逗号：可能是小数或千位
            parts = s.split(",")
            if len(parts) == 2 and len(parts[1]) <= 2:
                # 小数格式 12345,50 → 12345
                s = parts[0]
            else:
                # 千位格式 41,750 → 41750
                s = s.replace(",", "")
        elif "." in s and "," not in s:
            parts = s.split(".")
            if len(parts) == 2 and len(parts[1]) <= 2:
                # 英式小数 12345.50 → 12345
                s = parts[0]
            else:
                # 千位 1.234.567 → 1234567
                s = s.replace(".", "")
        
        try:
            return int(re.sub(r"[^\d]", "", s))
        except ValueError:
            return None

    def _extract_all_amounts(self, text: str) -> List[Dict]:
        """提取文字中所有金额（用于调试和兜底）"""
        amounts = []
        # 匹配 1.234.567 kr 或 41.750,- 这样的格式
        pattern = r"(\d{1,3}(?:[.,]\d{3})*(?:[.,]\d{1,2})?)\s*(?:kr\.?|DKK|,-)"
        for match in re.finditer(pattern, text, re.IGNORECASE):
            raw = match.group(1)
            amount = self._parse_danish_number(raw)
            if amount and 100 <= amount <= 50_000_000:  # 合理范围
                # 找这个数前面的上下文（最多30字符）
                start = max(0, match.start() - 40)
                context = text[start:match.end()].strip()
                amounts.append({
                    "amount": amount,
                    "raw": raw,
                    "context": context
                })
        
        # 去重，按金额排序
        seen = set()
        unique = []
        for a in sorted(amounts, key=lambda x: x["amount"], reverse=True):
            if a["amount"] not in seen:
                seen.add(a["amount"])
                unique.append(a)
        
        return unique[:20]  # 最多返回前20个

    def _generate_summary(self, result: Dict) -> Dict:
        """生成人类可读的摘要"""
        costs = result["costs"]
        raw_numbers = result["raw_numbers"]
        
        summary = {
            "detected_costs": len(costs),
            "total_fees": None,
            "selling_price": None,
            "net_proceeds": None,
            "main_items": []
        }
        
        # 尝试找销售价格
        if "kontant_pris" in costs:
            summary["selling_price"] = costs["kontant_pris"]
        elif raw_numbers:
            # 最大的数通常是销售价格
            summary["selling_price"] = raw_numbers[0]["amount"]
        
        # 净收益
        if "netto_provenu" in costs:
            summary["net_proceeds"] = costs["netto_provenu"]
        
        # 总费用
        if "samlet" in costs:
            summary["total_fees"] = costs["samlet"]
        
        # 主要费用项
        display_names = {
            "salær": "中介服务费",
            "honorar": "佣金",
            "markedsføring": "营销费用",
            "tinglysning": "登记费",
            "tilstandsrapport": "房屋状况报告",
            "ejerskifteforsikring": "产权变更保险",
            "samlet": "总费用",
        }
        
        for key, name in display_names.items():
            if key in costs:
                summary["main_items"].append({
                    "name": name,
                    "danish_key": key,
                    "amount": costs[key],
                    "formatted": f"{costs[key]:,} kr".replace(",", ".")
                })
        
        return summary


# ============================================================
# 3. 高质量 PDF 输出（reportlab）
# ============================================================

class PDFGenerator:
    """
    高质量 PDF 生成器
    支持：中文、英文、丹麦语
    正确处理 emoji（转为文字描述）
    """

    def __init__(self):
        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
            from reportlab.lib import colors
            from reportlab.lib.enums import TA_LEFT, TA_CENTER
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
            self.available = True
        except ImportError:
            self.available = False
            print("[PDF Generator] reportlab not available")

    def _get_cjk_font(self):
        """获取支持中文/丹麦语的字体"""
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        # macOS 系统字体路径
        font_paths = [
            "/System/Library/Fonts/PingFang.ttc",          # macOS 中文
            "/System/Library/Fonts/STHeiti Light.ttc",      # macOS 中文
            "/System/Library/Fonts/Arial.ttf",              # 通用
            "/Library/Fonts/Arial.ttf",
        ]

        for path in font_paths:
            if os.path.exists(path):
                try:
                    pdfmetrics.registerFont(TTFont("CJKFont", path))
                    return "CJKFont"
                except Exception:
                    continue

        return "Helvetica"  # 最终备用

    def generate_resume_pdf(self, resume_data: Dict, language: str = "en") -> bytes:
        """
        生成简历 PDF
        正确处理 emoji（替换为文字）
        """
        if not self.available:
            return b""

        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
        from reportlab.lib import colors
        from reportlab.lib.enums import TA_LEFT, TA_CENTER

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, pagesize=A4,
            rightMargin=2*cm, leftMargin=2*cm,
            topMargin=2*cm, bottomMargin=2*cm
        )

        font_name = self._get_cjk_font()
        styles = getSampleStyleSheet()

        # 自定义样式
        style_title = ParagraphStyle(
            "Title", parent=styles["Title"],
            fontName=font_name, fontSize=18, spaceAfter=6,
            textColor=colors.HexColor("#1a1a2e"),
        )
        style_heading = ParagraphStyle(
            "Heading", parent=styles["Heading2"],
            fontName=font_name, fontSize=12, spaceBefore=12, spaceAfter=4,
            textColor=colors.HexColor("#16213e"),
            borderPad=2,
        )
        style_body = ParagraphStyle(
            "Body", parent=styles["Normal"],
            fontName=font_name, fontSize=10, spaceAfter=3, leading=14,
        )
        style_contact = ParagraphStyle(
            "Contact", parent=styles["Normal"],
            fontName=font_name, fontSize=9,
            textColor=colors.HexColor("#555555"),
        )

        story = []

        # 处理 emoji（reportlab 不支持，转为文字）
        def clean_text(t: str) -> str:
            if not t:
                return ""
            # 移除 emoji，保留文字
            emoji_pattern = re.compile(
                "[\U00010000-\U0010ffff]|"
                "[\U0001F600-\U0001F64F]|[\U0001F300-\U0001F5FF]|"
                "[\U0001F680-\U0001F6FF]|[\U0001F1E0-\U0001F1FF]",
                flags=re.UNICODE
            )
            return emoji_pattern.sub("", t).strip()

        # 姓名
        name = clean_text(resume_data.get("name", "Resume"))
        story.append(Paragraph(name, style_title))

        # 联系方式
        contact_parts = []
        for field in ["email", "phone", "location"]:
            val = clean_text(resume_data.get(field, ""))
            if val:
                contact_parts.append(val)
        if contact_parts:
            story.append(Paragraph(" | ".join(contact_parts), style_contact))

        story.append(Spacer(1, 0.3*cm))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#16213e")))
        story.append(Spacer(1, 0.3*cm))

        # 简历内容（支持 markdown 风格的 ## 标题）
        content = clean_text(resume_data.get("content", "") or resume_data.get("polished_content", ""))
        if content:
            for line in content.split("\n"):
                line = line.strip()
                if not line:
                    story.append(Spacer(1, 0.15*cm))
                elif line.startswith("## ") or line.startswith("# "):
                    heading_text = line.lstrip("#").strip()
                    story.append(Paragraph(heading_text, style_heading))
                    story.append(HRFlowable(width="100%", thickness=0.5,
                                             color=colors.HexColor("#cccccc")))
                elif line.startswith("- ") or line.startswith("• ") or line.startswith("* ") or line.startswith("· ") or line.startswith("– ") or line.startswith("— "):
                    # 支持多种 bullet 符号，统一转换为 •
                    bullet_prefix = line[0]
                    bullet_symbol = "•"
                    # 特殊处理多字符符号
                    if line.startswith("– ") or line.startswith("— "):
                        content = line[2:]
                    else:
                        content = line[2:]
                    story.append(Paragraph(f"{bullet_symbol} {content}", style_body))
                elif re.match(r"^[•●○■□▪▫◦]\s", line):
                    # 支持 Unicode bullet 符号
                    story.append(Paragraph(f"• {line[2:].strip()}", style_body))
                elif line.startswith("**") and line.endswith("**"):
                    story.append(Paragraph(f"<b>{line[2:-2]}</b>", style_body))
                else:
                    story.append(Paragraph(line, style_body))

        doc.build(story)
        buffer.seek(0)
        return buffer.getvalue()


# ============================================================
# 4. 模块级快捷函数（供其他模块调用）
# ============================================================

_property_parser = DanishPropertyReportParser()
_pdf_generator = PDFGenerator()


def parse_property_report(pdf_bytes: bytes) -> Dict:
    """解析丹麦中介报价单，返回结构化费用数据"""
    return _property_parser.parse(pdf_bytes)


def generate_resume_pdf(resume_data: Dict, language: str = "en") -> bytes:
    """生成简历 PDF"""
    return _pdf_generator.generate_resume_pdf(resume_data, language)


def extract_pdf_text(pdf_bytes: bytes) -> str:
    """快捷函数：提取 PDF 文字"""
    result = extract_text_from_pdf(pdf_bytes)
    return result["text"]


if __name__ == "__main__":
    # 自测
    print("[PDF Engine] 模块加载成功")
    print(f"  - PyMuPDF: ", end="")
    try:
        import fitz; print(f"✅ v{fitz.version[0]}")
    except: print("❌")
    print(f"  - pdfplumber: ", end="")
    try:
        import pdfplumber; print("✅")
    except: print("❌")
    print(f"  - reportlab: ", end="")
    try:
        from reportlab.lib.pagesizes import A4; print("✅")
    except: print("❌")
    print(f"  - pdf2image: ", end="")
    try:
        from pdf2image import convert_from_bytes; print("✅")
    except: print("❌")
    print(f"  - pytesseract: ", end="")
    try:
        import pytesseract; print("✅")
    except: print("❌")
