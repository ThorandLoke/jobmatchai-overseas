"""
简历模版服务 - 提供模版预览、下载功能

支持模版：
1. classic - 专业经典型（适合金融、咨询）
2. modern - 现代简约型（适合IT、科技）
3. creative - 创意活力型（适合市场营销）

Copyright © 2026 JobMatchAI. All rights reserved.
"""

import os
import re
from typing import Dict, Any, List, Optional

# 模版目录
TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "frontend", "templates")

# 模版定义
TEMPLATES = {
    "classic": {
        "id": "classic",
        "name_zh": "专业经典型",
        "name_en": "Professional Classic",
        "name_da": "Professionel Klassisk",
        "description_zh": "深蓝色经典风格，适合金融、咨询、管理等传统行业",
        "description_en": "Deep blue classic style, ideal for finance, consulting, and management roles",
        "description_da": "Klassisk dybblå stil, ideel til finans, rådgivning og ledelse",
        "file": "resume-classic.html",
        "preview_color": "#1a365d",
        "tags_zh": ["金融", "咨询", "管理", "传统行业"],
        "tags_en": ["Finance", "Consulting", "Management", "Traditional"],
        "tags_da": ["Finans", "Rådgivning", "Ledelse", "Traditionel"]
    },
    "modern": {
        "id": "modern",
        "name_zh": "现代简约型",
        "name_en": "Modern Minimal",
        "name_da": "Moderne Minimalistisk",
        "description_zh": "左侧彩色边栏，适合IT、科技、互联网等行业",
        "description_en": "Left-side colorful bar, ideal for IT, tech, and internet companies",
        "description_da": "Farverig bar i venstre side, ideel til IT, teknologi og internetvirksomheder",
        "file": "resume-modern.html",
        "preview_color": "#667eea",
        "tags_zh": ["IT", "科技", "互联网", "现代企业"],
        "tags_en": ["IT", "Tech", "Internet", "Modern"],
        "tags_da": ["IT", "Teknologi", "Internet", "Moderne"]
    },
    "creative": {
        "id": "creative",
        "name_zh": "创意活力型",
        "name_en": "Creative Tech",
        "name_da": "Kreativ Tech",
        "description_zh": "赛博朋克风格，适合创意、市场营销、创业公司",
        "description_en": "Cyberpunk style, ideal for creative, marketing, and startup roles",
        "description_da": "Cyberpunk stil, ideel til kreative, marketing og startup roller",
        "file": "resume-creative.html",
        "preview_color": "#764ba2",
        "tags_zh": ["创意", "营销", "创业", "年轻活力"],
        "tags_en": ["Creative", "Marketing", "Startup", "Dynamic"],
        "tags_da": ["Kreativ", "Marketing", "Startup", "Dynamisk"]
    }
}

# 外部资源链接（导流用）
EXTERNAL_LINKS = {
    "canva": {
        "name_zh": "Canva",
        "name_en": "Canva",
        "url": "https://www.canva.com/resumes/templates/",
        "description_zh": "免费模版 + 在线编辑",
        "description_en": "Free templates + Online editor"
    },
    "zety": {
        "name_zh": "Zety",
        "name_en": "Zety",
        "url": "https://zety.com/",
        "description_zh": "750+ 职业简历模版",
        "description_en": "750+ professional resume templates"
    },
    "resumegenius": {
        "name_zh": "ResumeGenius",
        "name_en": "ResumeGenius",
        "url": "https://resumegenius.com/resume-templates",
        "description_zh": "550+ 免费模版下载",
        "description_en": "550+ Free resume templates"
    }
}


def get_template_list(language: str = "en") -> List[Dict[str, Any]]:
    """获取所有模版列表"""
    result = []
    for template_id, template in TEMPLATES.items():
        result.append({
            "id": template_id,
            "name": template.get(f"name_{language}", template["name_en"]),
            "description": template.get(f"description_{language}", template["description_en"]),
            "preview_color": template["preview_color"],
            "tags": template.get(f"tags_{language}", template["tags_en"]),
            "preview_url": f"/templates/{template['file']}"
        })
    return result


def get_template_by_id(template_id: str, language: str = "en") -> Optional[Dict[str, Any]]:
    """获取指定模版"""
    template = TEMPLATES.get(template_id)
    if not template:
        return None
    
    return {
        "id": template_id,
        "name": template.get(f"name_{language}", template["name_en"]),
        "description": template.get(f"description_{language}", template["description_en"]),
        "preview_color": template["preview_color"],
        "tags": template.get(f"tags_{language}", template["tags_en"]),
        "file_path": os.path.join(TEMPLATE_DIR, template["file"]),
        "download_ready": True
    }


def get_template_html(template_id: str, resume_data: Dict[str, Any]) -> Optional[str]:
    """根据简历数据渲染模版HTML"""
    template = TEMPLATES.get(template_id)
    if not template:
        return None
    
    template_path = os.path.join(TEMPLATE_DIR, template["file"])
    if not os.path.exists(template_path):
        return None
    
    with open(template_path, "r", encoding="utf-8") as f:
        html = f.read()
    
    # 简单的模版变量替换
    replacements = {
        "{{NAME}}": resume_data.get("name", ""),
        "{{TITLE}}": resume_data.get("title", ""),
        "{{EMAIL}}": resume_data.get("email", ""),
        "{{PHONE}}": resume_data.get("phone", ""),
        "{{LOCATION}}": resume_data.get("location", ""),
    }
    
    for key, value in replacements.items():
        html = html.replace(key, str(value))
    
    # 处理 LinkedIn
    if resume_data.get("linkedin"):
        html = html.replace("{{#LINKEDIN}}", "").replace("{{/LINKEDIN}}", "")
        html = html.replace("{{LINKEDIN}}", resume_data["linkedin"])
    else:
        html = re.sub(r"\{\{#LINKEDIN\}\}.*?\{\{/LINKEDIN\}\}", "", html, flags=re.DOTALL)
        html = html.replace("{{LINKEDIN}}", "")
    
    # 处理 Summary
    if resume_data.get("summary"):
        html = html.replace("{{#SUMMARY}}", "").replace("{{/SUMMARY}}", "")
        html = html.replace("{{SUMMARY}}", resume_data["summary"])
    else:
        html = re.sub(r"\{\{#SUMMARY\}\}.*?\{\{/SUMMARY\}\}", "", html, flags=re.DOTALL)
        html = html.replace("{{SUMMARY}}", "")
    
    # 处理 Education
    if resume_data.get("education"):
        html = html.replace("{{#EDUCATION}}", "").replace("{{/EDUCATION}}", "")
        edu = resume_data["education"][0] if resume_data["education"] else {}
        html = html.replace("{{DEGREE}}", edu.get("degree", ""))
        html = html.replace("{{SCHOOL}}", edu.get("school", ""))
        html = html.replace("{{DATE_RANGE}}", edu.get("date_range", ""))
        html = html.replace("{{GPA}}", edu.get("gpa", ""))
    else:
        html = re.sub(r"\{\{#EDUCATION\}\}.*?\{\{/EDUCATION\}\}", "", html, flags=re.DOTALL)
    
    # 处理 Languages
    if resume_data.get("languages"):
        languages_str = " · ".join(resume_data["languages"])
        html = html.replace("{{#LANGUAGES}}", "").replace("{{/LANGUAGES}}", "")
        html = html.replace("{{LANGUAGES}}", languages_str)
    else:
        html = re.sub(r"\{\{#LANGUAGES\}\}.*?\{\{/LANGUAGES\}\}", "", html, flags=re.DOTALL)
        html = html.replace("{{LANGUAGES}}", "")
    
    # 处理 Experience
    if resume_data.get("experience"):
        html = html.replace("{{#EXPERIENCE}}", "").replace("{{/EXPERIENCE}}", "")
        exp = resume_data["experience"][0] if resume_data["experience"] else {}
        html = html.replace("{{JOB_TITLE}}", exp.get("title", ""))
        html = html.replace("{{COMPANY}}", exp.get("company", ""))
        html = html.replace("{{DATE_RANGE}}", exp.get("date_range", ""))
        # 处理描述
        if exp.get("description"):
            desc_html = "".join([f"<li>{desc}</li>" for desc in exp["description"]])
            html = html.replace("{{#DESCRIPTION}}<li>{{.}}</li>{{/DESCRIPTION}}", desc_html)
    else:
        html = re.sub(r"\{\{#EXPERIENCE\}\}.*?\{\{/EXPERIENCE\}\}", "", html, flags=re.DOTALL)
    
    return html


def get_external_links(language: str = "en") -> List[Dict[str, Any]]:
    """获取外部模版资源链接"""
    result = []
    for key, link in EXTERNAL_LINKS.items():
        result.append({
            "name": link.get(f"name_{language}", link["name_zh"]),
            "url": link["url"],
            "description": link.get(f"description_{language}", link["description_en"])
        })
    return result


# 推荐的简历关键词（用于ATS优化）
ATS_KEYWORDS = {
    "leadership": ["led", "管理", "负责", "主管", "团队", "supervised", "managed", "led"],
    "achievements": ["提高", "增加", "减少", "优化", "achieved", "increased", "improved", "reduced"],
    "technical": ["开发", "实现", "部署", "设计", "developed", "implemented", "deployed", "designed"],
    "collaboration": ["协作", "合作", "协调", "collaborated", "coordinated", "worked with"],
    "results": ["结果", "成果", "成效", "result", "outcome", "impact", "delivered"]
}


def suggest_ats_keywords(job_title: str, industry: str = "") -> List[str]:
    """根据职位和行业推荐ATS关键词"""
    suggestions = []
    
    # 通用关键词
    common = ["项目管理", "跨团队协作", "数据分析", "解决方案", 
              "project management", "cross-functional", "data analysis", "solution"]
    suggestions.extend(common[:4])
    
    # IT相关
    if any(k in job_title.lower() for k in ["developer", "engineer", "technical", "it"]):
        suggestions.extend(["敏捷开发", "API", "DevOps", "Agile", "API", "DevOps"])
    
    # ERP相关
    if any(k in job_title.lower() for k in ["erp", "sap", "netsuite", "dynamics"]):
        suggestions.extend(["ERP实施", "业务流程优化", "系统集成", 
                           "ERP implementation", "BPR", "system integration"])
    
    # 管理咨询
    if any(k in job_title.lower() for k in ["consultant", "advisor", "manager"]):
        suggestions.extend(["战略规划", "流程改进", "成本控制",
                           "strategic planning", "process improvement", "cost control"])
    
    return list(set(suggestions))[:8]
