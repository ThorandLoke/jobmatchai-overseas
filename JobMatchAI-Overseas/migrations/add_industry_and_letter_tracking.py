"""
数据库迁移脚本 v2
为申请追踪添加行业分类和求职信进化功能

新增字段：
- industry: 行业分类
- cover_letter_version: 求职信版本号
- previous_letter_summary: 上封求职信摘要（用于学习改进）

Copyright © 2026 JobMatchAI. All rights reserved.
"""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "jobmatchai.db")

# 行业定义（多语言）
INDUSTRIES = {
    "it_tech": {
        "name_zh": "IT/科技",
        "name_en": "IT & Technology",
        "name_da": "IT & Teknologi"
    },
    "finance": {
        "name_zh": "金融/银行",
        "name_en": "Finance & Banking",
        "name_da": "Finans & Bank"
    },
    "erp_sap": {
        "name_zh": "ERP/企业管理软件",
        "name_en": "ERP & Enterprise Software",
        "name_da": "ERP & Virksomhedssoftware"
    },
    "consulting": {
        "name_zh": "咨询/顾问",
        "name_en": "Consulting",
        "name_da": "Rådgivning"
    },
    "manufacturing": {
        "name_zh": "制造业",
        "name_en": "Manufacturing",
        "name_da": "Produktion"
    },
    "retail": {
        "name_zh": "零售/电商",
        "name_en": "Retail & E-commerce",
        "name_da": "Detailhandel & E-handel"
    },
    "healthcare": {
        "name_zh": "医疗健康",
        "name_en": "Healthcare",
        "name_da": "Sundhedssektor"
    },
    "energy": {
        "name_zh": "能源/环保",
        "name_en": "Energy & Sustainability",
        "name_da": "Energi & Bæredygtighed"
    },
    "education": {
        "name_zh": "教育/培训",
        "name_en": "Education & Training",
        "name_da": "Uddannelse & Træning"
    },
    "other": {
        "name_zh": "其他",
        "name_en": "Other",
        "name_da": "Andet"
    }
}


def run_migration():
    """执行数据库迁移"""
    if not os.path.exists(DB_PATH):
        print(f"❌ 数据库不存在: {DB_PATH}")
        return False
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 检查现有字段
    cursor.execute("PRAGMA table_info(applications)")
    existing_columns = [col[1] for col in cursor.fetchall()]
    
    migrations_applied = []
    
    # 迁移1: 添加行业字段
    if "industry" not in existing_columns:
        cursor.execute("ALTER TABLE applications ADD COLUMN industry TEXT DEFAULT 'other'")
        migrations_applied.append("✅ 添加 industry 字段")
    
    # 迁移2: 添加求职信版本字段
    if "cover_letter_version" not in existing_columns:
        cursor.execute("ALTER TABLE applications ADD COLUMN cover_letter_version INTEGER DEFAULT 1")
        migrations_applied.append("✅ 添加 cover_letter_version 字段")
    
    # 迁移3: 添加上封求职信摘要字段
    if "previous_letter_summary" not in existing_columns:
        cursor.execute("ALTER TABLE applications ADD COLUMN previous_letter_summary TEXT")
        migrations_applied.append("✅ 添加 previous_letter_summary 字段")
    
    # 迁移4: 添加申请信质量评分字段
    if "letter_quality_score" not in existing_columns:
        cursor.execute("ALTER TABLE applications ADD COLUMN letter_quality_score REAL DEFAULT 0")
        migrations_applied.append("✅ 添加 letter_quality_score 字段")
    
    # 迁移5: 添加目标薪资字段（用于和市场薪资对比）
    if "expected_salary" not in existing_columns:
        cursor.execute("ALTER TABLE applications ADD COLUMN expected_salary TEXT")
        migrations_applied.append("✅ 添加 expected_salary 字段")
    
    conn.commit()
    conn.close()
    
    for msg in migrations_applied:
        print(msg)
    
    if migrations_applied:
        print(f"\n🎉 迁移完成！共应用 {len(migrations_applied)} 项更改")
    else:
        print("✅ 数据库已是最新版本")
    
    return True


def get_industry_list(language="en"):
    """获取行业列表"""
    result = {}
    for key, info in INDUSTRIES.items():
        if language == "zh":
            name = info["name_zh"]
        elif language == "da":
            name = info["name_da"]
        else:
            name = info["name_en"]
        result[key] = name
    return result


def detect_industry_from_job_title(job_title: str) -> str:
    """根据职位标题自动识别行业"""
    job_title_lower = job_title.lower()
    
    industry_keywords = {
        "it_tech": ["developer", "engineer", "software", "data", "cloud", "devops", "security", "it ", "tech"],
        "finance": ["finance", "accountant", "financial", "bank", "investment", "cfo", "controller"],
        "erp_sap": ["erp", "sap", "netsuite", "dynamics", "axapta", "oracle", "crm", "implementation"],
        "consulting": ["consultant", "consulting", "advisory", "advisor"],
        "manufacturing": ["manufacturing", "production", "operations", "supply chain", "logistics"],
        "retail": ["retail", "ecommerce", "e-commerce", "sales", "marketing"],
        "healthcare": ["health", "medical", "pharma", "hospital"],
        "energy": ["energy", "sustainability", "renewable", "environmental"],
        "education": ["education", "teacher", "training", "academic"]
    }
    
    for industry, keywords in industry_keywords.items():
        for keyword in keywords:
            if keyword in job_title_lower:
                return industry
    
    return "other"


if __name__ == "__main__":
    run_migration()
    print("\n📋 行业列表:")
    for key, name in get_industry_list("en").items():
        print(f"  {key}: {name}")
