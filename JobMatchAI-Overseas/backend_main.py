"""
JobMatchAI - 智能求职助手
支持：中国、北欧、全球市场
核心功能：简历精修 + 邮件职位聚合 + 智能求职信 + 职位匹配

Copyright © 2026 JobMatchAI. All rights reserved.
"""
from fastapi import FastAPI, UploadFile, File, Form, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse, StreamingResponse
from pydantic import BaseModel
from typing import List, Optional, Dict
import uvicorn
import os
import re
import io
import json
import jwt
import unicodedata

# AI 配置 - 质量优先：简历用GPT-4o，求职信用GPT-4o-mini
# 首先尝试从 .env 文件加载环境变量
def load_env_file():
    """从 .env 文件加载环境变量"""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key] = value

# 加载 .env 文件
load_env_file()

try:
    from openai import OpenAI
    openai_api_key = os.getenv("OPENAI_API_KEY")
    groq_api_key = os.getenv("GROQ_API_KEY")

    if openai_api_key:
        # 优先使用 OpenAI（质量优先策略）
        ai_client = OpenAI(api_key=openai_api_key)
        AI_PROVIDER = "openai"
        AI_MODEL_RESUME = os.getenv("AI_MODEL_RESUME", "gpt-4o")
        AI_MODEL_COVER = os.getenv("AI_MODEL_COVER", "gpt-4o-mini")
        AI_MODEL = AI_MODEL_RESUME
        print(f"✅ Using OpenAI API | Resume: {AI_MODEL_RESUME} | Cover: {AI_MODEL_COVER}")
    elif groq_api_key:
        # 备用：Groq 免费方案
        ai_client = OpenAI(
            api_key=groq_api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        AI_PROVIDER = "groq"
        AI_MODEL_RESUME = "llama-3.1-70b-versatile"
        AI_MODEL_COVER = "llama-3.1-70b-versatile"
        AI_MODEL = AI_MODEL_RESUME
        print("✅ Using Groq API (Free tier)")
    else:
        ai_client = None
        AI_PROVIDER = None
        AI_MODEL_RESUME = None
        AI_MODEL_COVER = None
        AI_MODEL = None
        print("⚠️ No AI API key found, using fallback mode")

    AI_AVAILABLE = AI_PROVIDER is not None
except Exception as e:
    AI_AVAILABLE = False
    AI_PROVIDER = None
    AI_MODEL_RESUME = None
    AI_MODEL_COVER = None
    AI_MODEL = None
    print(f"⚠️ AI client init failed: {e}, using fallback mode")

app = FastAPI(title="JobMatchAI Nordic API", version="2.0.0")

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === 数据模型 ===
class Job(BaseModel):
    title: str
    company: str
    location: str
    description: str
    url: Optional[str] = ""
    source: str  # linkedin, jobindex, jobnet, etc.
    language: str = "da"  # zh, en, da

class ResumeAnalysis(BaseModel):
    skills: List[str]
    experience_years: int
    strengths: List[str]
    improvements: List[Dict]
    suggested_profile: str

# === 简历解析 ===
# 导入统一 PDF 处理引擎
try:
    from pdf_engine import extract_text_from_pdf, DanishPropertyReportParser, PDFGenerator
    PDF_ENGINE_AVAILABLE = True
    print("✅ PDF Engine loaded (PyMuPDF + pdfplumber + OCR)")
except ImportError as e:
    PDF_ENGINE_AVAILABLE = False
    print(f"⚠️ PDF Engine not available: {e}")

def parse_resume(file_content: bytes, filename: str) -> str:
    """解析简历文件 - PDF / DOCX / TXT
    
    使用统一 PDF 引擎，支持：
    - 文字型 PDF（PyMuPDF 快速提取）
    - 扫描件 PDF（OCR 识别）
    - DOCX、TXT
    """
    text = ""
    filename_lower = filename.lower()
    
    try:
        if filename_lower.endswith('.pdf'):
            # 优先使用统一 PDF 引擎
            if PDF_ENGINE_AVAILABLE:
                result = extract_text_from_pdf(file_content, use_ocr_fallback=True)
                text = result.get("text", "")
                method = result.get("method", "unknown")
                is_scanned = result.get("is_scanned", False)
                if text:
                    print(f"✅ PDF parsed via {method}, scanned={is_scanned}, chars={len(text)}")
                else:
                    print(f"⚠️ PDF engine returned empty text, method={method}")
            
            # 备用：pdfplumber
            if not text:
                try:
                    import pdfplumber
                    with pdfplumber.open(io.BytesIO(file_content)) as pdf:
                        for page in pdf.pages:
                            t = page.extract_text()
                            if t:
                                text += t + "\n"
                    if text:
                        print(f"✅ PDF parsed via pdfplumber fallback, chars={len(text)}")
                except Exception as e1:
                    print(f"pdfplumber fallback failed: {e1}")
            
            # 最终备用：PyPDF2
            if not text:
                try:
                    from PyPDF2 import PdfReader
                    reader = PdfReader(io.BytesIO(file_content))
                    for page in reader.pages:
                        t = page.extract_text()
                        if t:
                            text += t + "\n"
                    if text:
                        print(f"✅ PDF parsed via PyPDF2 fallback, chars={len(text)}")
                except Exception as e2:
                    print(f"PyPDF2 also failed: {e2}")
                            
        elif filename_lower.endswith('.docx'):
            try:
                import docx
                document = docx.Document(io.BytesIO(file_content))
                for para in document.paragraphs:
                    if para.text.strip():
                        text += para.text + "\n"
                for table in document.tables:
                    for row in table.rows:
                        row_texts = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                        if row_texts:
                            text += " | ".join(row_texts) + "\n"
            except Exception as e:
                print(f"DOCX解析失败: {e}")
        
        elif filename_lower.endswith('.txt'):
            for encoding in ['utf-8', 'utf-16', 'latin-1', 'gb18030']:
                try:
                    text = file_content.decode(encoding)
                    break
                except:
                    continue
                
    except Exception as e:
        print(f"解析错误: {e}")
    
    lines = [l for l in text.splitlines() if l.strip()]
    return "\n".join(lines)

# === 语言检测 ===
def detect_language(text: str) -> str:
    """检测文本语言：zh, en, da"""
    text_lower = text.lower()
    
    # 检测中文字符（最优先）
    zh_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    if zh_chars > 3:
        return 'zh'
    
    # 检测丹麦语特有字符（æ, ø, å）- 最可靠的丹麦语特征
    da_chars = sum(1 for c in ['æ', 'ø', 'å'] if c in text_lower)
    if da_chars >= 1:
        return 'da'
    
    # 检测丹麦语特有词汇（短词如 'en', 'er' 不可靠，容易误判）
    # 用更长的丹麦语词汇来检测
    da_words = ['erfaring', 'kompetencer', 'erfaringer', 'ansvarlig', 'arbejdsopgaver',
                'stilling', 'beskrivelse', 'kvalifikationer', 'uddannelse', 'erhvervserfaring']
    da_word_count = sum(1 for w in da_words if w in text_lower)
    if da_word_count >= 1:
        return 'da'
    
    # 默认英文（英语简历最常见）
    return 'en'

# === AI 增强简历分析 ===
def analyze_resume_with_ai(text: str, lang: str = 'en') -> Dict:
    """使用 AI 深度分析简历"""
    if not AI_AVAILABLE:
        return analyze_resume_fallback(text, lang)
    
    try:
        prompts = {
            'zh': f"""请分析以下简历，以JSON格式返回：
{{
  "skills": ["技能1", "技能2"],
  "experience_years": 数字,
  "strengths": ["优势1", "优势2", "优势3"],
  "improvements": [
    {{"type": "weak_verb", "priority": "high/medium/low", "description": "问题描述", "suggestion": "改进建议"}}
  ],
  "suggested_profile": "建议的个人简介（50字以内）",
  "ats_score": 数字（1-100 ATS友好度评分）
}}

简历内容：
{text[:3000]}""",
            'en': f"""Please analyze this resume and return JSON:
{{
  "skills": ["skill1", "skill2"],
  "experience_years": number,
  "strengths": ["strength1", "strength2", "strength3"],
  "improvements": [
    {{"type": "weak_verb", "priority": "high/medium/low", "description": "issue", "suggestion": "improvement"}}
  ],
  "suggested_profile": "suggested profile summary (under 50 words)",
  "ats_score": number (1-100 ATS compatibility score)
}}

Resume:
{text[:3000]}""",
            'da': f"""Analyser dette CV og returner JSON:
{{
  "skills": ["kompetence1", "kompetence2"],
  "experience_years": tal,
  "strengths": ["styrke1", "styrke2", "styrke3"],
  "improvements": [
    {{"type": "weak_verb", "priority": "high/medium/low", "description": "problem", "suggestion": "forbedring"}}
  ],
  "suggested_profile": "foreslået profil (under 50 ord)",
  "ats_score": tal (1-100 ATS-score)
}}

CV:
{text[:3000]}"""
        }
        
        response = ai_client.chat.completions.create(
            model=AI_MODEL_RESUME or AI_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional resume analyzer. Return only valid JSON."},
                {"role": "user", "content": prompts.get(lang, prompts['en'])}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        result = json.loads(response.choices[0].message.content)
        result['detected_language'] = lang
        result['ai_enhanced'] = True
        result['ai_provider'] = AI_PROVIDER
        return result
        
    except Exception as e:
        print(f"AI analysis failed: {e}, using fallback")
        return analyze_resume_fallback(text, lang)

def analyze_resume_fallback(text: str, lang: str = 'en') -> Dict:
    """本地规则分析（无需AI）"""
    # 技能关键词库（中英丹）
    skills_db = {
        'zh': ['Python', 'Java', 'ERP', 'NetSuite', 'Dynamics', '项目管理', '数据分析', 'SQL', '财务', '供应链'],
        'en': ['Python', 'Java', 'ERP', 'NetSuite', 'Dynamics', 'Project Management', 'Data Analysis', 'SQL', 'Finance', 'Supply Chain'],
        'da': ['Python', 'Java', 'ERP', 'NetSuite', 'Dynamics', 'Projektledelse', 'Dataanalyse', 'SQL', 'Finans', 'Forsyningskæde']
    }
    
    weak_verbs = {
        'zh': ['做了', '负责了', '参与了', '协助', '帮助'],
        'en': ['did', 'was responsible for', 'worked on', 'helped with', 'assisted'],
        'da': ['lavede', 'var ansvarlig for', 'arbejdede på', 'hjalp med', 'assisterede']
    }
    
    strong_verbs = {
        'zh': ['主导', '推动', '优化', '实现', '提升', '建立', '设计'],
        'en': ['led', 'implemented', 'optimized', 'achieved', 'improved', 'established', 'designed'],
        'da': ['ledede', 'implementerede', 'optimerede', 'opnåede', 'forbedrede', 'etablerede', 'designede']
    }
    
    text_lower = text.lower()
    detected_skills = [s for s in skills_db.get(lang, skills_db['en']) if s.lower() in text_lower]
    detected_weak = [v for v in weak_verbs.get(lang, weak_verbs['en']) if v in text_lower]
    
    improvements = []
    if detected_weak:
        improvements.append({
            'type': 'weak_verb',
            'priority': 'high',
            'description': {'zh': f'检测到 {len(detected_weak)} 处可强化的动词', 'en': f'Found {len(detected_weak)} weak verbs', 'da': f'Fandt {len(detected_weak)} svage verber'}.get(lang, 'Found weak verbs'),
            'suggestion': {'zh': '使用更强动词如"主导"、"实现"', 'en': 'Use stronger verbs like "led", "achieved"', 'da': 'Brug stærkere verber'}.get(lang, 'Use stronger verbs')
        })
    
    years = re.findall(r'(\d+)\s*(?:年|years?|år)', text_lower)
    exp_years = max([int(y) for y in years] + [0])
    
    profile_templates = {
        'zh': f'拥有{exp_years}年ERP系统实施经验，精通NetSuite和Dynamics AX。',
        'en': f'Experienced ERP professional with {exp_years}+ years in NetSuite and Dynamics AX.',
        'da': f'Erfaren ERP-professionel med {exp_years}+ års erfaring i NetSuite og Dynamics AX.'
    }
    
    return {
        'skills': detected_skills,
        'experience_years': exp_years,
        'strengths': detected_skills[:3] if detected_skills else ['ERP', 'Project Management'],
        'improvements': improvements,
        'suggested_profile': profile_templates.get(lang, profile_templates['en']),
        'ats_score': 70,
        'detected_language': lang,
        'ai_enhanced': False
    }

# 保持向后兼容
analyze_resume = analyze_resume_with_ai

# === AI 增强求职信生成 ===
def generate_cover_letter_with_ai(resume_text: str, job: Dict, lang: str = 'en') -> str:
    """使用 AI 生成高质量求职信
    
    支持 LinkedIn 导入职位的三语生成（中/英/丹）
    """
    if not AI_AVAILABLE:
        return generate_cover_letter_fallback(resume_text, job, lang)
    
    try:
        # 职位来源（如果是 LinkedIn，优化 prompt）
        is_linkedin = 'linkedin' in str(job.get('source', '')).lower()
        source_hint = ""
        if is_linkedin:
            source_hint = "\n注意：此职位来自 LinkedIn，求职信应该简练有力，突出核心竞争力，适合快速浏览。"
        
        prompts = {
            'zh': f"""基于以下简历和职位信息，写一封专业的求职信（300-400字）：

简历亮点：
{resume_text[:1500]}

职位信息：
- 公司：{job.get('company', '')}
- 职位：{job.get('title', '')}
- 地点：{job.get('location', '')}
- 要求：{job.get('description', '')[:800]}
{source_hint}

要求：
1. 突出简历中与职位匹配的经验
2. 使用专业但真诚的语气
3. 结构：开头（表达兴趣）→ 中间（2-3个匹配点，有具体例子）→ 结尾（行动号召）
4. 如果简历中有相关行业/公司经验，重点提及
5. 直接返回求职信正文，不要JSON""",
            'en': f"""Write a professional cover letter (300-400 words) based on:

Resume highlights:
{resume_text[:1500]}

Job details:
- Company: {job.get('company', '')}
- Position: {job.get('title', '')}
- Location: {job.get('location', '')}
- Requirements: {job.get('description', '')[:800]}
{source_hint}

Requirements:
1. Highlight relevant experience matching the job (be specific with examples)
2. Professional yet genuine tone — avoid generic phrases
3. Structure: Opening (hook) → Body (2-3 match points with concrete examples) → Closing (call to action)
4. If resume shows relevant industry/company experience, emphasize it
5. Return only the cover letter text, no JSON""",
            'da': f"""Skriv en professionel ansøgning (300-400 ord) baseret på:

CV-højdepunkter:
{resume_text[:1500]}

Jobdetaljer:
- Virksomhed: {job.get('company', '')}
- Stilling: {job.get('title', '')}
- Lokation: {job.get('location', '')}
- Krav: {job.get('description', '')[:800]}
{source_hint}

Krav:
1. Fremhæv relevant erfaring der matcher jobbet (vær konkret med eksempler)
2. Professionel men oprigtig tone — undgå generiske fraser
3. Struktur: Indledning (hook) → Hoveddel (2-3 matchpunkter med konkrete eksempler) → Afslutning (call to action)
4. Hvis CV viser relevant brancherfaring, fremhæv det
5. Dansk arbejdskultur: direkte kommunikation, fokus på værditilbud, undgå for meget selvros
6. Returner kun ansøgningsteksten, ingen JSON"""
        }
        
        response = ai_client.chat.completions.create(
            model=AI_MODEL_COVER or AI_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional career coach who writes compelling, personalized cover letters. You understand Nordic/Danish work culture — direct communication, value-focused, not overly boastful."},
                {"role": "user", "content": prompts.get(lang, prompts['en'])}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        letter = response.choices[0].message.content.strip()
        return letter
        
    except Exception as e:
        print(f"AI cover letter failed: {e}, using fallback")
        return generate_cover_letter_fallback(resume_text, job, lang)

def generate_cover_letter_fallback(resume_text: str, job: Dict, lang: str = 'en') -> str:
    """模板生成（无需AI）— 针对北欧市场优化"""
    # 提取姓名（从简历第一行或默认）
    name_line = resume_text.strip().split('\n')[0] if resume_text else ""
    # 尝试提取英文姓名
    import re as _re
    name_match = _re.search(r'^([A-Z][a-z]+\s+[A-Z][a-z]+)', name_line)
    name = name_match.group(1) if name_match else "[Dit Navn]"

    templates = {
        'zh': f"""尊敬的招聘经理：

您好！我在{job.get('source', '招聘网站')}上看到贵公司{job.get('company', '')}的{job.get('title', '')}职位，对此非常感兴趣。

基于我的简历，我拥有丰富的相关经验，相信能为贵公司带来价值。

职位要求：
{job.get('description', '')[:500]}...

期待有机会与您进一步交流。

此致
敬礼！

{[name]}""",
        'en': f"""Dear Hiring Manager,

I am writing to express my strong interest in the {job.get('title', '')} position at {job.get('company', '')}.

Based on my experience outlined in my resume, I am confident that I can bring significant value to your team.

Job Requirements:
{job.get('description', '')[:500]}...

I look forward to discussing how my skills align with your needs.

Best regards,

{name}""",
        'da': f"""Kære Rekrutteringsansvarlig,

Jeg skriver for at udtrykke min interesse for stillingen som {job.get('title', '')} hos {job.get('company', '')}.

Baseret på min erfaring beskrevet i mit CV er jeg overbevist om, at jeg kan bidrage med reel værdi til jeres team fra første dag.

Jobkrav:
{job.get('description', '')[:500]}...

Jeg vil meget gerne til en samtale, hvor vi kan drøfte, hvordan mine kompetencer matcher jeres behov.

Med venlig hilsen,

{name}"""
    }
    return templates.get(lang, templates['en'])

# 保持向后兼容
generate_cover_letter = generate_cover_letter_with_ai

# === 职位搜索 API ===
import requests

# Adzuna API 配置 (支持 UK, AU, CA, FR, NL, BE)
ADZUNA_APP_ID = "690f8e34"
ADZUNA_APP_KEY = "9e5d7db533450288d6780344c1c160ba"
ADZUNA_COUNTRIES = {
    "gb": "英国",
    "au": "澳大利亚",
    "ca": "加拿大",
    "fr": "法国",
    "nl": "荷兰",
    "be": "比利时"
}

def search_adzuna(keyword: str, country: str = "gb", location: str = "", limit: int = 10) -> List[Dict]:
    """搜索国际职位 - Adzuna API"""
    url = f"http://api.adzuna.com/v1/api/jobs/{country}/search/1"
    params = {
        "app_id": ADZUNA_APP_ID,
        "app_key": ADZUNA_APP_KEY,
        "what": keyword,
        "results_per_page": min(limit, 50),
        "content-type": "application/json"
    }
    if location:
        params["where"] = location
    
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200:
            return []
        
        data = r.json()
        jobs = []
        country_name = ADZUNA_COUNTRIES.get(country, country.upper())
        
        if "results" in data:
            for j in data["results"]:
                company_val = j.get("company")
                if isinstance(company_val, dict):
                    company_name = company_val.get("display_name", "N/A")
                else:
                    company_name = str(company_val) if company_val else "N/A"
                
                location_val = j.get("location")
                if isinstance(location_val, dict):
                    location_name = location_val.get("display_name", "")
                else:
                    location_name = str(location_val) if location_val else ""
                
                jobs.append({
                    "title": j.get("title", ""),
                    "company": company_name,
                    "location": location_name,
                    "description": j.get("description", "")[:500] if j.get("description") else "",
                    "url": j.get("redirect_url", ""),
                    "date": j.get("created", "")[:10] if j.get("created") else "",
                    "source": f"🇦🇹 Adzuna-{country_name}",
                    "language": "en"
                })
        return jobs
    except Exception as e:
        print(f"Adzuna API Error: {e}")
        return []

# 德国 Arbeitsagentur API
ARBEITSAGENTUR_KEY = "jobboerse-jobsuche"

def search_germany(keyword: str, location: str = "", limit: int = 10) -> List[Dict]:
    """搜索德国职位 - Arbeitsagentur API"""
    # 增强关键词匹配：添加 ERP 相关同义词
    enhanced_keyword = keyword
    erp_synonyms = ['dynamics', 'ax', '365', 'finance', 'erp', 'sap', 'netsuite']
    for syn in erp_synonyms:
        if syn in keyword.lower():
            enhanced_keyword = f"{keyword} {syn}"
            break
    
    url = "https://rest.arbeitsagentur.de/jobboerse/jobsuche-service/v1/app/v1/web/jobsuche"
    params = {
        "was": enhanced_keyword,
        "wo": location if location else "Deutschland",
        "umfang": "VOLLZEIT",
        "page": 1,
        "size": min(limit, 50)
    }
    headers = {
        "X-API-Key": ARBEITSAGENTUR_KEY,
        "Content-Type": "application/json"
    }
    
    try:
        r = requests.get(url, params=params, headers=headers, timeout=15)
        if r.status_code != 200:
            return []
        
        data = r.json()
        jobs = []
        
        for j in data.get("stellenangebote", [])[:limit]:
            jobs.append({
                "title": j.get("titel", ""),
                "company": j.get("arbeitgeber", {}).get("name", "N/A") if isinstance(j.get("arbeitgeber"), dict) else str(j.get("arbeitgeber", "N/A")),
                "location": j.get("arbeitsort", {}).get("ort", "") if isinstance(j.get("arbeitsort"), dict) else str(j.get("arbeitsort", "")),
                "description": j.get("beschreibung", "")[:500] if j.get("beschreibung") else "",
                "url": j.get("refnr", ""),
                "date": j.get("veroeffentlichungsdatum", "")[:10] if j.get("veroeffentlichungsdatum") else "",
                "source": "🇩🇪 Arbeitsagentur",
                "language": "de"
            })
        return jobs
    except Exception as e:
        print(f"Arbeitsagentur API Error: {e}")
        return []

# 瑞典 Jobtechdev API
JOBTECHDEV_BASE = "https://jobtechdev.se/api/v1"

def search_sweden(keyword: str, location: str = "", limit: int = 10) -> List[Dict]:
    """搜索瑞典职位 - Jobtechdev API"""
    url = f"{JOBTECHDEV_BASE}/search"
    params = {
        "q": keyword,
        "limit": min(limit, 50)
    }
    if location:
        params["place"] = location
    
    try:
        r = requests.get(url, params=params, timeout=15)
        if r.status_code != 200:
            return []
        
        data = r.json()
        jobs = []
        
        for j in data.get("hits", {}).get("hits", [])[:limit]:
            src = j.get("_source", {})
            workplace = src.get("workplace_address", {}) or {}
            jobs.append({
                "title": src.get("headline", ""),
                "company": src.get("employer", {}).get("name", "N/A") if isinstance(src.get("employer"), dict) else "N/A",
                "location": workplace.get("city", "") if isinstance(workplace, dict) else "",
                "description": src.get("description", {}).get("text", "")[:500] if isinstance(src.get("description"), dict) else "",
                "url": j.get("_source", {}).get("webpage_url", ""),
                "date": src.get("publication_date", "")[:10] if src.get("publication_date") else "",
                "source": "🇸🇪 Jobtechdev",
                "language": "sv"
            })
        return jobs
    except Exception as e:
        print(f"Jobtechdev API Error: {e}")
        return []

# === 中国职位搜索（演示数据）===
# 注意：中国主流招聘平台（前程无忧、智联、Boss直聘）均无公开免费API
# 政府网站（人社部公共招聘网）也无开放接口
# 如需真实数据，建议申请企查查API（企业实名，0.5元/次）
CHINA_DEMO_JOBS = [
    {
        "title": "ERP实施顾问（NetSuite/Dynamics）",
        "company": "华为技术有限公司",
        "location": "深圳",
        "description": "负责企业ERP系统实施，负责财务模块或供应链模块的规划与落地。要求5年以上ERP实施经验，熟悉NetSuite或SAP。",
        "url": "https://career.huawei.com",
        "date": "2026-03-28",
        "source": "🇨🇳 演示数据",
        "language": "zh"
    },
    {
        "title": "Dynamics 365 F&O高级顾问",
        "company": "微软中国有限公司",
        "location": "北京",
        "description": "为企业客户提供Dynamics 365 Finance & Operations实施服务，负责项目管理与客户需求分析。英语可作为工作语言。",
        "url": "https://careers.microsoft.com",
        "date": "2026-03-27",
        "source": "🇨🇳 演示数据",
        "language": "zh"
    },
    {
        "title": "Oracle NetSuite实施工程师",
        "company": "阿里巴巴集团",
        "location": "杭州",
        "description": "参与NetSuite项目实施，负责需求调研、方案设计与系统上线。具备Oracle NetSuite认证优先。",
        "url": "https://talent.alibaba.com",
        "date": "2026-03-26",
        "source": "🇨🇳 演示数据",
        "language": "zh"
    },
    {
        "title": "SAP FICO模块顾问",
        "company": "中石化数字化公司",
        "location": "上海",
        "description": "负责SAP FICO模块的实施与优化，进行业务调研、方案设计及用户培训。",
        "url": "https://sinopec.com",
        "date": "2026-03-25",
        "source": "🇨🇳 演示数据",
        "language": "zh"
    },
    {
        "title": "ERP项目经理",
        "company": "腾讯科技有限公司",
        "location": "深圳",
        "description": "主导ERP项目整体规划与执行，管理项目团队与客户关系，协调各方资源确保项目按时交付。",
        "url": "https://careers.tencent.com",
        "date": "2026-03-24",
        "source": "🇨🇳 演示数据",
        "language": "zh"
    },
    {
        "title": "供应链系统分析师",
        "company": "京东集团",
        "location": "北京",
        "description": "分析供应链业务需求，设计并优化ERP系统流程，推进供应链数字化转型。",
        "url": "https://careers.jd.com",
        "date": "2026-03-23",
        "source": "🇨🇳 演示数据",
        "language": "zh"
    }
]

def search_china(keyword: str, location: str = "", limit: int = 10) -> List[Dict]:
    """搜索中国职位（演示数据）
    
    ⚠️ 注意：这是演示数据！
    
    中国主流招聘平台均无免费公开API：
    - 前程无忧(51job)：无公开API
    - 智联招聘：无公开API  
    - Boss直聘：需企业资质（Boss Hi平台）
    - 人社部公共招聘网：无开放接口
    
    如需真实数据，可申请：
    - 企查查API：企业实名，0.5元/次
    """
    # 关键词过滤：模拟根据关键词筛选
    if keyword:
        keyword_lower = keyword.lower()
        filtered = [j for j in CHINA_DEMO_JOBS 
                   if keyword_lower in j["title"].lower() 
                   or keyword_lower in j["description"].lower()
                   or keyword_lower in j["company"].lower()]
    else:
        filtered = CHINA_DEMO_JOBS
    
    # 地点过滤
    if location:
        location_lower = location.lower()
        filtered = [j for j in filtered 
                   if location_lower in j["location"] 
                   or location_lower in j["location"].lower()]
    
    return filtered[:limit]

# === API端点 ===

@app.get("/")
def read_root():
    """返回前端页面"""
    frontend_path = os.path.join(os.path.dirname(__file__), "frontend", "index.html")
    if os.path.exists(frontend_path):
        return FileResponse(frontend_path)
    return {"message": "JobMatchAI Nordic API", "version": "2.0.0"}

@app.get("/beta")
def read_beta_page():
    """返回Beta测试引导页面"""
    beta_path = os.path.join(os.path.dirname(__file__), "frontend", "beta.html")
    if os.path.exists(beta_path):
        return FileResponse(beta_path)
    return {"error": "Beta page not found"}

@app.get("/en")
def read_english_page():
    """返回英文版页面"""
    en_path = os.path.join(os.path.dirname(__file__), "frontend", "index-en.html")
    if os.path.exists(en_path):
        return FileResponse(en_path)
    return {"error": "English page not found"}

@app.get("/health")
def health_check():
    """健康检查"""
    return {"status": "ok", "service": "JobMatchAI Nordic"}

@app.post("/upload-resume")
async def upload_resume(file: UploadFile = File(...)):
    """上传并解析简历"""
    try:
        content = await file.read()
        text = parse_resume(content, file.filename)
        lang = detect_language(text)
        
        return {
            "success": True,
            "filename": file.filename,
            "text": text,
            "detected_language": lang,
            "language_name": {"zh": "中文", "en": "English", "da": "Dansk"}.get(lang, "English")
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/upload-job-document")
async def upload_job_document(file: UploadFile = File(...)):
    """上传并解析职位文档（PDF/DOCX/TXT）"""
    try:
        content = await file.read()
        text = parse_resume(content, file.filename)
        lang = detect_language(text)
        
        # 使用 AI 提取职位信息
        job_info = extract_job_from_text(text, lang)
        
        return {
            "success": True,
            "filename": file.filename,
            "text": text,
            "detected_language": lang,
            "language_name": {"zh": "中文", "en": "English", "da": "Dansk"}.get(lang, "English"),
            "job_info": job_info
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def extract_job_from_text(text: str, lang: str = 'en') -> Dict:
    """从职位文档文本中提取结构化职位信息"""
    if not AI_AVAILABLE:
        # Fallback: 返回原始文本作为描述
        return {
            "title": "",
            "company": "",
            "description": text[:2000],
            "requirements": [],
            "location": "",
            "success": True,
            "source": "Document Upload"
        }
    
    try:
        prompt = f"""You are a job description parser. Extract structured information from the following job posting text.

Text:
{text[:4000]}

Return JSON format:
{{
    "title": "Job title",
    "company": "Company name",
    "description": "Brief job description (max 500 chars)",
    "requirements": ["requirement 1", "requirement 2"],
    "location": "Job location",
    "success": true
}}

If information is not found, use empty string or empty array."""

        response = ai_client.chat.completions.create(
            model=AI_MODEL_RESUME or AI_MODEL,
            messages=[
                {"role": "system", "content": "You are a job description parser. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1500,
            timeout=30
        )
        
        content = response.choices[0].message.content.strip()
        if content.startswith('```'):
            content = content.split('```')[1]
            if content.startswith('json'):
                content = content[4:]
        
        job_info = json.loads(content)
        job_info['success'] = True
        job_info['source'] = 'Document Upload'
        return job_info
        
    except Exception as e:
        print(f"Job extraction failed: {e}")
        return {
            "title": "",
            "company": "",
            "description": text[:2000],
            "requirements": [],
            "location": "",
            "success": True,
            "source": "Document Upload"
        }

@app.post("/analyze-resume")
async def analyze_resume_endpoint(
    resume_text: str = Form(...),
    language: str = Form("auto")
):
    """分析简历并返回改进建议"""
    try:
        if language == "auto":
            lang = detect_language(resume_text)
        else:
            lang = language
        
        analysis = analyze_resume(resume_text, lang)
        
        return {
            "success": True,
            "analysis": analysis,
            "detected_language": lang
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/generate-cover-letter")
async def generate_cover_letter_endpoint(
    resume_text: str = Form(...),
    job_title: str = Form(...),
    company: str = Form(...),
    job_description: str = Form(...),
    language: str = Form("da")
):
    """生成求职信"""
    try:
        job = {
            "title": job_title,
            "company": company,
            "description": job_description,
            "source": "User Input"
        }
        
        cover_letter = generate_cover_letter(resume_text, job, language)
        
        return {
            "success": True,
            "cover_letter": cover_letter,
            "language": language
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/detect-job-language")
def detect_job_language_endpoint(text: str):
    """检测职位描述语言"""
    lang = detect_language(text)
    return {
        "language": lang,
        "language_name": {"zh": "中文", "en": "English", "da": "Dansk"}.get(lang, "English")
    }


# === 智能职位匹配 API（新增）===

from smart_matcher import UserProfileManager, SmartJobMatcher, AutoJobProcessor
from email_reader import JobEmailReader
from linkedin_importer import linkedin_importer, detect_job_language as linkedin_detect_language

# 初始化管理器
profile_manager = UserProfileManager()
job_matcher = SmartJobMatcher(profile_manager)
auto_processor = AutoJobProcessor(profile_manager, job_matcher)

class EmailConfig(BaseModel):
    email: str
    password: str
    imap_server: Optional[str] = None

class JobAction(BaseModel):
    user_id: str
    job: Dict
    action: str  # 'view', 'save', 'apply', 'ignore'

@app.post("/user-profile/create")
async def create_user_profile(user_id: str = Form(...), resume_text: str = Form(...)):
    """从简历创建用户画像"""
    try:
        profile = profile_manager.create_profile(user_id, resume_text)
        return {
            "success": True,
            "profile": {
                "user_id": profile.user_id,
                "skills": profile.skills,
                "total_years": profile.total_years,
                "industries": profile.industries,
                "roles": profile.roles
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/user-profile/{user_id}")
async def get_user_profile(user_id: str):
    """获取用户画像"""
    profile = profile_manager.get_profile(user_id)
    if not profile:
        return {"success": False, "error": "Profile not found"}
    
    return {
        "success": True,
        "profile": profile.to_dict()
    }

@app.post("/user-profile/update-from-resume")
async def update_profile_from_resume(user_id: str = Form(...), resume_text: str = Form(...)):
    """根据更新的简历刷新用户画像"""
    try:
        profile = profile_manager.update_profile_from_resume(user_id, resume_text)
        return {
            "success": True,
            "profile": {
                "user_id": profile.user_id,
                "skills": profile.skills,
                "total_years": profile.total_years,
                "updated_at": profile.updated_at
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/jobs/fetch-from-email")
async def fetch_jobs_from_email(config: EmailConfig):
    """从用户邮箱读取招聘邮件"""
    try:
        reader = JobEmailReader(
            email_address=config.email,
            password=config.password,
            imap_server=config.imap_server
        )
        
        jobs = reader.fetch_job_emails(limit=50)
        reader.disconnect()
        
        return {
            "success": True,
            "count": len(jobs),
            "jobs": jobs
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/jobs/match")
async def match_jobs_endpoint(
    user_id: str = Form(...),
    jobs: str = Form(...)  # JSON字符串
):
    """智能匹配职位"""
    try:
        jobs_list = json.loads(jobs)
        matched_jobs = job_matcher.filter_and_rank_jobs(user_id, jobs_list, min_score=60.0)
        
        return {
            "success": True,
            "total": len(jobs_list),
            "matched": len(matched_jobs),
            "jobs": matched_jobs
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/jobs/process-email-batch")
async def process_email_batch(
    user_id: str = Form(...),
    email_config: str = Form(...)  # JSON字符串
):
    """一键处理：读取邮件 → 智能筛选 → 返回匹配职位"""
    try:
        config = json.loads(email_config)
        
        # 1. 读取邮件
        reader = JobEmailReader(
            email_address=config['email'],
            password=config['password'],
            imap_server=config.get('imap_server')
        )
        jobs = reader.fetch_job_emails(limit=50)
        reader.disconnect()
        
        # 2. 智能筛选
        result = auto_processor.process_email_jobs(user_id, jobs)
        
        # 3. 生成每日摘要
        digest = auto_processor.generate_daily_digest(user_id, jobs)
        
        return {
            "success": True,
            "summary": result['summary'],
            "high_match": result['high_match'],
            "medium_match": result['medium_match'],
            "digest": digest
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/jobs/action")
async def record_job_action(action: JobAction):
    """记录用户对职位的操作（用于学习偏好）"""
    try:
        profile_manager.learn_from_job_action(action.user_id, action.job, action.action)
        return {"success": True, "message": f"Recorded {action.action} action"}
    except Exception as e:
        return {"success": False, "error": str(e)}

# === 职位搜索 API ===
@app.get("/jobs/search")
async def search_jobs(
    keyword: str = "",
    country: str = "all",
    location: str = "",
    limit: int = 10
):
    """统一职位搜索 API
    
    支持的 country 参数:
    - all: 搜索所有来源
    - gb: 英国 (Adzuna)
    - au: 澳大利亚 (Adzuna)
    - ca: 加拿大 (Adzuna)
    - fr: 法国 (Adzuna)
    - nl: 荷兰 (Adzuna)
    - be: 比利时 (Adzuna)
    - de: 德国 (Arbeitsagentur)
    - se: 瑞典 (Jobtechdev)
    - cn: 中国 (演示数据)
    """
    all_jobs = []
    
    try:
        if country == "all":
            # 搜索所有来源
            # 中国（演示数据）
            all_jobs.extend(search_china(keyword, location, limit))
            # 国际 (UK)
            all_jobs.extend(search_adzuna(keyword, "gb", location, limit))
            # 德国
            all_jobs.extend(search_germany(keyword, location, limit))
            # 瑞典
            all_jobs.extend(search_sweden(keyword, location, limit))
        elif country in ["gb", "au", "ca", "fr", "nl", "be"]:
            # Adzuna 国家
            all_jobs.extend(search_adzuna(keyword, country, location, limit))
        elif country == "de":
            # 德国
            all_jobs.extend(search_germany(keyword, location, limit))
        elif country == "se":
            # 瑞典
            all_jobs.extend(search_sweden(keyword, location, limit))
        elif country == "cn":
            # 中国（演示数据）
            all_jobs.extend(search_china(keyword, location, limit))
        else:
            return {"success": False, "error": f"不支持的国家: {country}"}
        
        return {
            "success": True,
            "count": len(all_jobs),
            "jobs": all_jobs[:limit * 3] if country == "all" else all_jobs
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/jobs/sources")
def get_job_sources():
    """获取支持的职位来源"""
    return {
        "success": True,
        "sources": [
            {"id": "all", "name": "全部来源", "flag": "🌐"},
            {"id": "cn", "name": "中国（演示）", "flag": "🇨🇳", "api": "Demo Data"},
            {"id": "gb", "name": "英国", "flag": "🇬🇧", "api": "Adzuna"},
            {"id": "au", "name": "澳大利亚", "flag": "🇦🇺", "api": "Adzuna"},
            {"id": "ca", "name": "加拿大", "flag": "🇨🇦", "api": "Adzuna"},
            {"id": "fr", "name": "法国", "flag": "🇫🇷", "api": "Adzuna"},
            {"id": "nl", "name": "荷兰", "flag": "🇳🇱", "api": "Adzuna"},
            {"id": "be", "name": "比利时", "flag": "🇧🇪", "api": "Adzuna"},
            {"id": "de", "name": "德国", "flag": "🇩🇪", "api": "Arbeitsagentur"},
            {"id": "se", "name": "瑞典", "flag": "🇸🇪", "api": "Jobtechdev"},
        ]
    }


# === 智能简历精修 API（行为数据挖掘）===

from resume_enhancer import (
    BehaviorDataCollector, 
    ResumeEnhancer, 
    DynamicResumeOptimizer,
    HiddenSkill,
    ForgottenExperience
)
from resume_extractor import (
    ResumeExtractor,
    ResumeJobMatcher,
    BatchJobMatcher,
    ResumeProfile,
    MatchResult
)

# 初始化
resume_enhancer = ResumeEnhancer(ai_client) if AI_AVAILABLE else ResumeEnhancer()
dynamic_optimizer = DynamicResumeOptimizer(ai_client) if AI_AVAILABLE else DynamicResumeOptimizer()
resume_extractor = ResumeExtractor()
job_matcher = ResumeJobMatcher()
batch_matcher = BatchJobMatcher()


@app.post("/enhance/collect-behavior")
async def collect_behavior_data(
    user_id: str = Form(...),
    emails: str = Form("[]"),  # JSON字符串
    calendar_events: str = Form("[]"),  # JSON字符串
    documents: str = Form("[]")  # JSON字符串
):
    """收集用户行为数据（邮件、日历、文档）
    
    用于挖掘用户的隐性能力和可能被遗忘的经历
    """
    try:
        import json
        
        # 解析JSON
        emails_list = json.loads(emails) if emails else []
        events_list = json.loads(calendar_events) if calendar_events else []
        docs_list = json.loads(documents) if documents else []
        
        # 收集数据
        collector = BehaviorDataCollector()
        email_data = collector.collect_from_email(emails_list)
        calendar_data = collector.collect_from_calendar(events_list)
        doc_data = collector.collect_from_documents(docs_list)
        
        return {
            "success": True,
            "collected": {
                "email_count": len(emails_list),
                "calendar_events_count": len(events_list),
                "documents_count": len(docs_list)
            },
            "email_data": email_data,
            "calendar_data": calendar_data,
            "doc_data": doc_data
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/enhance/resume")
async def enhance_resume(
    user_id: str = Form(...),
    resume_text: str = Form(...),
    resume_skills: str = Form("[]"),  # JSON字符串
    emails: str = Form("[]"),
    calendar_events: str = Form("[]"),
    documents: str = Form("[]")
):
    """智能简历精修 - 挖掘隐性能力 + 发现遗忘经历
    
    通过分析用户的邮件、日历、文档等行为数据，
    发现简历中可能未体现的隐性能力和可能被遗忘的项目/培训/证书。
    """
    try:
        import json
        
        # 解析数据
        skills_list = json.loads(resume_skills) if resume_skills else []
        emails_list = json.loads(emails) if emails else []
        events_list = json.loads(calendar_events) if calendar_events else []
        docs_list = json.loads(documents) if documents else []
        
        # 收集行为数据
        collector = BehaviorDataCollector()
        email_data = collector.collect_from_email(emails_list)
        calendar_data = collector.collect_from_calendar(events_list)
        doc_data = collector.collect_from_documents(docs_list)
        
        # 分析并生成增强建议
        enhancement = resume_enhancer.analyze_and_enhance(
            user_id=user_id,
            resume_text=resume_text,
            resume_skills=skills_list,
            email_data=email_data,
            calendar_data=calendar_data,
            doc_data=doc_data
        )
        
        return {
            "success": True,
            "hidden_skills": [s.to_dict() for s in enhancement.hidden_skills],
            "forgotten_experiences": [e.to_dict() for e in enhancement.forgotten_experiences],
            "keyword_additions": enhancement.keyword_additions,
            "keyword_weights": enhancement.keyword_weights,
            "suggestions": enhancement.suggestions,
            "ai_insights": enhancement.ai_insights
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/enhance/dynamic-optimize")
async def dynamic_optimize_resume(
    user_id: str = Form(...),
    resume_text: str = Form(...),
    resume_skills: str = Form("[]"),
    job_title: str = Form(...),
    job_company: str = Form(""),
    job_description: str = Form("")
):
    """动态简历优化 - 针对特定职位优化简历
    
    根据目标职位的要求，动态调整简历关键词和表述方式，
    最大化简历与职位的匹配度。
    """
    try:
        import json
        
        skills_list = json.loads(resume_skills) if resume_skills else []
        
        target_job = {
            "title": job_title,
            "company": job_company,
            "description": job_description
        }
        
        # 执行动态优化
        result = dynamic_optimizer.optimize_for_job(
            user_id=user_id,
            resume_text=resume_text,
            resume_skills=skills_list,
            target_job=target_job
        )
        
        return {
            "success": True,
            **result
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/enhance/sources")
def get_behavior_sources():
    """获取支持的行为数据来源"""
    return {
        "success": True,
        "sources": [
            {
                "id": "email",
                "name": "邮件",
                "description": "分析邮件主题和发件人，挖掘项目经验和协作技能",
                "icon": "📧",
                "example": "从'Re: ERP Migration Kickoff'中发现ERP迁移项目经验"
            },
            {
                "id": "calendar",
                "name": "日历",
                "description": "分析日历事件，发现培训和会议参与情况",
                "icon": "📅",
                "example": "从'SAP Certification Workshop'中发现可能的证书"
            },
            {
                "id": "documents",
                "name": "文档/笔记",
                "description": "分析文档标题和笔记内容，发现专业技能",
                "icon": "📄",
                "example": "从技术文档标题中发现PowerBI、Python等技能"
            },
            {
                "id": "job_views",
                "name": "浏览记录",
                "description": "分析浏览过的职位，发现用户的真实兴趣",
                "icon": "👀",
                "example": "通过多次浏览D365职位推断用户对微软生态的偏好"
            }
        ],
        "privacy_note": "所有数据仅在本地处理，不会上传到任何服务器"
    }


# === 简历精准抓取 API ===

@app.post("/extract/resume")
async def extract_resume(resume_text: str = Form(...)):
    """精准抓取简历结构化信息
    
    从简历文本中提取：
    - 基本信息（姓名、邮箱、电话、地点）
    - 工作经历（公司、职位、时间、描述、技能）
    - 教育背景
    - 技能列表
    - 语言能力
    - 证书
    """
    try:
        profile = resume_extractor.extract(resume_text)
        return {
            "success": True,
            "profile": profile.to_dict()
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/extract/match")
async def match_resume_to_job(
    resume_text: str = Form(...),
    job: str = Form(...)  # JSON字符串
):
    """简历与单个职位精准匹配
    
    返回：
    - 综合匹配分数
    - 技能匹配率
    - 经验匹配率
    - 匹配/缺失技能列表
    - 能力差距分析
    - 简历优化建议
    """
    try:
        job_dict = json.loads(job)
        match_result = job_matcher.match(resume_text, job_dict)
        return {
            "success": True,
            "match": match_result.to_dict(),
            "job_title": job_dict.get("title", ""),
            "company": job_dict.get("company", "")
        }
    except Exception as e:
        return {"success": False, "error": str(e)}




@app.post("/extract/batch-match")
async def batch_match_jobs(
    resume_text: str = Form(...),
    jobs: str = Form(...),  # JSON字符串
    min_score: float = Form(50.0)
):
    """批量匹配简历与多个职位
    
    对所有职位按匹配度排序，返回排名结果。
    """
    try:
        jobs_list = json.loads(jobs)
        ranked_jobs = batch_matcher.rank_jobs(resume_text, jobs_list, min_score)
        
        return {
            "success": True,
            "total_jobs": len(jobs_list),
            "matched_jobs": len(ranked_jobs),
            "ranked_jobs": ranked_jobs
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/extract/skill-gap")
async def analyze_skill_gap(
    resume_text: str = Form(...),
    job_description: str = Form(...)
):
    """分析简历与职位描述之间的技能差距
    
    比对简历中已有的技能与职位要求，识别：
    - 完全匹配的技能
    - 部分匹配的技能
    - 完全缺失的技能
    """
    try:
        profile = resume_extractor.extract(resume_text)
        job_dict = {"title": "", "description": job_description, "company": ""}
        match_result = job_matcher.match(resume_text, job_dict)
        
        return {
            "success": True,
            "resume_skills": profile.skills,
            "matched_skills": match_result.matched_skills,
            "partial_skills": match_result.partial_skills,
            "missing_skills": match_result.missing_skills,
            "skill_match_rate": match_result.skill_match_rate,
            "experience_years": profile.total_years,
            "work_experiences": [e.to_dict() for e in profile.work_experiences]
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# === 求职信质量测试 API ===

class CoverLetterQualityChecker:
    """求职信质量检查器"""

    def __init__(self):
        pass

    def check(self, cover_letter: str, job: Dict, resume_text: str = "") -> Dict:
        """检查求职信质量"""
        scores = {}
        issues = []
        suggestions = []

        # 1. 长度检查
        word_count = len(cover_letter.split())
        if 200 <= word_count <= 400:
            scores['length'] = 100
        elif 150 <= word_count < 200 or 400 < word_count <= 500:
            scores['length'] = 70
        else:
            scores['length'] = 40
            issues.append(f"字数 {word_count} 字，理想范围 200-400 词")
            suggestions.append("将求职信长度调整到 200-400 词之间")

        # 2. 结构检查
        structure_keywords = {
            'opening': ['dear', 'dearest', 'hello', '尊敬的', 'kære'],
            'closing': ['regards', 'sincerely', 'best', '致敬', 'med venlig hilsen']
        }
        structure_score = 0
        for section, keywords in structure_keywords.items():
            if any(kw in cover_letter.lower() for kw in keywords):
                structure_score += 50
        scores['structure'] = structure_score
        if structure_score < 100:
            issues.append("求职信缺少开头或结尾称呼")
            suggestions.append("确保包含正式开头（Dear...）和结尾（Best regards...）")

        # 3. 关键词匹配检查
        if job.get('description'):
            job_keywords = set(job['description'].lower().split())
            cover_lower = cover_letter.lower()
            matched = sum(1 for kw in job_keywords if kw in cover_lower and len(kw) > 3)
            total = sum(1 for kw in job_keywords if len(kw) > 3)
            keyword_rate = (matched / max(total, 1)) * 100
            scores['keyword_match'] = min(keyword_rate * 2, 100)
            if keyword_rate < 30:
                suggestions.append("求职信中职位关键词覆盖率较低，建议更多引用职位描述中的关键要求")

        # 4. ATS友好度检查
        ats_score = 100
        bad_patterns = ['***', '████', '[REDACTED]', 'confidential']
        for pat in bad_patterns:
            if pat in cover_letter:
                ats_score -= 30
        if not re.search(r'[a-zA-Z]', cover_letter):
            ats_score = 0
        scores['ats_friendly'] = max(ats_score, 0)

        # 5. 强动词检查
        strong_verbs = ['achieved', 'led', 'implemented', 'improved', 'delivered', 
                        'increased', 'reduced', 'optimized', '主导', '实现', '提升']
        weak_verbs = ['did', 'worked', 'helped', '参与', '做了']
        
        strong_count = sum(1 for v in strong_verbs if v in cover_letter.lower())
        weak_count = sum(1 for v in weak_verbs if v in cover_letter.lower())
        
        if strong_count >= 3 and weak_count <= 1:
            scores['action_verbs'] = 100
        elif strong_count >= 1:
            scores['action_verbs'] = 60
        else:
            scores['action_verbs'] = 30
            suggestions.append("使用更有力的动词（Led, Achieved, Implemented 等）替代弱动词")

        # 6. 个性化检查（是否提到公司名）
        company_mentioned = job.get('company', '') and \
                             job['company'].lower() in cover_letter.lower()
        scores['personalization'] = 100 if company_mentioned else 50
        if not company_mentioned:
            suggestions.append(f"建议在求职信中提到公司名称：{job.get('company', '目标公司')}")

        # 7. 简历匹配度
        resume_match = 50
        if resume_text:
            resume_words = set(resume_text.lower().split())
            cover_words = set(cover_letter.lower().split())
            overlap = len(resume_words & cover_words) / max(len(resume_words), 1)
            resume_match = overlap * 100
        scores['resume_relevance'] = resume_match

        # 综合评分 - 申请成功率视角
        # 核心：简历-职位匹配度 和 关键词匹配率 是申请成功的关键
        weights = {
            'length': 0.10,           # 长度（降低权重）
            'structure': 0.10,       # 结构（降低权重）
            'keyword_match': 0.30,   # 关键词匹配（提高！说明理解职位要求）
            'ats_friendly': 0.10,    # ATS友好（降低权重）
            'action_verbs': 0.10,    # 行动词（降低权重）
            'personalization': 0.10, # 个性化
            'resume_relevance': 0.20 # 简历-职位关联（提高！核心指标）
        }
        overall = sum(scores[k] * weights[k] for k in weights)

        # 评分等级 - 申请成功率视角
        if overall >= 80:
            grade = "🌟 高度推荐"
        elif overall >= 65:
            grade = "✅ 推荐申请"
        elif overall >= 50:
            grade = "⚠️ 谨慎申请"
        else:
            grade = "❌ 不建议申请"

        return {
            "overall_score": round(overall, 1),
            "grade": grade,
            "scores": {k: round(v, 1) for k, v in scores.items()},
            "issues": issues,
            "suggestions": suggestions,
            "word_count": word_count,
            "company_mentioned": company_mentioned
        }


# 初始化求职信检查器
cover_letter_checker = CoverLetterQualityChecker()


@app.post("/cover-letter/check")
async def check_cover_letter(
    cover_letter: str = Form(...),
    job_title: str = Form(""),
    company: str = Form(""),
    job_description: str = Form(""),
    resume_text: str = Form("")
):
    """评估申请成功率
    
    检查维度（申请成功率视角）：
    - 关键词匹配率 (30%) - 理解职位要求的程度
    - 简历-职位关联度 (20%) - 核心！简历能力是否匹配职位
    - 长度、结构、ATS友好度、行动词、个性化 (各10%)
    """
    try:
        job = {
            "title": job_title,
            "company": company,
            "description": job_description
        }
        result = cover_letter_checker.check(cover_letter, job, resume_text)
        
        return {
            "success": True,
            **result
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/cover-letter/check-with-job")
async def check_cover_letter_with_job(
    cover_letter: str = Form(...),
    saved_jobs: str = Form("[]")  # JSON字符串
):
    """根据已保存的职位测试求职信质量
    
    saved_jobs 为包含职位信息的JSON数组
    """
    try:
        jobs_list = json.loads(saved_jobs)
        results = []
        
        for job in jobs_list:
            result = cover_letter_checker.check(cover_letter, job)
            results.append({
                "job_title": job.get("title", ""),
                "company": job.get("company", ""),
                **result
            })
        
        # 按质量分数排序
        results.sort(key=lambda x: x.get("overall_score", 0), reverse=True)
        
        return {
            "success": True,
            "total_jobs": len(jobs_list),
            "results": results
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# === 企业端龙虾接口 API ===

class LobsterCompanyAPI:
    """
    企业端龙虾接口
    
    龙虾(Lobster)是欧洲企业对B2B SaaS平台的昵称，
    这里指为企业HR/招聘团队提供的接口服务：
    - 接收投递的职位申请
    - 简历自动筛选
    - 候选人匹配排序
    - 申请状态管理
    """

    def __init__(self):
        # 企业注册表（内存存储，可扩展到数据库）
        self._companies: Dict[str, Dict] = {}
        self._job_postings: Dict[str, List[Dict]] = {}
        self._applications: Dict[str, List[Dict]] = {}

    def register_company(self, company_id: str, company_name: str, 
                         api_key: str, industry: str = "") -> Dict:
        """注册企业"""
        self._companies[company_id] = {
            "company_id": company_id,
            "name": company_name,
            "api_key": api_key,
            "industry": industry,
            "registered_at": "2026-04-01",
            "status": "active"
        }
        self._job_postings[company_id] = []
        self._applications[company_id] = []
        return self._companies[company_id]

    def post_job(self, company_id: str, job: Dict) -> Dict:
        """发布职位"""
        job_id = f"{company_id}_{len(self._job_postings.get(company_id, [])) + 1}"
        job_entry = {
            "job_id": job_id,
            "company_id": company_id,
            "title": job.get("title", ""),
            "description": job.get("description", ""),
            "requirements": job.get("requirements", ""),
            "location": job.get("location", ""),
            "salary_range": job.get("salary_range", ""),
            "status": "active",
            "posted_at": "2026-04-01",
            "applications_count": 0
        }
        if company_id not in self._job_postings:
            self._job_postings[company_id] = []
        self._job_postings[company_id].append(job_entry)
        return job_entry

    def submit_application(self, company_id: str, job_id: str, 
                           applicant: Dict) -> Dict:
        """接收职位申请"""
        app_id = f"APP_{company_id}_{len(self._applications.get(company_id, [])) + 1}"
        application = {
            "application_id": app_id,
            "job_id": job_id,
            "company_id": company_id,
            "applicant_name": applicant.get("name", ""),
            "applicant_email": applicant.get("email", ""),
            "resume_text": applicant.get("resume_text", ""),
            "cover_letter": applicant.get("cover_letter", ""),
            "status": "new",  # new, screening, interview, offer, rejected
            "submitted_at": "2026-04-01",
            "match_score": 0
        }
        
        # 自动计算匹配分
        if applicant.get("resume_text") and job_id:
            job = self._find_job(company_id, job_id)
            if job:
                match_res = job_matcher.match(applicant["resume_text"], job)
                application["match_score"] = match_res.overall_score
        
        if company_id not in self._applications:
            self._applications[company_id] = []
        self._applications[company_id].append(application)
        
        # 更新职位申请计数
        for j in self._job_postings.get(company_id, []):
            if j["job_id"] == job_id:
                j["applications_count"] += 1
                break
        
        return application

    def _find_job(self, company_id: str, job_id: str) -> Optional[Dict]:
        """查找职位"""
        for job in self._job_postings.get(company_id, []):
            if job["job_id"] == job_id:
                return job
        return None

    def get_candidates(self, company_id: str, job_id: str, 
                       min_score: float = 0) -> List[Dict]:
        """获取候选人列表（按匹配度排序）"""
        apps = self._applications.get(company_id, [])
        candidates = [a for a in apps if a["job_id"] == job_id]
        candidates.sort(key=lambda x: x.get("match_score", 0), reverse=True)
        return [c for c in candidates if c["match_score"] >= min_score]

    def update_application_status(self, company_id: str, application_id: str,
                                   new_status: str) -> Dict:
        """更新申请状态"""
        for app in self._applications.get(company_id, []):
            if app["application_id"] == application_id:
                app["status"] = new_status
                return app
        return {}


# 初始化龙虾接口
lobster_api = LobsterCompanyAPI()

# 预注册演示企业
DEMO_COMPANY_ID = "demo_company_001"
lobster_api.register_company(
    company_id=DEMO_COMPANY_ID,
    company_name="Nordic ERP Solutions A/S",
    api_key="lobster_demo_key_2026",
    industry="IT Consulting"
)


@app.post("/lobster/register-company")
async def lobster_register_company(
    company_id: str = Form(...),
    company_name: str = Form(...),
    api_key: str = Form(...),
    industry: str = Form("")
):
    """注册企业（龙虾接口）"""
    try:
        company = lobster_api.register_company(company_id, company_name, api_key, industry)
        return {"success": True, "company": company}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/lobster/post-job")
async def lobster_post_job(
    company_id: str = Form(...),
    job: str = Form(...)  # JSON字符串
):
    """发布职位（龙虾接口）"""
    try:
        job_dict = json.loads(job)
        job_entry = lobster_api.post_job(company_id, job_dict)
        return {"success": True, "job": job_entry}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/lobster/submit-application")
async def lobster_submit_application(
    company_id: str = Form(...),
    job_id: str = Form(...),
    applicant: str = Form(...)  # JSON字符串
):
    """提交职位申请（龙虾接口）
    
    自动：
    1. 接收简历和求职信
    2. 计算与职位的匹配分
    3. 按匹配度排序候选人
    """
    try:
        applicant_dict = json.loads(applicant)
        application = lobster_api.submit_application(company_id, job_id, applicant_dict)
        return {
            "success": True,
            "application": application,
            "message": f"申请已提交！匹配度评分：{application['match_score']}%"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/lobster/candidates/{company_id}/{job_id}")
async def lobster_get_candidates(
    company_id: str,
    job_id: str,
    min_score: float = 0
):
    """获取职位候选人列表（按匹配度排序）"""
    try:
        candidates = lobster_api.get_candidates(company_id, job_id, min_score)
        return {
            "success": True,
            "job_id": job_id,
            "total": len(candidates),
            "candidates": candidates
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/lobster/jobs/{company_id}")
async def lobster_get_jobs(company_id: str):
    """获取企业的所有职位"""
    jobs = lobster_api._job_postings.get(company_id, [])
    return {"success": True, "jobs": jobs}


# === Stripe 付费系统 API ===

import stripe
from datetime import datetime

# Stripe 配置
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")

stripe_client = None
if STRIPE_SECRET_KEY:
    try:
        stripe.api_key = STRIPE_SECRET_KEY
        stripe_client = stripe
        print(f"✅ Stripe 已连接")
    except Exception as e:
        print(f"⚠️ Stripe 初始化失败: {e}")

# 订阅套餐配置
SUBSCRIPTION_PLANS = {
    "monthly": {
        "name": "月卡",
        "price_id": os.getenv("STRIPE_PRICE_MONTHLY", "price_monthly_placeholder"),
        "price": 29,  # ¥ / 月
        "currency": "cny",
        "interval": "month",
        "features": [
            "✅ 10次职位搜索",
            "✅ 3次简历分析",
            "✅ 10份求职信生成",
            "✅ 10次AI智能匹配",
            "✅ 3次行为数据挖掘",
        ],
        "tagline": "💡 每天不到1块钱"
    },
    "quarterly": {
        "name": "季卡",
        "price_id": os.getenv("STRIPE_PRICE_QUARTERLY", "price_quarterly_placeholder"),
        "price": 79,  # ¥ / 季
        "currency": "cny",
        "interval": "quarter",
        "features": [
            "✅ 30次职位搜索",
            "✅ 10次简历分析",
            "✅ 30份求职信生成",
            "✅ 30次AI智能匹配",
            "✅ 10次行为数据挖掘",
        ],
        "tagline": "💡 比月卡省¥8"
    },
    "yearly": {
        "name": "年卡",
        "price_id": os.getenv("STRIPE_PRICE_YEARLY", "price_yearly_placeholder"),
        "price": 199,  # ¥ / 年
        "currency": "cny",
        "interval": "year",
        "features": [
            "✅ 无限职位搜索",
            "✅ 无限简历分析",
            "✅ 无限求职信生成",
            "✅ 无限AI智能匹配",
            "✅ 30次行为数据挖掘",
            "✅ 申请追踪",
            "✅ 企业端龙虾接口"
        ],
        "tagline": "💡 最超值，省¥149"
    }
}

# 用户订阅状态（内存存储，生产环境应使用数据库）
user_subscriptions: Dict[str, Dict] = {}


class StripeManager:
    """Stripe 订阅管理器"""

    def __init__(self):
        self.plans = SUBSCRIPTION_PLANS

    def get_plans(self) -> List[Dict]:
        """获取所有订阅套餐"""
        result = []
        for plan_id, plan in self.plans.items():
            result.append({
                "id": plan_id,
                "name": plan["name"],
                "price": plan["price"],
                "currency": plan["currency"],
                "interval": plan["interval"],
                "features": plan["features"],
                "savings": self._calculate_savings(plan_id)
            })
        return result

    def _calculate_savings(self, plan_id: str) -> str:
        """计算节省金额"""
        monthly_total = 79 * 12
        plan = self.plans.get(plan_id, {})
        yearly_price = plan.get("price", 0)
        if plan_id == "yearly" and yearly_price > 0:
            saved = monthly_total - yearly_price
            return f"省 {saved} DKK/年"
        elif plan_id == "quarterly" and yearly_price > 0:
            saved = monthly_total - yearly_price * 4
            return f"省 {saved} DKK/年"
        return ""

    def create_checkout_session(self, plan_id: str, user_id: str,
                                 success_url: str = "/?payment=success",
                                 cancel_url: str = "/?payment=cancelled") -> Dict:
        """创建 Stripe Checkout Session"""
        if not stripe_client:
            # Demo 模式：模拟支付流程
            return self._create_demo_checkout(plan_id, user_id)

        plan = self.plans.get(plan_id)
        if not plan:
            return {"success": False, "error": "Invalid plan"}

        try:
            session = stripe_client.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[{
                    'price_data': {
                        'currency': plan["currency"],
                        'product_data': {
                            'name': f"JobMatchAI {plan['name']}",
                            'description': f"Access to all JobMatchAI features for {plan['interval']}"
                        },
                        'unit_amount': plan["price"] * 100,  # Stripe 使用分
                    },
                    'quantity': 1,
                }],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "user_id": user_id,
                    "plan_id": plan_id
                },
                customer_email=None
            )
            return {
                "success": True,
                "session_id": session.id,
                "checkout_url": session.url
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _create_demo_checkout(self, plan_id: str, user_id: str) -> Dict:
        """创建演示用 checkout（无真实 Stripe key）"""
        plan = self.plans.get(plan_id, {})
        demo_session_id = f"demo_session_{user_id}_{plan_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        return {
            "success": True,
            "demo_mode": True,
            "session_id": demo_session_id,
            "checkout_url": f"/#/payment/demo?plan={plan_id}&session={demo_session_id}",
            "message": "⚠️ Demo模式：配置 STRIPE_SECRET_KEY 后启用真实支付"
        }

    def verify_subscription(self, user_id: str) -> Dict:
        """验证用户订阅状态"""
        sub = user_subscriptions.get(user_id, {})
        plan_id = sub.get("plan_id", "")
        plan = self.plans.get(plan_id, {})

        # 检查是否过期
        expires_at = sub.get("expires_at", "")
        is_active = False
        if expires_at:
            try:
                exp_date = datetime.fromisoformat(expires_at)
                is_active = exp_date > datetime.now()
            except:
                is_active = False

        return {
            "user_id": user_id,
            "is_active": is_active,
            "plan_id": plan_id,
            "plan_name": plan.get("name", "免费版"),
            "expires_at": expires_at,
            "features": plan.get("features", []) if is_active else []
        }

    def activate_subscription(self, user_id: str, plan_id: str) -> Dict:
        """激活订阅（支付成功后调用）"""
        plan = self.plans.get(plan_id)
        if not plan:
            return {"success": False, "error": "Invalid plan"}

        # 计算到期时间
        now = datetime.now()
        interval = plan.get("interval", "month")
        if interval == "month":
            from datetime import timedelta
            expires = now + timedelta(days=30)
        elif interval == "quarter":
            from datetime import timedelta
            expires = now + timedelta(days=90)
        else:
            from datetime import timedelta
            expires = now + timedelta(days=365)

        user_subscriptions[user_id] = {
            "plan_id": plan_id,
            "plan_name": plan["name"],
            "activated_at": now.isoformat(),
            "expires_at": expires.isoformat(),
            "status": "active"
        }

        return {
            "success": True,
            "plan_id": plan_id,
            "plan_name": plan["name"],
            "activated_at": now.isoformat(),
            "expires_at": expires.isoformat()
        }

    def cancel_subscription(self, user_id: str) -> Dict:
        """取消订阅"""
        if user_id in user_subscriptions:
            del user_subscriptions[user_id]
        return {"success": True, "message": "订阅已取消"}

    def get_billing_portal_session(self, user_id: str, return_url: str = "/") -> Dict:
        """获取 Stripe Billing Portal Session"""
        if not stripe_client:
            return {
                "success": False,
                "error": "Stripe not configured",
                "demo_mode": True
            }

        try:
            session = stripe_client.billing_portal.Session.create(
                customer="cus_demo_" + user_id,
                return_url=return_url
            )
            return {
                "success": True,
                "portal_url": session.url
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


# 初始化 Stripe 管理器
stripe_manager = StripeManager()


@app.get("/payment/plans")
def get_payment_plans():
    """获取所有订阅套餐"""
    return {
        "success": True,
        "plans": stripe_manager.get_plans(),
        "currency": "dkk",
        "demo_note": "配置 STRIPE_SECRET_KEY 环境变量启用真实支付" if not STRIPE_SECRET_KEY else ""
    }


@app.get("/payment/subscription/{user_id}")
def get_subscription(user_id: str):
    """获取用户订阅状态"""
    return {
        "success": True,
        "subscription": stripe_manager.verify_subscription(user_id)
    }


@app.post("/payment/create-checkout")
async def create_payment_checkout(
    plan_id: str = Form(...),
    user_id: str = Form(...)
):
    """创建支付会话"""
    try:
        result = stripe_manager.create_checkout_session(plan_id, user_id)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/payment/activate-demo")
async def activate_demo_subscription(
    plan_id: str = Form(...),
    user_id: str = Form(...)
):
    """演示模式：直接激活订阅（无需真实支付）"""
    try:
        result = stripe_manager.activate_subscription(user_id, plan_id)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/payment/cancel")
async def cancel_subscription(user_id: str = Form(...)):
    """取消订阅"""
    try:
        result = stripe_manager.cancel_subscription(user_id)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/payment/webhook")
async def stripe_webhook(request: Request):
    """处理 Stripe Webhook"""
    if not stripe_client:
        return JSONResponse({"received": True}, status_code=200)

    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    try:
        event = stripe_client.webhook.construct_event(
            payload, sig_header, STRIPE_WEBHOOK_SECRET
        )

        if event["type"] == "checkout.session.completed":
            session = event["data"]["object"]
            user_id = session.get("metadata", {}).get("user_id")
            plan_id = session.get("metadata", {}).get("plan_id")
            if user_id and plan_id:
                stripe_manager.activate_subscription(user_id, plan_id)
                print(f"✅ 订阅激活: {user_id} -> {plan_id}")

        elif event["type"] == "customer.subscription.deleted":
            # 处理取消订阅
            pass

        return JSONResponse({"received": True}, status_code=200)
    except Exception as e:
        print(f"⚠️ Webhook 错误: {e}")
        return JSONResponse({"error": str(e)}, status_code=400)


# === 职位申请追踪 API ===

class ApplicationTracker:
    """职位申请追踪器"""

    def __init__(self):
        # 申请记录存储
        self._applications: Dict[str, List[Dict]] = {}

    def add_application(self, user_id: str, application: Dict) -> Dict:
        """添加一条申请记录"""
        if user_id not in self._applications:
            self._applications[user_id] = []
        
        app_entry = {
            "id": f"app_{user_id}_{len(self._applications[user_id]) + 1}",
            "user_id": user_id,
            "job_title": application.get("job_title", ""),
            "company": application.get("company", ""),
            "company_website": application.get("company_website", ""),
            "job_url": application.get("job_url", ""),
            "salary_range": application.get("salary_range", ""),
            "location": application.get("location", ""),
            "status": application.get("status", "applied"),
            "applied_date": application.get("applied_date", "2026-04-01"),
            "deadline": application.get("deadline", ""),
            "contact_name": application.get("contact_name", ""),
            "contact_email": application.get("contact_email", ""),
            "notes": application.get("notes", ""),
            "interview_date": "",
            "interview_notes": "",
            "offer_received": False,
            "rejected": False,
            "follow_up_date": "",
            "priority": application.get("priority", "normal"),  # high, normal, low
            "match_score": application.get("match_score", 0),
            "updated_at": "2026-04-01"
        }
        
        self._applications[user_id].append(app_entry)
        return app_entry

    def get_applications(self, user_id: str, status: str = "all") -> List[Dict]:
        """获取用户的申请列表"""
        apps = self._applications.get(user_id, [])
        if status != "all":
            apps = [a for a in apps if a["status"] == status]
        # 按更新时间和优先级排序
        priority_order = {"high": 0, "normal": 1, "low": 2}
        apps.sort(key=lambda x: (priority_order.get(x["priority"], 1), -x.get("match_score", 0)))
        return apps

    def update_status(self, user_id: str, application_id: str, 
                      new_status: str, notes: str = "") -> Dict:
        """更新申请状态"""
        for app in self._applications.get(user_id, []):
            if app["id"] == application_id:
                old_status = app["status"]
                app["status"] = new_status
                app["updated_at"] = "2026-04-01"
                if notes:
                    app["notes"] = notes
                if new_status == "rejected":
                    app["rejected"] = True
                if new_status == "offer":
                    app["offer_received"] = True
                return app
        return {}

    def get_statistics(self, user_id: str) -> Dict:
        """获取申请统计"""
        apps = self._applications.get(user_id, [])
        total = len(apps)
        
        status_counts = {}
        for app in apps:
            s = app.get("status", "unknown")
            status_counts[s] = status_counts.get(s, 0) + 1
        
        response_rate = 0
        if total > 0:
            responded = sum(1 for a in apps if a["status"] not in ["applied", "new"])
            response_rate = round(responded / total * 100, 1)
        
        # 本周申请数
        import datetime
        today = datetime.date.today()
        week_apps = [a for a in apps if a.get("applied_date", "") 
                     >= str(today - datetime.timedelta(days=7))]
        
        return {
            "total_applications": total,
            "status_breakdown": status_counts,
            "response_rate": response_rate,
            "this_week": len(week_apps),
            "pending_response": status_counts.get("applied", 0) + status_counts.get("new", 0),
            "interviews": status_counts.get("interview", 0),
            "offers": status_counts.get("offer", 0),
            "rejections": status_counts.get("rejected", 0)
        }


# 初始化申请追踪器
app_tracker = ApplicationTracker()


@app.post("/tracker/add")
async def add_application(
    user_id: str = Form(...),
    application: str = Form(...)  # JSON字符串
):
    """添加职位申请记录"""
    try:
        app_dict = json.loads(application)
        entry = app_tracker.add_application(user_id, app_dict)
        return {"success": True, "application": entry}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/tracker/list/{user_id}")
async def list_applications(
    user_id: str,
    status: str = "all"
):
    """获取申请列表"""
    apps = app_tracker.get_applications(user_id, status)
    return {
        "success": True,
        "count": len(apps),
        "applications": apps
    }


@app.post("/tracker/update-status")
async def update_application_status(
    user_id: str = Form(...),
    application_id: str = Form(...),
    new_status: str = Form(...),
    notes: str = Form("")
):
    """更新申请状态
    
    状态选项：
    - new: 新申请
    - applied: 已投递
    - screening: 筛选中
    - interview: 面试中
    - offer: 已拿到offer
    - rejected: 被拒绝
    - withdrawn: 自己撤回
    - accepted: 已接受
    """
    try:
        app = app_tracker.update_status(user_id, application_id, new_status, notes)
        if app:
            return {"success": True, "application": app}
        return {"success": False, "error": "Application not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/tracker/add-interview")
async def add_interview(
    user_id: str = Form(...),
    application_id: str = Form(...),
    interview_date: str = Form(...),
    interview_notes: str = Form("")
):
    """添加面试信息"""
    for app in app_tracker._applications.get(user_id, []):
        if app["id"] == application_id:
            app["interview_date"] = interview_date
            app["interview_notes"] = interview_notes
            app["status"] = "interview"
            app["updated_at"] = "2026-04-01"
            return {"success": True, "application": app}
    return {"success": False, "error": "Application not found"}


@app.get("/tracker/stats/{user_id}")
async def get_tracker_stats(user_id: str):
    """获取申请统计"""
    stats = app_tracker.get_statistics(user_id)
    return {"success": True, "stats": stats}


@app.get("/tracker/upcoming/{user_id}")
async def get_upcoming_activities(user_id: str):
    """获取即将到来的活动（面试/待跟进）"""
    apps = app_tracker._applications.get(user_id, [])
    upcoming = []
    
    for app in apps:
        if app.get("interview_date"):
            upcoming.append({
                "type": "interview",
                "application_id": app["id"],
                "job_title": app["job_title"],
                "company": app["company"],
                "date": app["interview_date"],
                "notes": app.get("interview_notes", "")
            })
        if app.get("follow_up_date"):
            upcoming.append({
                "type": "follow_up",
                "application_id": app["id"],
                "job_title": app["job_title"],
                "company": app["company"],
                "date": app["follow_up_date"],
                "notes": ""
            })
    
    upcoming.sort(key=lambda x: x.get("date", ""))
    return {"success": True, "upcoming": upcoming[:10]}


from early_bird import EarlyBirdCollector

# 初始化早期测试收集器
early_bird = EarlyBirdCollector()


# === 早期测试数据收集 API（Beta测试用） ===

# === LinkedIn 职位导入 ===

@app.post("/parse-job-url")
async def parse_job_url_endpoint(url: str = Form(...)):
    """解析 LinkedIn 职位 URL，提取职位信息
    
    用法：前端用户粘贴 LinkedIn 职位链接 → 后端抓取解析 → 返回结构化数据
    支持多种 LinkedIn 职位 URL 格式
    """
    try:
        result = linkedin_importer.parse_linkedin_url(url)
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/fetch-job-from-url")
async def fetch_job_from_url_endpoint(url: str = Form(...)):
    """从URL抓取职位信息（前端调用的端点）
    
    支持 LinkedIn、Jobindex、Jobnet 等职位网站
    返回格式与前端期望的一致
    
    策略：先用 LinkedIn API 抓取 -> 不完整则用 AI 提取 -> 再不完整则提示手动输入
    """
    try:
        result = linkedin_importer.parse_linkedin_url(url)
        
        if result.get("success") and result.get("job"):
            job = result["job"]
            title = job.get("title", "")
            company = job.get("company", "")
            description = job.get("description", "")
            raw_text = job.get("raw_text", "") or description
            
            # 如果 LinkedIn 抓取的数据不完整（缺少职位名或公司），用 AI 补充
            if (not title or not company) and raw_text and AI_AVAILABLE:
                print(f"LinkedIn 抓取数据不完整，尝试 AI 补充提取 (title='{title}', company='{company}')")
                try:
                    # 使用 AI 从 raw_text 中提取完整职位信息
                    extracted = extract_job_from_text(raw_text[:5000])
                    if extracted.get("success"):
                        title = title or extracted.get("title", "")
                        company = company or extracted.get("company", "")
                        if not description and extracted.get("description"):
                            description = extracted.get("description", "")
                        print(f"AI 补充提取成功: title='{title}', company='{company}'")
                except Exception as ai_err:
                    print(f"AI 补充提取失败: {ai_err}")
                    # 继续使用 LinkedIn 返回的部分数据
            
            return {
                "success": True,
                "job": {
                    "success": True,
                    "title": title or "职位名称（请手动填写）",
                    "company": company or "公司名称（请手动填写）",
                    "location": job.get("location", ""),
                    "description": description,
                    "url": url,
                    "source": job.get("source", "LinkedIn"),
                    "raw_text": raw_text
                }
            }
        else:
            error_msg = result.get("error", "无法从此链接抓取职位信息")
            return {
                "success": False,
                "job": {
                    "success": False,
                    "error": error_msg
                },
                "message": f"⚠️ {error_msg}。请尝试在职位页面复制全部内容，粘贴到下方。"
            }
    except Exception as e:
        return {
            "success": False,
            "job": {
                "success": False,
                "error": str(e)
            },
            "message": "⚠️ 抓取出错，请稍后重试或手动粘贴职位信息"
        }


@app.post("/import-linkedin")
async def import_linkedin_endpoint(
    url: str = Form(""),
    job_text: str = Form(""),
):
    """导入 LinkedIn 职位 — 支持两种方式：
    
    1. URL 方式：提供 LinkedIn 职位链接，自动抓取解析
    2. 粘贴方式：用户直接粘贴职位描述文本
    
    至少需要提供 url 或 job_text 之一
    """
    try:
        # 方式1: URL 自动解析
        if url:
            result = linkedin_importer.parse_linkedin_url(url)
            if result.get("success") and result.get("job"):
                job = result["job"]
                return {
                    "success": True,
                    "import_method": "url",
                    "job": job,
                    "message": "✅ 职位信息已成功解析"
                }
            # URL 解析失败，提示使用粘贴方式
            return {
                "success": False,
                "import_method": "url_failed",
                "error": result.get("error", "无法解析此链接"),
                "message": "⚠️ 无法自动解析此 LinkedIn 职位。请在 LinkedIn 职位页面复制全部内容，粘贴到下方。",
                "fallback": True
            }
        
        # 方式2: 手动粘贴解析
        elif job_text:
            result = linkedin_importer.parse_manual_input(job_text)
            if result.get("success") and result.get("job"):
                job = result["job"]
                return {
                    "success": True,
                    "import_method": "paste",
                    "job": job,
                    "message": "✅ 职位信息已从粘贴内容中提取"
                }
            return {
                "success": False,
                "error": result.get("error", "无法解析粘贴内容")
            }
        
        else:
            return {"success": False, "error": "请提供 LinkedIn 职位链接或职位描述文本"}
            
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/linkedin/generate-cover-letter")
async def linkedin_cover_letter_endpoint(
    resume_text: str = Form(...),
    job_title: str = Form(...),
    company: str = Form(""),
    job_description: str = Form(""),
    job_location: str = Form(""),
    language: str = Form("auto"),
):
    """从 LinkedIn 导入的职位生成三语求职信
    
    language 参数：
    - "auto": 自动检测职位描述语言
    - "zh": 中文
    - "en": 英文
    - "da": 丹麦文
    
    与 /generate-cover-letter 的区别：
    - 增强了职位来源识别（LinkedIn）
    - 自动语言检测
    - 更好的 Danish 求职信模板
    """
    try:
        # 自动检测语言
        if language == "auto":
            lang = linkedin_detect_language(job_description) if job_description else detect_language(job_title)
        else:
            lang = language

        job = {
            "title": job_title,
            "company": company,
            "description": job_description,
            "location": job_location,
            "source": "LinkedIn",
            "url": ""
        }

        cover_letter = generate_cover_letter(resume_text, job, lang)

        return {
            "success": True,
            "cover_letter": cover_letter,
            "language": lang,
            "language_name": {"zh": "中文", "en": "English", "da": "Dansk"}.get(lang, "English"),
            "job": {
                "title": job_title,
                "company": company,
                "source": "LinkedIn"
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/linkedin/validate-url")
def validate_linkedin_url(url: str):
    """快速验证 LinkedIn URL 是否有效，无需完整解析"""
    is_valid, result = linkedin_importer.validate_url(url)
    return {
        "is_valid": is_valid,
        "job_id": result if is_valid else None,
        "error": None if is_valid else result
    }


# === Beta 测试系统 ===

@app.post("/beta/submit")
async def submit_beta_form(
    email: str = Form(...),
    name: str = Form(""),
    phone: str = Form(""),
    country: str = Form(""),
    city: str = Form(""),
    resume_text: str = Form(""),
    resume_file_name: str = Form(""),
    job_links: str = Form("[]"),  # JSON字符串
    social_accounts: str = Form("[]"),  # JSON字符串
    notes: str = Form(""),
    source: str = Form("website")
):
    """早期测试表单提交

    用于收集用户数据：
    - 简历文本或文件
    - 已申请/关注的职位链接
    - 社交媒体账号
    - 联系方式

    所有数据用于本地AI处理，帮助优化算法。
    """
    try:
        job_links_list = json.loads(job_links) if job_links else []
        social_list = json.loads(social_accounts) if social_accounts else []

        result = early_bird.submit_form(
            email=email,
            name=name,
            phone=phone,
            country=country,
            city=city,
            resume_text=resume_text,
            resume_file_name=resume_file_name,
            job_links=job_links_list,
            social_accounts=social_list,
            notes=notes,
            source=source
        )

        return result
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/beta/submission/{submission_id}")
async def get_beta_submission(submission_id: str):
    """获取提交详情"""
    submission = early_bird.get_submission(submission_id)
    if submission:
        return {"success": True, "submission": submission}
    return {"success": False, "error": "Submission not found"}


@app.get("/beta/submissions")
async def list_beta_submissions(
    status: str = "all",
    source: str = "all",
    limit: int = 50
):
    """获取提交列表"""
    submissions = early_bird.list_submissions(status, source, limit)
    return {"success": True, "submissions": submissions}


@app.post("/beta/update-status")
async def update_beta_status(
    submission_id: str = Form(...),
    status: str = Form(...),
    notes: str = Form("")
):
    """更新处理状态"""
    success = early_bird.update_status(submission_id, status, notes)
    return {"success": success}


@app.get("/beta/statistics")
async def get_beta_statistics():
    """获取统计数据"""
    stats = early_bird.get_statistics()
    return {"success": True, "statistics": stats}


@app.post("/beta/process")
async def process_beta_submission(
    submission_id: str = Form(...),
    action: str = Form(...),
    result: str = Form("")
):
    """记录处理操作"""
    early_bird.log_processing(submission_id, action, result)
    early_bird.update_status(submission_id, "processed", result)
    return {"success": True}


# ============================================================
# 新增：用户认证、简历管理、申请追踪 API
# ============================================================

from fastapi import Header, HTTPException
from typing import Optional

# 导入认证模块
from auth import (
    register_user, login_user, get_current_user, 
    update_user_profile, change_password, extract_token_from_header
)

# 导入简历导出模块
from resume_exporter import export_user_resume, get_resume_for_export, DOCX_AVAILABLE

# 导入申请追踪模块
from application_tracker import application_service

# 导入数据库和简历模块
from database import (
    create_resume, get_user_resumes, get_primary_resume,
    update_resume, delete_resume, get_resume_by_id,
    create_cover_letter, get_user_cover_letters, update_cover_letter, delete_cover_letter
)


def get_current_user_id(authorization: Optional[str] = Header(None)) -> Optional[str]:
    """从请求头获取当前用户ID"""
    if not authorization:
        return None
    token = extract_token_from_header(authorization)
    if not token:
        return None
    from auth import get_user_from_token
    user = get_user_from_token(token)
    return user["user_id"] if user else None


# === 认证 API ===

@app.post("/auth/register")
async def register_endpoint(
    email: str = Form(...),
    password: str = Form(...),
    name: str = Form(""),
    phone: str = Form(""),
    country: str = Form(""),
    city: str = Form("")
):
    """用户注册"""
    result = register_user(email, password, name, phone, country, city)
    return result


@app.post("/auth/login")
async def login_endpoint(
    email: str = Form(...),
    password: str = Form(...)
):
    """用户登录"""
    result = login_user(email, password)
    return result


@app.get("/auth/me")
async def get_me_endpoint(authorization: Optional[str] = Header(None)):
    """获取当前用户信息"""
    if not authorization:
        return {"success": False, "error": "Authorization header required"}
    
    result = get_current_user(authorization)
    return result


@app.post("/auth/update-profile")
async def update_profile_endpoint(
    authorization: Optional[str] = Header(None),
    name: str = Form(""),
    phone: str = Form(""),
    country: str = Form(""),
    city: str = Form(""),
    preferred_language: str = Form("")
):
    """更新用户资料"""
    user_id = get_current_user_id(authorization)
    if not user_id:
        return {"success": False, "error": "Unauthorized"}
    
    updates = {}
    if name: updates["name"] = name
    if phone: updates["phone"] = phone
    if country: updates["country"] = country
    if city: updates["city"] = city
    if preferred_language: updates["preferred_language"] = preferred_language
    
    return update_user_profile(user_id, **updates)


@app.post("/auth/change-password")
async def change_password_endpoint(
    authorization: Optional[str] = Header(None),
    old_password: str = Form(...),
    new_password: str = Form(...)
):
    """修改密码"""
    user_id = get_current_user_id(authorization)
    if not user_id:
        return {"success": False, "error": "Unauthorized"}
    
    return change_password(user_id, old_password, new_password)


# === 快速注册（保存进度）API ===

@app.post("/session/register")
async def session_register_endpoint(
    session_id: str = Form(...),
    email: str = Form(...),
    password: str = Form(""),
    interested_position: str = Form("")
):
    """
    快速注册：将匿名会话绑定到用户账户
    
    1. 如果邮箱已存在，直接绑定会话并登录
    2. 如果邮箱不存在，创建新用户并绑定
    3. 转移会话中的简历、职位数据到用户账户
    """
    from database import (
        save_session_data, get_all_session_data, bind_session_to_user,
        get_user_by_email, create_user
    )
    from auth import hash_password
    import json
    
    try:
        # 检查邮箱是否已注册
        existing_user = get_user_by_email(email)
        
        if existing_user:
            # 已注册用户：直接绑定会话
            user_id = existing_user["user_id"]
            bind_result = bind_session_to_user(session_id, user_id)
            
            return {
                "success": True,
                "is_new_user": False,
                "user_id": user_id,
                "message": "已绑定到您的账户，之前的进度已保存"
            }
        else:
            # 新用户：创建账户并绑定
            user_id = f"user_{int(datetime.now().timestamp())}"
            password_hash = hash_password(password) if password else hash_password(f"temp_{session_id}")
            
            # 创建用户
            create_user(
                user_id=user_id,
                email=email,
                password_hash=password_hash,
                name="",
                phone="",
                country="",
                city=""
            )
            
            # 绑定会话并转移数据
            bind_session_to_user(session_id, user_id)
            
            return {
                "success": True,
                "is_new_user": True,
                "user_id": user_id,
                "message": "注册成功！您的简历和进度已保存"
            }
            
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/session/save-progress")
async def session_save_progress_endpoint(
    session_id: str = Form(...),
    data_type: str = Form(...),
    data_content: str = Form(...)
):
    """
    保存会话进度（临时存储）
    
    data_type: resume | job_description | cover_letter | analysis_result
    """
    from database import save_session_data
    
    try:
        save_session_data(session_id, data_type, data_content)
        return {"success": True, "message": "进度已保存"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/session/{session_id}/data")
async def session_get_data_endpoint(session_id: str):
    """获取会话保存的数据"""
    from database import get_all_session_data
    
    try:
        data = get_all_session_data(session_id)
        return {"success": True, "data": data}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/session/check-email")
async def check_email_exists_endpoint(email: str = Form(...)):
    """检查邮箱是否已注册"""
    from database import get_user_by_email
    
    user = get_user_by_email(email)
    return {
        "exists": user is not None,
        "user_id": user["user_id"] if user else None
    }


# === 简历管理 API ===

@app.post("/resumes/upload")
async def upload_resume_endpoint(
    authorization: Optional[str] = Header(None),
    resume_text: str = Form(...),
    title: str = Form(""),
    language: str = Form("en"),
    file_name: str = Form(""),
    file_type: str = Form(""),
    is_primary: bool = Form(False)
):
    """上传简历"""
    user_id = get_current_user_id(authorization)
    if not user_id:
        return {"success": False, "error": "Unauthorized"}
    
    try:
        resume = create_resume(
            user_id=user_id,
            content=resume_text,
            title=title or "My Resume",
            language=language,
            file_name=file_name,
            file_type=file_type,
            is_primary=is_primary
        )
        return {
            "success": True,
            "resume": {
                "resume_id": resume["resume_id"],
                "title": resume["title"],
                "language": resume["language"],
                "created_at": resume["created_at"]
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/resumes")
async def list_resumes_endpoint(
    authorization: Optional[str] = Header(None)
):
    """获取用户简历列表"""
    user_id = get_current_user_id(authorization)
    if not user_id:
        return {"success": False, "error": "Unauthorized"}
    
    resumes = get_user_resumes(user_id)
    return {
        "success": True,
        "resumes": [
            {
                "resume_id": r["resume_id"],
                "title": r["title"],
                "language": r["language"],
                "is_primary": bool(r.get("is_primary", 0)),
                "ats_score": r.get("ats_score"),
                "created_at": r["created_at"]
            }
            for r in resumes
        ]
    }


@app.get("/resumes/primary")
async def get_primary_resume_endpoint(
    authorization: Optional[str] = Header(None)
):
    """获取主要简历"""
    user_id = get_current_user_id(authorization)
    if not user_id:
        return {"success": False, "error": "Unauthorized"}
    
    resume = get_primary_resume(user_id)
    if resume:
        return {
            "success": True,
            "resume": {
                "resume_id": resume["resume_id"],
                "title": resume["title"],
                "content": resume["content"],
                "language": resume["language"],
                "is_primary": True,
                "ats_score": resume.get("ats_score"),
                "created_at": resume["created_at"]
            }
        }
    return {"success": False, "error": "No resume found"}


@app.get("/resumes/{resume_id}")
async def get_resume_detail_endpoint(
    resume_id: str,
    authorization: Optional[str] = Header(None)
):
    """获取简历详情"""
    user_id = get_current_user_id(authorization)
    if not user_id:
        return {"success": False, "error": "Unauthorized"}
    
    resume = get_resume_by_id(resume_id)
    if resume and resume["user_id"] == user_id:
        return {
            "success": True,
            "resume": resume
        }
    return {"success": False, "error": "Resume not found"}


@app.post("/resumes/{resume_id}/set-primary")
async def set_primary_resume_endpoint(
    resume_id: str,
    authorization: Optional[str] = Header(None)
):
    """设为主要简历"""
    user_id = get_current_user_id(authorization)
    if not user_id:
        return {"success": False, "error": "Unauthorized"}
    
    resume = get_resume_by_id(resume_id)
    if resume and resume["user_id"] == user_id:
        update_resume(resume_id, is_primary=True)
        return {"success": True, "message": "Primary resume set"}
    return {"success": False, "error": "Resume not found"}


@app.post("/resumes/{resume_id}/delete")
async def delete_resume_endpoint(
    resume_id: str,
    authorization: Optional[str] = Header(None)
):
    """删除简历"""
    user_id = get_current_user_id(authorization)
    if not user_id:
        return {"success": False, "error": "Unauthorized"}
    
    resume = get_resume_by_id(resume_id)
    if resume and resume["user_id"] == user_id:
        delete_resume(resume_id)
        return {"success": True, "message": "Resume deleted"}
    return {"success": False, "error": "Resume not found"}


# === 简历导出 API ===

@app.get("/export-resume")
async def export_resume_endpoint(
    authorization: Optional[str] = Header(None),
    resume_id: str = "",
    language: str = "en"
):
    """导出简历为 Word 文档
    
    参数：
    - resume_id: 简历ID（为空则导出主要简历）
    - language: 导出语言 (en, zh, da, auto)
    """
    user_id = get_current_user_id(authorization)
    if not user_id:
        return {"success": False, "error": "Unauthorized"}
    
    if not DOCX_AVAILABLE:
        return {"success": False, "error": "Word export not available. Please install python-docx."}
    
    try:
        doc_bytes = export_user_resume(user_id, resume_id, language)
        if doc_bytes:
            return StreamingResponse(
                io.BytesIO(doc_bytes),
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={
                    "Content-Disposition": f"attachment; filename=resume_{language}.docx"
                }
            )
        return {"success": False, "error": "Resume not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/export-resume-pdf")
async def export_resume_pdf_endpoint(
    authorization: Optional[str] = Header(None),
    resume_id: str = Form(""),
    language: str = Form("en"),
    polished_content: str = Form(""),
    user_name: str = Form(""),
    user_email: str = Form(""),
    user_phone: str = Form(""),
    user_location: str = Form("")
):
    """导出简历为专业 PDF 文档（使用 reportlab，支持中/英/丹麦语）
    
    参数：
    - resume_id: 简历ID（为空则导出主要简历）
    - language: 导出语言 (en, zh, da)
    - polished_content: 精修后的简历内容（可选，会覆盖数据库内容）
    - user_name/user_email/user_phone/user_location: 用户信息（精修内容时需要）
    """
    user_id = get_current_user_id(authorization)
    if not user_id:
        return {"success": False, "error": "Unauthorized"}
    
    if not PDF_ENGINE_AVAILABLE:
        return {"success": False, "error": "PDF engine not available. Please check dependencies."}
    
    try:
        # 优先使用精修内容
        if polished_content:
            resume_data = {
                "name": user_name or "Resume",
                "content": polished_content,
                "email": user_email,
                "phone": user_phone,
                "location": user_location,
            }
        else:
            # 从数据库获取
            if resume_id:
                resume_data_db = get_resume_by_id(resume_id)
            else:
                resume_data_db = get_primary_resume(user_id)
            
            if not resume_data_db:
                return {"success": False, "error": "Resume not found"}
            
            resume_data = {
                "name": resume_data_db.get("title", "Resume"),
                "content": resume_data_db.get("content", ""),
                "email": resume_data_db.get("email", ""),
                "phone": resume_data_db.get("phone", ""),
                "location": resume_data_db.get("location", ""),
            }
        
        # 生成 PDF
        from pdf_engine import generate_resume_pdf
        pdf_bytes = generate_resume_pdf(resume_data, language)
        
        if not pdf_bytes:
            return {"success": False, "error": "PDF generation failed"}
        
        return StreamingResponse(
            io.BytesIO(pdf_bytes),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=resume_{language}.pdf"
            }
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e)}


# === 求职信管理 API ===

@app.post("/cover-letters/save")
async def save_cover_letter_endpoint(
    authorization: Optional[str] = Header(None),
    company: str = Form(...),
    content: str = Form(...),
    job_title: str = Form(""),
    application_id: str = Form(""),
    language: str = Form("en"),
    is_template: bool = Form(False),
    quality_score: float = Form(0)
):
    """保存求职信"""
    user_id = get_current_user_id(authorization)
    if not user_id:
        return {"success": False, "error": "Unauthorized"}
    
    try:
        cl = create_cover_letter(
            user_id=user_id,
            company=company,
            content=content,
            job_title=job_title,
            application_id=application_id,
            language=language,
            is_template=is_template,
            quality_score=quality_score
        )
        return {
            "success": True,
            "cover_letter": {
                "cover_letter_id": cl["cover_letter_id"],
                "company": cl["company"],
                "language": cl["language"],
                "created_at": cl["created_at"]
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/cover-letters")
async def list_cover_letters_endpoint(
    authorization: Optional[str] = Header(None),
    application_id: str = ""
):
    """获取求职信列表"""
    user_id = get_current_user_id(authorization)
    if not user_id:
        return {"success": False, "error": "Unauthorized"}
    
    letters = get_user_cover_letters(user_id, application_id)
    return {
        "success": True,
        "cover_letters": [
            {
                "cover_letter_id": cl["cover_letter_id"],
                "company": cl["company"],
                "job_title": cl.get("job_title", ""),
                "language": cl["language"],
                "is_template": bool(cl.get("is_template", 0)),
                "quality_score": cl.get("quality_score", 0),
                "created_at": cl["created_at"]
            }
            for cl in letters
        ]
    }


@app.get("/cover-letters/templates")
async def list_templates_endpoint(
    authorization: Optional[str] = Header(None)
):
    """获取求职信模板列表"""
    user_id = get_current_user_id(authorization)
    if not user_id:
        return {"success": False, "error": "Unauthorized"}
    
    templates = get_templates(user_id)
    return {
        "success": True,
        "templates": [
            {
                "cover_letter_id": cl["cover_letter_id"],
                "company": cl["company"],
                "job_title": cl.get("job_title", ""),
                "created_at": cl["created_at"]
            }
            for cl in templates
        ]
    }


@app.get("/cover-letters/{cover_letter_id}")
async def get_cover_letter_detail_endpoint(
    cover_letter_id: str,
    authorization: Optional[str] = Header(None)
):
    """获取求职信详情"""
    user_id = get_current_user_id(authorization)
    if not user_id:
        return {"success": False, "error": "Unauthorized"}
    
    cl = get_cover_letter_by_id(cover_letter_id)
    if cl and cl["user_id"] == user_id:
        return {
            "success": True,
            "cover_letter": cl
        }
    return {"success": False, "error": "Cover letter not found"}


@app.post("/cover-letters/{cover_letter_id}/update")
async def update_cover_letter_endpoint(
    cover_letter_id: str,
    authorization: Optional[str] = Header(None),
    content: str = Form(""),
    language: str = Form(""),
    is_template: bool = Form(None)
):
    """更新求职信"""
    user_id = get_current_user_id(authorization)
    if not user_id:
        return {"success": False, "error": "Unauthorized"}
    
    cl = get_cover_letter_by_id(cover_letter_id)
    if not cl or cl["user_id"] != user_id:
        return {"success": False, "error": "Cover letter not found"}
    
    updates = {}
    if content: updates["content"] = content
    if language: updates["language"] = language
    if is_template is not None: updates["is_template"] = is_template
    
    updated = update_cover_letter(cover_letter_id, **updates)
    return {
        "success": True,
        "cover_letter": updated
    }


@app.post("/cover-letters/{cover_letter_id}/delete")
async def delete_cover_letter_endpoint(
    cover_letter_id: str,
    authorization: Optional[str] = Header(None)
):
    """删除求职信"""
    user_id = get_current_user_id(authorization)
    if not user_id:
        return {"success": False, "error": "Unauthorized"}
    
    success = delete_cover_letter(cover_letter_id, user_id)
    if success:
        return {"success": True, "message": "Cover letter deleted"}
    return {"success": False, "error": "Cover letter not found"}


# === 申请追踪 API ===

@app.post("/applications/add")
async def add_application_endpoint(
    authorization: Optional[str] = Header(None),
    job_title: str = Form(...),
    company: str = Form(...),
    job_id: str = Form(""),
    company_website: str = Form(""),
    job_url: str = Form(""),
    salary_range: str = Form(""),
    location: str = Form(""),
    status: str = Form("new"),
    priority: str = Form("normal"),
    applied_date: str = Form(""),
    deadline: str = Form(""),
    contact_name: str = Form(""),
    contact_email: str = Form(""),
    contact_phone: str = Form(""),
    notes: str = Form(""),
    match_score: float = Form(0),
    resume_id: str = Form(""),
    cover_letter_id: str = Form("")
):
    """添加申请记录"""
    user_id = get_current_user_id(authorization)
    if not user_id:
        return {"success": False, "error": "Unauthorized"}
    
    return application_service.add_application(
        user_id=user_id,
        job_title=job_title,
        company=company,
        job_id=job_id,
        company_website=company_website,
        job_url=job_url,
        salary_range=salary_range,
        location=location,
        status=status,
        priority=priority,
        applied_date=applied_date,
        deadline=deadline,
        contact_name=contact_name,
        contact_email=contact_email,
        contact_phone=contact_phone,
        notes=notes,
        match_score=match_score,
        resume_id=resume_id,
        cover_letter_id=cover_letter_id
    )


@app.get("/applications")
async def list_applications_endpoint(
    authorization: Optional[str] = Header(None),
    status: str = "all",
    page: int = 1,
    page_size: int = 20
):
    """获取申请列表"""
    user_id = get_current_user_id(authorization)
    if not user_id:
        return {"success": False, "error": "Unauthorized"}
    
    return application_service.list_applications(user_id, status, page, page_size)


@app.get("/applications/{application_id}")
async def get_application_endpoint(
    application_id: str,
    authorization: Optional[str] = Header(None)
):
    """获取单个申请详情"""
    user_id = get_current_user_id(authorization)
    if not user_id:
        return {"success": False, "error": "Unauthorized"}
    
    return application_service.get_application(application_id, user_id)


@app.post("/applications/{application_id}/update")
async def update_application_endpoint(
    application_id: str,
    authorization: Optional[str] = Header(None),
    job_title: str = Form(""),
    company: str = Form(""),
    company_website: str = Form(""),
    job_url: str = Form(""),
    salary_range: str = Form(""),
    location: str = Form(""),
    status: str = Form(""),
    priority: str = Form(""),
    applied_date: str = Form(""),
    deadline: str = Form(""),
    contact_name: str = Form(""),
    contact_email: str = Form(""),
    contact_phone: str = Form(""),
    notes: str = Form(""),
    follow_up_date: str = Form("")
):
    """更新申请记录"""
    user_id = get_current_user_id(authorization)
    if not user_id:
        return {"success": False, "error": "Unauthorized"}
    
    updates = {}
    if job_title: updates["job_title"] = job_title
    if company: updates["company"] = company
    if company_website: updates["company_website"] = company_website
    if job_url: updates["job_url"] = job_url
    if salary_range: updates["salary_range"] = salary_range
    if location: updates["location"] = location
    if status: updates["status"] = status
    if priority: updates["priority"] = priority
    if applied_date: updates["applied_date"] = applied_date
    if deadline: updates["deadline"] = deadline
    if contact_name: updates["contact_name"] = contact_name
    if contact_email: updates["contact_email"] = contact_email
    if contact_phone: updates["contact_phone"] = contact_phone
    if notes: updates["notes"] = notes
    if follow_up_date: updates["follow_up_date"] = follow_up_date
    
    return application_service.update_application(application_id, user_id, **updates)


@app.post("/applications/{application_id}/update-status")
async def update_status_endpoint(
    application_id: str,
    authorization: Optional[str] = Header(None),
    new_status: str = Form(...),
    notes: str = Form("")
):
    """更新申请状态"""
    user_id = get_current_user_id(authorization)
    if not user_id:
        return {"success": False, "error": "Unauthorized"}
    
    return application_service.update_status(application_id, user_id, new_status, notes)


@app.post("/applications/{application_id}/add-interview")
async def add_interview_endpoint(
    application_id: str,
    authorization: Optional[str] = Header(None),
    interview_date: str = Form(...),
    interview_notes: str = Form("")
):
    """添加面试信息"""
    user_id = get_current_user_id(authorization)
    if not user_id:
        return {"success": False, "error": "Unauthorized"}
    
    return application_service.add_interview(application_id, user_id, interview_date, interview_notes)


@app.post("/applications/{application_id}/delete")
async def delete_application_endpoint(
    application_id: str,
    authorization: Optional[str] = Header(None)
):
    """删除申请记录"""
    user_id = get_current_user_id(authorization)
    if not user_id:
        return {"success": False, "error": "Unauthorized"}
    
    return application_service.delete_application(application_id, user_id)


@app.get("/applications/stats")
async def get_application_stats_endpoint(
    authorization: Optional[str] = Header(None)
):
    """获取申请统计"""
    user_id = get_current_user_id(authorization)
    if not user_id:
        return {"success": False, "error": "Unauthorized"}
    
    return application_service.get_statistics(user_id)


@app.get("/applications/upcoming")
async def get_upcoming_activities_endpoint(
    authorization: Optional[str] = Header(None)
):
    """获取即将到来的活动"""
    user_id = get_current_user_id(authorization)
    if not user_id:
        return {"success": False, "error": "Unauthorized"}
    
    return application_service.get_upcoming_activities(user_id)


@app.get("/applications/status-options")
async def get_status_options_endpoint(
    language: str = "en"
):
    """获取状态选项列表"""
    return application_service.get_status_options(language)


# ========== 简历精修 API ==========

class PolishRequest(BaseModel):
    resume_text: str
    language: str = "auto"

class PolishApplyRequest(BaseModel):
    original_text: str
    suggestions: List[Dict]

class DiscoverSkillsRequest(BaseModel):
    document_text: str
    resume_text: str = ""
    document_type: str = "document"

def generate_polish_suggestions(text: str, lang: str = 'en') -> List[Dict]:
    """使用 AI 生成逐条精修建议（升级版：分队优化算法）"""
    if not AI_AVAILABLE:
        return generate_polish_fallback(text, lang)

    # 升级版提示词模板（应用分队算法优化成果）
    prompts_by_lang = {
        'zh': """你是一位拥有20年HR高管经验的顶级职业顾问。请深度分析这份简历，提供专业精修建议。

【核心要求 - 必须严格执行】
你必须逐一检查简历中的每一句话，找出**所有**需要改进的地方。
**绝对不能遗漏任何弱句！** 如果简历有10个弱句，就返回10条建议。

【必须标记为需要改进的句子类型】
1. **弱动词句子**：包含"负责"、"参与"、"协助"、"做了"、"完成了"、"参与"、"支持"等被动词
2. **缺乏量化**：没有数字、数据、百分比的成就描述
3. **笼统描述**：可以更具体却没有具体化的内容
4. **重复内容**：与前后句子意思重复的表达

【精修原则】
- 禁止使用：负责、参与、协助、做了、完成（弱动词）
- 必须包含：量化数据、具体成果、独特价值
- 北欧职场适配：强调协作、平等、成果导向的表达方式

【输出格式】
每条建议必须包含：
- original: 简历原文（精确匹配，10-50字）
- suggested: 精修版本（保持原意但更专业，10-60字）
- reason: 修改原因（50-100字），必须说明：
  * 原句的问题（具体哪里不够好）
  * 新版本的改进（如何更好）
  * 对求职的价值（为什么招聘方会注意到）
- type: 类型（weak_verb/quantification/differentiation/story/format）
- priority: 优先级（high/medium/low）

【示例】
简历原文: "负责ERP系统实施"
返回建议:
{
  "original": "负责ERP系统实施",
  "suggested": "主导ERP系统实施，3个月内完成200+用户上线",
  "reason": "原句'负责'过于被动，只说明参与了工作。新句'主导'体现领导力和项目控制能力，'3个月'和'200+用户'提供量化证据，让招聘方直观看到你的交付能力和影响范围。",
  "type": "weak_verb",
  "priority": "high"
}

简历内容：
{text[:4000]}

返回JSON数组。只返回JSON，不要任何其他文字。""",
        'en': """You are a top career consultant with 20 years of HR executive experience. Provide professional resume improvement suggestions.

【Core Requirement - MUST FOLLOW STRICTLY】
Check EVERY sentence in the resume. Find ALL weak sentences that need improvement.
**DO NOT skip any weak sentences!** If the resume has 10 weak sentences, return 10 suggestions.

【Must Flag These Sentence Types】
1. **Weak Verb Sentences**: Contains "responsible for", "participated in", "assisted", "helped with", "worked on", "supported", "helped"
2. **Missing Quantification**: Achievements without numbers, percentages, or concrete metrics
3. **Vague Descriptions**: Content that could be more specific but isn't
4. **Redundant Content**: Repetitive expressions

【Improvement Principles】
- FORBIDDEN: responsible for, participated in, assisted, helped with (weak verbs)
- MUST INCLUDE: quantifiable data, concrete results, unique value
- Nordic Workplace Fit: Emphasize collaboration, equality, and result-oriented expression

【Output Format】
Each suggestion must include:
- original: exact text from resume (10-50 characters)
- suggested: polished version keeping original meaning (10-60 characters)
- reason: explanation (50-100 characters) covering:
  * Problem with original (specific weakness)
  * Improvement in new version (how it's better)
  * Job search value (why recruiters will notice)
- type: type (weak_verb/quantification/differentiation/story/format)
- priority: priority (high/medium/low)

【Example】
Resume text: "Responsible for ERP implementation"
Return:
{
  "original": "Responsible for ERP implementation",
  "suggested": "Led ERP implementation, delivered to 200+ users in 3 months",
  "reason": "'Responsible for' is passive and vague. 'Led' shows leadership and project control. '200+ users in 3 months' provides quantifiable evidence of delivery capability and impact scope.",
  "type": "weak_verb",
  "priority": "high"
}

Resume:
{text[:4000]}

IMPORTANT: Return suggestions for EVERY weak sentence found. Return ONLY JSON array, nothing else.""",
        'da': """Du er en top karrierekonsulent med 20 års erfaring som HR-direktør. Giv professionelle forbedringsforslag til CV'et.

【Kernekrav - SKAL FØLGES STRENGT】
Gennemgå HVER sætning i CV'et. Find ALLE svage sætninger, der skal forbedres.
**Gå IKKE udenom nogen svage sætninger!** Hvis CV'et har 10 svage sætninger, returner 10 forslag.

【Skal Markere Disse Sætningstyper】
1. **Svage Verbum-sætninger**: Indeholder "ansvarlig for", "deltog i", "assisterede", "hjælpe med", "arbejdede på", "understøttede"
2. **Manglende Kvantificering**: Præstationer uden tal, procenter eller konkrete målinger
3. **Vage Beskrivelser**: Indhold der kunne være mere specifikt men ikke er
4. **Gentaget Indhold**: Repetitive udtryk

【Forbedringsprincipper】
- FORBUDT: ansvarlig for, deltog i, assisterede (svage verber)
- SKAL INDEHOLDE: kvantificerbare data, konkrete resultater
- Nordisk arbejdspladstilpasning: Fremhæv samarbejde, lighed og resultatorientering

【Output-format】
Hvert forslag skal indeholde:
- original: præcis tekst fra CV (10-50 tegn)
- suggested: forbedret version (10-60 tegn)
- reason: forklaring (50-100 tegn)
- type: type (weak_verb/quantification/differentiation/story/format)
- priority: prioritet (high/medium/low)

【Eksempel】
CV-tekst: "Ansvarlig for ERP-implementering"
Returner:
{
  "original": "Ansvarlig for ERP-implementering",
  "suggested": "Ledede ERP-implementering, leverede til 200+ brugere på 3 måneder",
  "reason": "'Ansvarlig for' er passivt. 'Ledede' viser lederskab. '200+ brugere på 3 måneder' giver kvantificerbare beviser.",
  "type": "weak_verb",
  "priority": "high"
}

CV:
{text[:4000]}

VIGTIGT: Returner forslag til ALLE svage sætninger. Returner KUN JSON-array.""",
    }

    try:
        prompt = prompts_by_lang.get(lang, prompts_by_lang['en'])

        response = ai_client.chat.completions.create(
            model=AI_MODEL_RESUME or AI_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional resume writing expert. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,  # 降低随机性
            max_tokens=6000,  # 支持最多30条建议输出
            timeout=60
        )

        content = response.choices[0].message.content.strip()
        if content.startswith('```'):
            content = content.split('```')[1]
            if content.startswith('json'):
                content = content[4:]
        suggestions = json.loads(content)

        for i, s in enumerate(suggestions):
            if 'id' not in s:
                s['id'] = i + 1

        # 限制最多30条建议
        MAX_SUGGESTIONS = 30
        return suggestions[:MAX_SUGGESTIONS]

    except Exception as e:
        print(f"Polish suggestions failed: {e}, using fallback")
        return generate_polish_fallback(text, lang)

def generate_polish_fallback(text: str, lang: str = 'en') -> List[Dict]:
    """本地规则生成精修建议（无需AI）- 提供详细解释"""
    # 弱动词映射及详细解释
    weak_verb_details = {
        'zh': [
            {
                'weak': '负责',
                'strong': '主导',
                'reason': '"负责"只是说明你参与了这项工作，但没有体现你的主动性和成果。"主导"则强调你是项目的推动者和决策者，展现了领导力和责任感，让招聘方看到你能独立承担重要任务。'
            },
            {
                'weak': '参与',
                'strong': '推动',
                'reason': '"参与"暗示你只是团队中的一员，贡献度不明确。"推动"则表明你是项目的核心驱动力，能够主动解决问题、协调资源，体现更强的执行力和影响力。'
            },
            {
                'weak': '协助',
                'strong': '协同',
                'reason': '"协助"给人一种配角的感觉，似乎只是打下手。"协同"则强调你与团队平等合作、共同完成任务的能力，体现跨部门沟通和协作的专业素养。'
            },
            {
                'weak': '做了',
                'strong': '实现',
                'reason': '"做了"过于口语化和模糊，缺乏专业感。"实现"则带有目标达成的意味，暗示你不仅完成了任务，还取得了可衡量的成果，更符合职场专业表达。'
            }
        ],
        'en': [
            {
                'weak': 'responsible for',
                'strong': 'led',
                'reason': '"Responsible for" merely states you were involved, but shows no initiative or results. "Led" demonstrates you were the driver and decision-maker, showcasing leadership and ownership. It transforms you from a participant into a leader.'
            },
            {
                'weak': 'worked on',
                'strong': 'delivered',
                'reason': '"Worked on" is vague about your contribution and impact. "Delivered" implies you completed the project successfully and achieved tangible results. It shows you finish what you start and create value.'
            },
            {
                'weak': 'helped with',
                'strong': 'collaborated on',
                'reason': '"Helped with" suggests you played a minor supporting role. "Collaborated on" positions you as an equal partner who contributed meaningfully to the team effort, highlighting your teamwork and communication skills.'
            }
        ],
        'da': [
            {
                'weak': 'ansvarlig for',
                'strong': 'ledede',
                'reason': '"Ansvarlig for" angiver blot deltagelse, men viser ikke initiativ eller resultater. "Ledede" demonstrerer, at du var drivkraften og beslutningstageren, og viser lederskab og ejerskab.'
            },
            {
                'weak': 'arbejdede på',
                'strong': 'leverede',
                'reason': '"Arbejdede på" er vag om dit bidrag. "Leverede" indebærer, at du gennemførte projektet succesfuldt med håndgribelige resultater. Det viser, at du afslutter det, du starter.'
            }
        ]
    }

    suggestions = []
    text_lower = text.lower()
    verb_details = weak_verb_details.get(lang, weak_verb_details['en'])

    for detail in verb_details:
        weak = detail['weak']
        strong = detail['strong']
        reason = detail['reason']
        
        if weak.lower() in text_lower:
            for line in text.split('\n'):
                if weak.lower() in line.lower():
                    improved = line.lower().replace(weak.lower(), strong)
                    improved = improved[0].upper() + improved[1:] if improved else improved
                    suggestions.append({
                        'id': len(suggestions) + 1,
                        'original': line.strip(),
                        'suggested': improved,
                        'reason': reason,
                        'type': 'weak_verb',
                        'priority': 'medium'
                    })
                    break

    # 如果没有找到弱动词，添加量化建议
    if not suggestions:
        quantify_reasons = {
            'zh': '你的简历缺少具体的数字和成果量化。招聘方希望看到"提升了30%"而不是"提升了业绩"。建议添加：完成的项目数量、节省的成本金额、提升的效率百分比、服务的客户数量等具体指标。',
            'en': 'Your resume lacks specific numbers and quantified achievements. Recruiters want to see "increased by 30%" not just "improved performance". Consider adding: number of projects completed, cost savings amount, efficiency improvement percentage, number of clients served.',
            'da': 'Dit CV mangler specifikke tal og kvantificerede resultater. Rekrutterere vil se "øget med 30%" ikke bare "forbedret præstation". Overvej at tilføje: antal projekter gennemført, omkostningsbesparelser, effektivitetsforbedring.'
        }
        suggestions.append({
            'id': 1,
            'original': text[:100] + '...' if len(text) > 100 else text,
            'suggested': text[:100] + '...' if len(text) > 100 else text,
            'reason': quantify_reasons.get(lang, quantify_reasons['en']),
            'type': 'missing_quantify',
            'priority': 'medium'
        })

    return suggestions

def clean_text_for_pdf(text: str) -> str:
    """清理文本中的问题字符，确保PDF渲染正常"""
    if not text:
        return text
    # Unicode NFC规范化
    text = unicodedata.normalize('NFC', text)
    # 替换常见的特殊Unicode字符为标准ASCII等价物
    replacements = {
        '\u2018': "'",  # 左单引号
        '\u2019': "'",  # 右单引号
        '\u201c': '"',  # 左双引号
        '\u201d': '"',  # 右双引号
        '\u2013': '-',  # en dash
        '\u2014': '-',  # em dash
        '\u00a0': ' ',  # 不间断空格
        '\u3000': ' ',  # 全角空格
        '\u200b': '',   # 零宽空格
        '\ufeff': '',   # BOM
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    # 移除所有控制字符（除换行和Tab外）
    text = ''.join(c for c in text if unicodedata.category(c) not in ['Cc'] or c in ['\n', '\t'])
    return text

def apply_polish_suggestions(original_text: str, accepted_suggestions: List[Dict]) -> str:
    """应用用户接受的精修建议"""
    result = original_text
    for suggestion in sorted(accepted_suggestions, key=lambda x: result.rfind(x['original']), reverse=True):
        if suggestion.get('accepted', True):
            original = suggestion['original']
            suggested = suggestion['suggested']
            if original in result:
                result = result.replace(original, suggested, 1)
    
    # 清理文本确保PDF渲染正常
    return clean_text_for_pdf(result)

def discover_skills_from_document(doc_text: str, resume_text: str = "", doc_type: str = "document") -> List[Dict]:
    """从文档中发现隐藏的能力和项目经验"""
    if not AI_AVAILABLE:
        return []

    try:
        prompt = f"""You are a career coach expert. Analyze the provided document and compare with the resume to discover skills and experiences that are NOT mentioned in the resume but are evident in the document.

Document content:
{doc_text[:3000]}

Existing resume:
{resume_text[:2000] if resume_text else 'No resume provided'}

Return a JSON array of discovered skills/experiences:
[
  {{
    "skill": "Skill or experience name",
    "evidence": "Specific evidence from the document",
    "confidence": 85
  }}
]

Return ONLY JSON array with 2-5 items. If no new skills found, return empty array."""

        response = ai_client.chat.completions.create(
            model=AI_MODEL_RESUME or AI_MODEL,
            messages=[
                {"role": "system", "content": "You are a professional career coach. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=1000,
            timeout=20
        )

        content = response.choices[0].message.content.strip()
        if content.startswith('```'):
            content = content.split('```')[1]
            if content.startswith('json'):
                content = content[4:]
        return json.loads(content)

    except Exception as e:
        print(f"Discover skills failed: {e}")
        return []

@app.post("/api/resume/polish")
async def polish_resume(request: PolishRequest):
    """生成逐条精修建议"""
    try:
        if request.language == "auto":
            lang = detect_language(request.resume_text)
        else:
            lang = request.language

        suggestions = generate_polish_suggestions(request.resume_text, lang)

        return {
            "success": True,
            "total": len(suggestions),
            "suggestions": suggestions,
            "language": lang,
            "language_name": {"zh": "中文", "en": "English", "da": "Dansk"}.get(lang, "English")
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/resume/apply-polish")
async def apply_polish(request: PolishApplyRequest):
    """应用用户选择的精修建议"""
    try:
        accepted = [s for s in request.suggestions if s.get('accepted', True)]
        polished_text = apply_polish_suggestions(request.original_text, accepted)

        return {
            "success": True,
            "accepted_count": len(accepted),
            "total_count": len(request.suggestions),
            "polished_resume": polished_text
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/api/resume/discover-skills")
async def discover_skills(request: DiscoverSkillsRequest):
    """从文档中发现隐藏能力"""
    try:
        discovered = discover_skills_from_document(
            request.document_text,
            request.resume_text,
            request.document_type
        )

        return {
            "success": True,
            "discovered_skills": discovered,
            "count": len(discovered)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ========== 简历语种转换 API ==========

class TranslateResumeRequest(BaseModel):
    resume_text: str
    source_lang: str = "auto"  # 源语言: zh, en, da, auto
    target_lang: str  # 目标语言: zh, en, da

def translate_resume_with_ai(resume_text: str, source_lang: str, target_lang: str) -> str:
    """使用 AI 翻译简历到目标语言"""
    if not AI_AVAILABLE:
        return None
    
    lang_names = {
        'zh': '中文',
        'en': 'English',
        'da': 'Dansk (Danish)'
    }
    
    source_name = lang_names.get(source_lang, source_lang)
    target_name = lang_names.get(target_lang, target_lang)
    
    prompt = f"""You are a professional resume translator. Translate the following resume from {source_name} to {target_name}.

Requirements:
1. Maintain professional resume format and structure
2. Adapt cultural conventions for {target_name} resumes
3. Keep all dates, numbers, and factual information accurate
4. Translate company names only if they have common {target_name} equivalents
5. Maintain professional tone appropriate for job applications

Resume to translate:
{resume_text[:4000]}

Return ONLY the translated resume text, nothing else."""

    try:
        response = ai_client.chat.completions.create(
            model=AI_MODEL_RESUME or AI_MODEL,
            messages=[
                {"role": "system", "content": f"You are a professional resume translator specializing in {source_name} to {target_name} translation."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=3000,
            timeout=60
        )
        
        content = response.choices[0].message.content.strip()
        # 清理文本确保PDF渲染正常
        return clean_text_for_pdf(content) if content else content
    except Exception as e:
        print(f"Resume translation failed: {e}")
        return None

@app.post("/api/resume/translate")
async def translate_resume_endpoint(request: TranslateResumeRequest):
    """一键转换简历语种"""
    try:
        # 自动检测源语言
        if request.source_lang == "auto":
            source_lang = detect_language(request.resume_text)
        else:
            source_lang = request.source_lang
        
        # 如果源语言和目标语言相同，直接返回
        if source_lang == request.target_lang:
            return {
                "success": True,
                "translated_resume": request.resume_text,
                "source_lang": source_lang,
                "target_lang": request.target_lang,
                "message": "源语言和目标语言相同，无需翻译"
            }
        
        # 使用 AI 翻译
        if AI_AVAILABLE:
            translated = translate_resume_with_ai(
                request.resume_text,
                source_lang,
                request.target_lang
            )
            
            if translated:
                return {
                    "success": True,
                    "translated_resume": translated,
                    "source_lang": source_lang,
                    "target_lang": request.target_lang,
                    "source_lang_name": {"zh": "中文", "en": "English", "da": "Dansk"}.get(source_lang, source_lang),
                    "target_lang_name": {"zh": "中文", "en": "English", "da": "Dansk"}.get(request.target_lang, request.target_lang)
                }
        
        # 如果 AI 不可用或翻译失败，返回错误
        return {
            "success": False,
            "error": "翻译服务暂时不可用，请稍后重试",
            "source_lang": source_lang,
            "target_lang": request.target_lang
        }
        
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.post("/upload-document")
async def upload_document(file: UploadFile = File(...)):
    """上传文档并解析内容"""
    try:
        content = await file.read()
        filename_lower = file.filename.lower()

        text = ""
        if filename_lower.endswith('.txt'):
            for encoding in ['utf-8', 'utf-16', 'latin-1', 'gb18030']:
                try:
                    text = content.decode(encoding)
                    break
                except:
                    continue
        elif filename_lower.endswith('.pdf'):
            try:
                import pdfplumber
                with pdfplumber.open(io.BytesIO(content)) as pdf:
                    for page in pdf.pages:
                        t = page.extract_text()
                        if t:
                            text += t + "\n"
            except:
                pass
        elif filename_lower.endswith('.docx'):
            try:
                import docx
                document = docx.Document(io.BytesIO(content))
                for para in document.paragraphs:
                    if para.text.strip():
                        text += para.text + "\n"
            except:
                pass
        elif filename_lower.endswith('.html') or filename_lower.endswith('.htm'):
            try:
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(content.decode('utf-8', errors='ignore'), 'html.parser')
                # 移除脚本和样式
                for script in soup(["script", "style"]):
                    script.decompose()
                # 获取纯文本
                text = soup.get_text(separator=' ', strip=True)
            except Exception as e:
                text = content.decode('utf-8', errors='ignore')
        elif filename_lower.endswith('.eml'):
            try:
                from bs4 import BeautifulSoup
                msg_content = content.decode('utf-8', errors='ignore')
                soup = BeautifulSoup(msg_content, 'html.parser')
                # 获取正文
                text = soup.get_text(separator=' ', strip=True)
            except Exception as e:
                text = content.decode('utf-8', errors='ignore')

        return {
            "success": True,
            "filename": file.filename,
            "text": text[:5000],
            "detected_language": detect_language(text)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============ Beta 测试 API ============
from early_bird import collector

class BetaSubmissionRequest(BaseModel):
    email: str
    name: str = ""
    phone: str = ""
    country: str = ""
    city: str = ""
    resume_text: str = ""
    resume_file_name: str = ""
    job_links: List[Dict] = []
    social_accounts: List[Dict] = []
    notes: str = ""
    source: str = "website"

@app.post("/beta/submit")
async def beta_submit(request: BetaSubmissionRequest):
    """Beta 测试用户提交"""
    try:
        result = collector.submit_form(
            email=request.email,
            name=request.name,
            phone=request.phone,
            country=request.country,
            city=request.city,
            resume_text=request.resume_text,
            resume_file_name=request.resume_file_name,
            job_links=request.job_links,
            social_accounts=request.social_accounts,
            notes=request.notes,
            source=request.source
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/beta/submissions")
async def beta_submissions(status: str = "all", source: str = "all", limit: int = 50):
    """获取 Beta 测试提交列表（管理用）"""
    try:
        submissions = collector.list_submissions(status=status, source=source, limit=limit)
        return {"success": True, "submissions": submissions, "count": len(submissions)}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/beta/statistics")
async def beta_statistics():
    """获取 Beta 测试统计数据"""
    try:
        stats = collector.get_statistics()
        return {"success": True, "statistics": stats}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/beta/submission/{submission_id}")
async def beta_submission_detail(submission_id: str):
    """获取单个提交详情"""
    try:
        submission = collector.get_submission(submission_id)
        if submission:
            return {"success": True, "submission": submission}
        else:
            return {"success": False, "error": "Submission not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.post("/beta/process/{submission_id}")
async def beta_process_submission(submission_id: str, status: str = "processed", notes: str = ""):
    """更新提交处理状态"""
    try:
        success = collector.update_status(submission_id, status, notes)
        if success:
            collector.log_processing(submission_id, f"status_changed_to_{status}", notes)
            return {"success": True, "message": f"Submission {submission_id} updated to {status}"}
        else:
            return {"success": False, "error": "Submission not found"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============ 静态文件服务 ============
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

# 获取当前文件所在目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

@app.get("/")
async def root():
    """API 根路径 - 返回 API 信息"""
    return {
        "service": "JobMatchAI API",
        "version": "2.0.0",
        "endpoints": {
            "health": "/health",
            "frontend": "/app",
            "analyze": "/analyze",
            "jobs_search": "/jobs/search",
            "cover_letter": "/cover-letter"
        }
    }

@app.get("/app")
async def app_page():
    """前端页面 - 语言选择"""
    return FileResponse(os.path.join(FRONTEND_DIR, "index.html"))

@app.get("/app-en")
async def app_en_page():
    """前端页面 - 英文版"""
    return FileResponse(os.path.join(FRONTEND_DIR, "index-en.html"))

@app.get("/app-zh")
async def app_zh_page():
    """前端页面 - 中文版"""
    return FileResponse(os.path.join(FRONTEND_DIR, "index-zh.html"))

@app.get("/beta.html")
async def beta_page():
    """Beta 测试页面"""
    return FileResponse(os.path.join(FRONTEND_DIR, "beta.html"))

@app.get("/admin")
async def admin_page():
    """管理后台页面"""
    admin_path = os.path.join(BASE_DIR, "admin.html")
    if os.path.exists(admin_path):
        return FileResponse(admin_path)
    return {"error": "Admin page not found"}

@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "version": "2.0.0", "ai_available": AI_AVAILABLE}

# 模板文件路由
@app.get("/static/templates/{filename}")
async def serve_template(filename: str):
    """服务模板JS文件"""
    file_path = os.path.join(FRONTEND_DIR, "templates", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/javascript")
    return {"detail": "File not found"}

# 通用静态文件路由
@app.get("/static/{filepath:path}")
async def serve_static(filepath: str):
    """服务其他静态文件"""
    file_path = os.path.join(FRONTEND_DIR, filepath)
    if os.path.exists(file_path):
        return FileResponse(file_path)
    return {"detail": "File not found"}


# === 启动 ===
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
