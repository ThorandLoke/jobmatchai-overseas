"""
JobMatchAI - 智能学习资源推荐引擎
根据用户缺失技能，匹配合适的学习资源（免费 + 付费）

策略：
1. 先查硬编码数据库（速度快，精选优质资源）
2. 命中 → 直接返回
3. 未命中 → 调用 AI（Groq/OpenAI）动态生成学习资源
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import re
import json
import sys
import os

router = APIRouter(prefix="/learning", tags=["智能学习推荐"])

# ============================================================
# AI 客户端（从 backend_main 共享，避免重复初始化）
# ============================================================
def get_ai_client():
    """获取当前可用的 AI 客户端"""
    try:
        import backend_main as bm
        if hasattr(bm, 'smart_ai_request'):
            return bm.smart_ai_request
    except Exception:
        pass
    return None


async def ai_generate_resources(skill: str, job_title: str = "") -> dict:
    """
    用 AI 为未知技能动态生成学习资源（搜索页 URL 格式，不生成具体课程链接）
    """
    smart_ai = get_ai_client()
    if not smart_ai:
        return None

    prompt = f"""你是一个职业发展顾问，需要为求职者推荐学习资源。

目标职位：{job_title or '未知'}
需要提升的技能：{skill}

请生成 JSON 格式的学习资源推荐，要求：
1. free 数组：3-4个免费资源，必须包含 B站搜索链接
2. paid 数组：2个付费资源
3. URL 必须用搜索页格式（不要具体课程链接，容易失效）：
   - B站：https://search.bilibili.com/all?keyword=SKILL（替换SKILL为中文关键词）
   - Coursera：https://www.coursera.org/search?query=SKILL
   - Udemy：https://www.udemy.com/topic/SKILL/
   - LinkedIn Learning：https://www.linkedin.com/learning/topics/SKILL
   - edX：https://www.edx.org/search?q=SKILL
   - YouTube：https://www.youtube.com/results?search_query=SKILL

只返回 JSON，不要其他文字：
{{
  "category": "技能分类名称（英文小写，如 python / data-analysis / project-management）",
  "industry": "所属行业（如 IT、金融、保险、医疗等）",
  "free": [
    {{"title": "B站 - {skill}系列教程", "type": "视频", "url": "https://search.bilibili.com/all?keyword={skill}", "desc": "简短说明", "level": "入门"}},
    {{"title": "YouTube - {skill} Tutorial", "type": "视频", "url": "https://www.youtube.com/results?search_query={skill}+tutorial", "desc": "简短说明", "level": "入门"}},
    {{"title": "Coursera - {skill}", "type": "课程", "url": "https://www.coursera.org/search?query={skill}", "desc": "简短说明", "level": "入门→进阶"}}
  ],
  "paid": [
    {{"title": "Udemy - {skill}课程", "type": "在线课", "url": "https://www.udemy.com/topic/{skill}/", "desc": "简短说明", "level": "进阶", "price_hint": "¥60-200"}},
    {{"title": "LinkedIn Learning - {skill}", "type": "在线课", "url": "https://www.linkedin.com/learning/topics/{skill}", "desc": "简短说明", "level": "进阶", "price_hint": "月订阅"}}
  ]
}}"""

    try:
        response = smart_ai(
            messages=[{"role": "user", "content": prompt}],
            preferred_provider="groq",
            max_tokens=800,
            temperature=0.3
        )
        content = response.choices[0].message.content.strip()
        # 提取 JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()
        data = json.loads(content)
        return {
            "skill": skill,
            "category": data.get("category", skill.lower().replace(" ", "-")),
            "industry": data.get("industry", ""),
            "free": data.get("free", []),
            "paid": data.get("paid", []),
            "ai_generated": True
        }
    except Exception as e:
        print(f"[AI Learning] 生成失败 for '{skill}': {e}")
        return None

router = APIRouter(prefix="/learning", tags=["智能学习推荐"])

# ============================================================
# 技能 → 学习资源数据库（手工精选，持续扩展）
# ============================================================
# 每个技能条目包含：free（免费）和 paid（付费）资源
LEARNING_DATABASE = {

    # ---- ERP / Dynamics 365 / SAP / Oracle NetSuite ----
    "dynamics 365": {
        "keywords": ["dynamics 365", "d365", "dynamics ax", "axapta", "dax"],
        "industry": "ERP",
        "resources": {
            "free": [
                {"title": "Microsoft Learn - Dynamics 365", "type": "文档", "url": "https://learn.microsoft.com/zh-cn/dynamics365/", "desc": "微软官方教程，免费的渐进式学习路径", "level": "入门→进阶"},
                {"title": "Dynamics 365 F&O 免费实验环境", "type": "实验", "url": "https://learn.microsoft.com/zh-cn/dynamics365/fin-ops-core/dev-devpros/d365fo-tutorial/how-to-get-demo-environment", "desc": "免费动手实验环境，边学边练", "level": "进阶"},
                {"title": "Microsoft Dynamics 365 YouTube 频道", "type": "视频", "url": "https://www.youtube.com/@MSDyn365", "desc": "官方产品演示和功能介绍视频", "level": "入门"},
            ],
            "paid": [
                {"title": "Udemy - Microsoft Dynamics 365 FO 开发课程", "type": "在线课", "url": "https://www.udemy.com/topic/microsoft-dynamics-365/", "desc": "涵盖实施、开发、配置全流程", "level": "进阶", "price_hint": "¥60-200"},
                {"title": "Coursera - Microsoft Dynamics 365 专项课程", "type": "证书课", "url": "https://www.coursera.org/search?query=dynamics%20365", "desc": "可获认证，职场认可度高", "level": "入门→进阶", "price_hint": "免费旁听/证书付费"},
            ]
        }
    },

    "sap": {
        "keywords": ["sap", "sap s/4hana", "sap erp", "abap", "sap fico", "sap mm"],
        "industry": "ERP",
        "resources": {
            "free": [
                {"title": "SAP Learning - 免费入门课程", "type": "课程", "url": "https://learning.sap.com", "desc": "SAP官方免费课程，从零开始", "level": "入门"},
                {"title": "OpenSAP - 免费大学课程", "type": "课程", "url": "https://opensap.com", "desc": "SAP合作伙伴大学的免费课程", "level": "入门→进阶"},
                {"title": "SAP Community", "type": "社区", "url": "https://community.sap.com", "desc": "全球SAP从业者问答社区", "level": "全部"},
            ],
            "paid": [
                {"title": "SAP Training - 官方认证课程", "type": "认证", "url": "https://training.sap.com", "desc": "官方认证，含金量最高", "level": "进阶", "price_hint": "¥5000+"},
                {"title": "Udemy - SAP FICO/ABAP 开发", "type": "在线课", "url": "https://www.udemy.com/topic/sap/", "desc": "经济实惠的实操课程", "level": "入门→进阶", "price_hint": "¥60-150"},
            ]
        }
    },

    "netsuite": {
        "keywords": ["netsuite", "oracle netsuite", "suitecloud", "suitescript"],
        "industry": "ERP",
        "resources": {
            "free": [
                {"title": "NetSuite 官方帮助中心", "type": "文档", "url": "https://docs.oracle.com/en/applications/netsuite/suitecloud-apis", "desc": "SuiteCloud API官方文档", "level": "进阶"},
                {"title": "NetSuite 官方 YouTube", "type": "视频", "url": "https://www.youtube.com/@OracleNetSuite", "desc": "产品功能演示视频", "level": "入门"},
                {"title": "NetSuite 社区", "type": "社区", "url": "https://community.oracle.com/community/netsuite", "desc": "用户交流，解决方案分享", "level": "全部"},
            ],
            "paid": [
                {"title": "NetSuite 官方培训", "type": "认证", "url": "https://www.netsuite.com/portal/services/training.shtml", "desc": "官方认证课程", "level": "入门→进阶", "price_hint": "含认证费用"},
                {"title": "Udemy - NetSuite ERP课程", "type": "在线课", "url": "https://www.udemy.com/topic/netsuite/", "desc": "第三方实操课程", "level": "入门→进阶", "price_hint": "¥60-200"},
            ]
        }
    },

    # ---- 财务 / 会计 ----
    "finance": {
        "keywords": ["finance", "financial", "accounting", "bookkeeping", "cpa", "财务", "会计"],
        "industry": "财务",
        "resources": {
            "free": [
                {"title": "Khan Academy - 财务与会计", "type": "视频课", "url": "https://www.khanacademy.org/college-finance", "desc": "从基础到中级，完全免费", "level": "入门→中级"},
                {"title": "Coursera - 财务基础（多所大学）", "type": "证书课", "url": "https://www.coursera.org/courses?query=finance", "desc": "可旁听，有证书选项", "level": "入门→中级"},
                {"title": "Wall Street Prep 免费资源", "type": "教程", "url": "https://www.wallstreetprep.com/", "desc": "华尔街级别的财务建模入门", "level": "中级"},
            ],
            "paid": [
                {"title": "LinkedIn Learning - 财务技能专项", "type": "在线课", "url": "https://www.linkedin.com/learning/topics/accounting", "desc": "Excel财务建模、财务报表分析", "level": "入门→进阶", "price_hint": "月费¥150/企业价"},
                {"title": "Udemy - 财务建模与估值", "type": "在线课", "url": "https://www.udemy.com/topic/financial-modeling/", "desc": "实操型，案例丰富", "level": "中级→进阶", "price_hint": "¥60-200"},
            ]
        }
    },

    "cpa": {
        "keywords": ["cpa", "cfa", "acca", "会计证书", "财务认证"],
        "industry": "财务",
        "resources": {
            "free": [
                {"title": " Becker CPA 备考资源（部分免费）", "type": "备考", "url": "https://www.becker.com/", "desc": "全球最权威CPA备考平台", "level": "备考"},
                {"title": "YouTube - CPA/CFA 免费备考", "type": "视频", "url": "https://www.youtube.com/results?search_query=cpa+exam+study", "desc": "大量免费备考视频", "level": "备考"},
            ],
            "paid": [
                {"title": "Becker CPA Review", "type": "备考课程", "url": "https://www.becker.com/cpa-review", "desc": "通过率最高的CPA备考课程", "level": "备考", "price_hint": "¥8000+"},
                {"title": "Wiley CPAexcel", "type": "备考课程", "url": "https://www.wiley.com/en-us/cpa-excel", "desc": "另一权威CPA备考课程", "level": "备考", "price_hint": "¥6000+"},
            ]
        }
    },

    # ---- 项目管理 ----
    "project management": {
        "keywords": ["project management", "pmp", "pm", "prince2", "scrum", "agile", "项目管理", "敏捷", "敏捷开发", "scrum master"],
        "industry": "项目管理",
        "resources": {
            "free": [
                {"title": "Scrum.org 免费资源", "type": "课程", "url": "https://www.scrum.org/resources", "desc": "Scrum官方免费学习资源", "level": "入门"},
                {"title": "PMI 免费电子书", "type": "电子书", "url": "https://www.pmi.org/learning/publications", "desc": "项目管理协会官方免费读物", "level": "入门"},
                {"title": "Atlassian Agile 指南", "type": "指南", "url": "https://www.atlassian.com/agile", "desc": "Jira出品，实用的敏捷实践指南", "level": "入门→中级"},
            ],
            "paid": [
                {"title": "Udemy - PMP认证备考", "type": "认证课", "url": "https://www.udemy.com/topic/pmp/", "desc": "最新PMBOK第7版，备考PMP", "level": "进阶", "price_hint": "¥150-300"},
                {"title": "LinkedIn Learning - 敏捷/Scrum课程", "type": "在线课", "url": "https://www.linkedin.com/learning/topics/agile", "desc": "含ScrumMaster认证内容", "level": "入门→进阶", "price_hint": "月费¥150"},
            ]
        }
    },

    "agile": {
        "keywords": ["agile", "scrum", "kanban", "jira", "sprint", "敏捷开发", "看板"],
        "industry": "项目管理",
        "resources": {
            "free": [
                {"title": "Atlassian Agile Coach", "type": "指南", "url": "https://www.atlassian.com/agile", "desc": "Jira官方敏捷指南，含实践案例", "level": "入门→中级"},
                {"title": "Scrum Guide - 官方指南（免费PDF）", "type": "文档", "url": "https://scrumguides.org/", "desc": "Scrum创始人发布的权威指南", "level": "入门"},
                {"title": "YouTube - Agile Manifesto 解读", "type": "视频", "url": "https://www.youtube.com/results?search_query=agile+manifesto+tutorial", "desc": "大量免费视频解读", "level": "入门"},
            ],
            "paid": [
                {"title": "Udemy - Agile & Scrum 认证课", "type": "认证课", "url": "https://www.udemy.com/topic/scrum/", "desc": "含PSM I / CSM 认证备考", "level": "入门→进阶", "price_hint": "¥100-300"},
            ]
        }
    },

    # ---- 数据 / 分析 ----
    "data analysis": {
        "keywords": ["data analysis", "data analytics", "power bi", "tableau", "excel", "数据分析", "bi", "商业智能"],
        "industry": "数据分析",
        "resources": {
            "free": [
                {"title": "Microsoft Learn - Power BI", "type": "课程", "url": "https://learn.microsoft.com/zh-cn/power-bi/", "desc": "微软官方免费教程，从入门到大师", "level": "入门→进阶"},
                {"title": "Tableau 官方入门教程", "type": "教程", "url": "https://www.tableau.com/learn/training", "desc": "官方免费学习路径", "level": "入门"},
                {"title": "Kaggle - 公开数据集练习", "type": "实践", "url": "https://www.kaggle.com/datasets", "desc": "真实数据集，边学边练SQL和Python", "level": "中级→进阶"},
            ],
            "paid": [
                {"title": "Udemy - Power BI 数据分析", "type": "在线课", "url": "https://www.udemy.com/topic/microsoft-power-bi/", "desc": "DAX、Power Query全涵盖", "level": "入门→进阶", "price_hint": "¥60-200"},
                {"title": "LinkedIn Learning - Tableau 数据可视化", "type": "在线课", "url": "https://www.linkedin.com/learning/topics/tableau", "desc": "连接LinkedIn简历，职场背书", "level": "入门→进阶", "price_hint": "月费¥150"},
            ]
        }
    },

    "sql": {
        "keywords": ["sql", "mysql", "postgresql", "database", "nosql", "mongodb", "数据库"],
        "industry": "技术",
        "resources": {
            "free": [
                {"title": "SQLZoo - 交互式SQL练习", "type": "练习", "url": "https://sqlzoo.net/", "desc": "浏览器里直接写SQL，零门槛", "level": "入门→中级"},
                {"title": "LeetCode SQL 练习", "type": "刷题", "url": "https://leetcode.com/problemset/database/", "desc": "面试级SQL题库", "level": "中级→进阶"},
                {"title": "Mode SQL Tutorial", "type": "教程", "url": "https://mode.com/sql-tutorial/", "desc": "免费SQL分析完整教程", "level": "入门→中级"},
            ],
            "paid": [
                {"title": "Udemy - MySQL/PostgreSQL 完整课程", "type": "在线课", "url": "https://www.udemy.com/topic/mysql/", "desc": "从安装到高级查询全覆盖", "level": "入门→进阶", "price_hint": "¥60-200"},
            ]
        }
    },

    "python": {
        "keywords": ["python", "pandas", "numpy", "django", "flask", "机器学习", "machine learning", "python编程"],
        "industry": "技术",
        "resources": {
            "free": [
                {"title": "Codecademy 免费Python", "type": "互动课", "url": "https://www.codecademy.com/learn/learn-python-3", "desc": "边写边学，适合零基础", "level": "入门"},
                {"title": "freeCodeCamp YouTube - Python全栈", "type": "视频", "url": "https://www.youtube.com/results?search_query=freecodecamp+python", "desc": "全套免费视频，播放量过亿", "level": "入门→中级"},
                {"title": "Kaggle Python课程", "type": "课程", "url": "https://www.kaggle.com/learn/python", "desc": "数据科学导向的Python入门", "level": "入门→中级"},
            ],
            "paid": [
                {"title": "Udemy - Python全栈开发", "type": "在线课", "url": "https://www.udemy.com/topic/python/", "desc": "最受欢迎的Python课程之一", "level": "入门→进阶", "price_hint": "¥60-200"},
                {"title": "Coursera - Python for Everybody (密歇根大学)", "type": "证书课", "url": "https://www.coursera.org/specializations/python", "desc": "经典大学课程，可获证书", "level": "入门", "price_hint": "免费旁听"},
            ]
        }
    },

    # ---- 供应链 ----
    "supply chain": {
        "keywords": ["supply chain", "logistics", "scm", "warehouse", "procurement", "sourcing", "供应链", "物流", "采购"],
        "industry": "供应链",
        "resources": {
            "free": [
                {"title": "MIT OpenCourseWare - 供应链管理", "type": "大学课", "url": "https://ocw.mit.edu/courses/sloan-school-of-management/", "desc": "MIT斯隆管理学院免费课程", "level": "入门→进阶"},
                {"title": "APICS 供应链入门资源", "type": "资源", "url": "https://www.apics.org/", "desc": "全球供应链管理协会资源", "level": "入门"},
            ],
            "paid": [
                {"title": "Udemy - 供应链管理实战", "type": "在线课", "url": "https://www.udemy.com/topic/supply-chain-management/", "desc": "实操导向的案例课程", "level": "入门→进阶", "price_hint": "¥60-200"},
                {"title": "Coursera - 供应链管理专项（ Rutgers大学）", "type": "专项", "url": "https://www.coursera.org/specializations/supply-chain-management", "desc": "5门课的完整专项，可获证书", "level": "进阶", "price_hint": "免费旁听"},
            ]
        }
    },

    # ---- DevOps / 云 ----
    "cloud": {
        "keywords": ["azure", "aws", "gcp", "cloud", "devops", "docker", "kubernetes", "k8s", "云", "云计算", "ci/cd"],
        "industry": "技术",
        "resources": {
            "free": [
                {"title": "AWS Training 免费数字课程", "type": "官方课", "url": "https://explore.skillbuilder.aws/", "desc": "AWS官方免费学习，含动手实验", "level": "入门→进阶"},
                {"title": "Microsoft Learn - Azure", "type": "官方课", "url": "https://learn.microsoft.com/zh-cn/azure/", "desc": "微软官方免费教程，中文版", "level": "入门→进阶"},
                {"title": "Kubernetes 官方教程", "type": "教程", "url": "https://kubernetes.io/zh-cn/docs/tutorials/", "desc": "K8s官方中文文档和教程", "level": "进阶"},
            ],
            "paid": [
                {"title": "Udemy - AWS/Azure DevOps 认证课", "type": "认证课", "url": "https://www.udemy.com/topic/aws-certified-devops/", "desc": "含AWS DevOps认证备考", "level": "进阶", "price_hint": "¥150-300"},
                {"title": "LinkedIn Learning - Docker/Kubernetes", "type": "在线课", "url": "https://www.linkedin.com/learning/topics/docker", "desc": "容器化完整学习路径", "level": "入门→进阶", "price_hint": "月费¥150"},
            ]
        }
    },

    # ---- 语言 ----
    "danish": {
        "keywords": ["danish", "丹麦语", "language", "语言"],
        "industry": "语言",
        "resources": {
            "free": [
                {"title": "Duolingo 丹麦语", "type": "APP", "url": "https://www.duolingo.com/", "desc": "每天10分钟，轻松入门丹麦语", "level": "入门"},
                {"title": "BBC Danish 入门", "type": "教程", "url": "https://www.bbc.co.uk/languages/other/quick-fix/danish-quick-fix.shtml", "desc": "BBC免费丹麦语速成", "level": "入门"},
                {"title": "YouTube - DanishClass101", "type": "视频", "url": "https://www.youtube.com/@DanishClass101", "desc": "丹麦语学习频道，从入门到进阶", "level": "入门→中级"},
            ],
            "paid": [
                {"title": "Preply/Italki - 丹麦语外教课", "type": "外教课", "url": "https://www.italki.com/", "desc": "一对一真人外教，按课时付费", "level": "中级→进阶", "price_hint": "¥50-150/课时"},
                {"title": "Babbel 丹麦语订阅", "type": "APP订阅", "url": "https://www.babbel.com/", "desc": "欧洲市场占有率最高的语言APP", "level": "入门→中级", "price_hint": "月费约¥90"},
            ]
        }
    },

    # ---- 软技能 ----
    "communication": {
        "keywords": ["communication", "presentation", "public speaking", "soft skill", "沟通", "演讲", "软技能"],
        "industry": "软技能",
        "resources": {
            "free": [
                {"title": "Coursera - 有效沟通（多所大学）", "type": "证书课", "url": "https://www.coursera.org/search?query=communication%20skills", "desc": "可旁听顶尖大学的沟通课", "level": "入门→中级"},
                {"title": "YouTube - TED Talks 演讲技巧", "type": "视频", "url": "https://www.youtube.com/results?search_query=how+to+give+a+good+presentation", "desc": "大量免费演讲技巧视频", "level": "入门"},
            ],
            "paid": [
                {"title": "LinkedIn Learning - 商务沟通专项", "type": "专项", "url": "https://www.linkedin.com/learning/topics/communication", "desc": "含职场邮件、演讲、会议沟通", "level": "入门→进阶", "price_hint": "月费¥150"},
            ]
        }
    },

    "leadership": {
        "keywords": ["leadership", "management", "coaching", "team", "领导力", "管理", "团队"],
        "industry": "软技能",
        "resources": {
            "free": [
                {"title": "Harvard Business Review 精选文章", "type": "文章", "url": "https://hbr.org/", "desc": "全球顶级管理思想，含免费文章", "level": "入门→进阶"},
                {"title": "MIT OpenCourseWare - 领导力", "type": "大学课", "url": "https://ocw.mit.edu/courses/sloan-school-of-management/", "desc": "MIT斯隆管理学院领导力课程", "level": "进阶"},
            ],
            "paid": [
                {"title": "Udemy - 领导力与管理技能", "type": "在线课", "url": "https://www.udemy.com/topic/leadership/", "desc": "实用的管理技巧和案例", "level": "入门→进阶", "price_hint": "¥60-200"},
            ]
        }
    },

    # ---- Excel / Office ----
    "excel": {
        "keywords": ["excel", "vlookup", "pivot table", "spreadsheet", "数据分析", "宏", "vba"],
        "industry": "工具",
        "resources": {
            "free": [
                {"title": "Microsoft 官方 Excel 帮助", "type": "文档", "url": "https://support.microsoft.com/zh-cn/excel", "desc": "最权威的Excel函数和功能帮助", "level": "全部"},
                {"title": "YouTube - ExcelJet 快捷键和公式", "type": "视频", "url": "https://www.youtube.com/@ExcelJet", "desc": "大量短平快的Excel技巧视频", "level": "入门→进阶"},
                {"title": "Chandoo.org - Excel图表和透视表", "type": "博客", "url": "https://chandoo.org/", "desc": "Excel图表和高级技巧博客", "level": "中级→进阶"},
            ],
            "paid": [
                {"title": "Udemy - Excel从入门到精通", "type": "在线课", "url": "https://www.udemy.com/topic/microsoft-excel/", "desc": "含VBA、Power Query高级内容", "level": "入门→进阶", "price_hint": "¥60-200"},
            ]
        }
    },

    # ---- 简历/求职 ----
    "resume": {
        "keywords": ["resume", "cv", "linkedin", "个人简历", "领英", "简历优化"],
        "industry": "求职",
        "resources": {
            "free": [
                {"title": "LinkedIn 免费简历检查", "type": "工具", "url": "https://www.linkedin.com/profile-builder", "desc": "LinkedIn官方简历工具", "level": "入门"},
                {"title": "Indeed 简历指南", "type": "指南", "url": "https://www.indeed.com/career-advice/resumes-cover-letters", "desc": "各行业简历写作指南", "level": "入门"},
                {"title": "Jobscan - ATS简历优化", "type": "工具", "url": "https://www.jobscan.co/", "desc": "检查简历对ATS的友好度", "level": "进阶"},
            ],
            "paid": [
                {"title": "TopResume - 专业简历优化", "type": "服务", "url": "https://www.topresume.com/", "desc": "专业HR一对一优化", "level": "进阶", "price_hint": "¥300-800"},
            ]
        }
    },

    # ---- AI / 机器学习 ----
    "ai": {
        "keywords": ["ai", "artificial intelligence", "machine learning", "deep learning", "llm", "chatgpt", "prompt engineering", "人工智能", "机器学习", "prompt"],
        "industry": "技术",
        "resources": {
            "free": [
                {"title": "fast.ai - 深度学习课程（免费）", "type": "课程", "url": "https://www.fast.ai/", "desc": "全球最受欢迎的免费深度学习课程", "level": "入门→进阶"},
                {"title": "Google AI Education", "type": "官方课", "url": "https://ai.google/education/", "desc": "Google官方AI学习资源", "level": "入门→进阶"},
                {"title": "DeepLearning.AI Coursera", "type": "证书课", "url": "https://www.coursera.org/specializations/deep-learning", "desc": "吴恩达深度学习专项课", "level": "入门→进阶", "price_hint": "免费旁听"},
            ],
            "paid": [
                {"title": "Udemy - 机器学习A-Z", "type": "在线课", "url": "https://www.udemy.com/topic/machine-learning/", "desc": "Python + R 双语言，含案例", "level": "入门→进阶", "price_hint": "¥150-300"},
                {"title": "Coursera - DeepLearning.AI TensorFlow开发者", "type": "认证", "url": "https://www.coursera.org/professional-certificates/tensorflow-in-practice", "desc": "吴恩达系列，职场认可", "level": "进阶", "price_hint": "免费旁听"},
            ]
        }
    },

    # ---- CRM / Salesforce ----
    "crm": {
        "keywords": ["salesforce", "crm", "hubspot", "dynamics crm", "客户管理", "crm系统"],
        "industry": "业务",
        "resources": {
            "free": [
                {"title": "Salesforce Trailhead（免费学习路径）", "type": "官方课", "url": "https://trailhead.salesforce.com/", "desc": "Salesforce官方免费学习平台，含徽章", "level": "入门→进阶"},
                {"title": "HubSpot Academy（免费营销/销售课）", "type": "官方课", "url": "https://academy.hubspot.com/", "desc": "Inbound Marketing权威认证，免费", "level": "入门→进阶"},
            ],
            "paid": [
                {"title": "Udemy - Salesforce Admin/Developer", "type": "在线课", "url": "https://www.udemy.com/topic/salesforce/", "desc": "Salesforce管理员和开发者认证备考", "level": "入门→进阶", "price_hint": "¥60-200"},
            ]
        }
    },

    # ---- GDPR / 合规 ----
    "compliance": {
        "keywords": ["gdpr", "compliance", "data privacy", "legal", "合规", "数据隐私", "信息安全", "security"],
        "industry": "合规",
        "resources": {
            "free": [
                {"title": "GDPR官方指南（欧盟官网）", "type": "官方文档", "url": "https://commission.europa.eu/law/law-topic/data-protection_en", "desc": "欧盟官方GDPR完整说明", "level": "入门→进阶"},
                {"title": "ICO（英国数据保护局）免费指南", "type": "指南", "url": "https://ico.org.uk/for-organisations/uk-gdpr-guidance/", "desc": "欧洲GDPR实操指南", "level": "入门"},
            ],
            "paid": [
                {"title": "Udemy - GDPR合规专项", "type": "在线课", "url": "https://www.udemy.com/topic/gdpr/", "desc": "企业合规实操课程", "level": "入门→进阶", "price_hint": "¥60-150"},
                {"title": "LinkedIn Learning - 信息安全基础", "type": "在线课", "url": "https://www.linkedin.com/learning/topics/security", "desc": "含CISSP等认证入门", "level": "入门→进阶", "price_hint": "月费¥150"},
            ]
        }
    },

    # ---- 通用技能关键词扩展 ----
    "programming": {
        "keywords": ["programming", "coding", "software development", "oop", "api", "rest api", "web development", "编程", "开发"],
        "industry": "技术",
        "resources": {
            "free": [
                {"title": "freeCodeCamp - Web开发全栈", "type": "课程", "url": "https://www.freecodecamp.org/", "desc": "全球最知名的免费编程学习平台", "level": "入门→中级"},
                {"title": "The Odin Project", "type": "课程", "url": "https://www.theodinproject.com/", "desc": "全栈Web开发，从零到就业", "level": "入门→中级"},
                {"title": "MDN Web Docs（Mozilla）", "type": "文档", "url": "https://developer.mozilla.org/", "desc": "Web开发最权威的参考资料", "level": "全部"},
            ],
            "paid": [
                {"title": "Udemy - 2024 Web开发 Bootcamp", "type": "在线课", "url": "https://www.udemy.com/topic/web-development/", "desc": "最畅销的Web开发课程", "level": "入门→进阶", "price_hint": "¥60-200"},
            ]
        }
    },

    # ---- 商业分析 ----
    "business analysis": {
        "keywords": ["business analysis", "ba", "requirement", "bpmn", "uml", "业务流程", "需求分析", "business analyst"],
        "industry": "业务分析",
        "resources": {
            "free": [
                {"title": "IIBA 商业分析入门资源", "type": "协会资源", "url": "https://www.iiba.org/", "desc": "国际商业分析协会官方内容", "level": "入门"},
                {"title": "Lucidchart - BPMN教程", "type": "工具教程", "url": "https://www.lucidchart.com/pages/bpmn-tutorial", "desc": "流程图绘制工具 + 教程", "level": "入门→中级"},
            ],
            "paid": [
                {"title": "Udemy - 商业分析实战", "type": "在线课", "url": "https://www.udemy.com/topic/business-analysis/", "desc": "含CBAP/ECBA认证备考内容", "level": "入门→进阶", "price_hint": "¥60-200"},
            ]
        }
    },

}


# ============================================================
# 模糊匹配：技能关键词 → 最相关分类
# ============================================================
def match_skill_to_category(skill: str) -> Optional[str]:
    """将用户输入的技能关键词，匹配到数据库中的分类"""
    skill_lower = skill.lower().strip()

    def word_match(a: str, b: str) -> bool:
        """使用单词边界判断 a 是否出现在 b 中（避免 'ai' 匹配 'supply chain'）"""
        # 用 \b 单词边界做精确词匹配
        pattern = r'\b' + re.escape(a) + r'\b'
        return bool(re.search(pattern, b))

    # 第一轮：单词边界精确匹配
    for category, data in LEARNING_DATABASE.items():
        for kw in data.get("keywords", []):
            kw_lower = kw.lower()
            if word_match(kw_lower, skill_lower) or word_match(skill_lower, kw_lower):
                return category

    # 第二轮：包含匹配（处理复合词，仅限长于3个字母的词）
    for category, data in LEARNING_DATABASE.items():
        for kw in data.get("keywords", []):
            kw_parts = kw.lower().split()
            if any(word_match(part, skill_lower) for part in kw_parts if len(part) > 3):
                return category

    return None


def get_resources_for_skill(skill: str) -> dict:
    """获取单个技能的学习资源（查硬编码数据库）"""
    category = match_skill_to_category(skill)

    if category and category in LEARNING_DATABASE:
        return {
            "skill": skill,
            "category": category,
            "industry": LEARNING_DATABASE[category].get("industry", ""),
            "free": LEARNING_DATABASE[category]["resources"]["free"],
            "paid": LEARNING_DATABASE[category]["resources"]["paid"],
            "ai_generated": False
        }

    # 未命中 → 返回 None，让调用者决定是否用 AI
    return None


def get_fallback_resources(skill: str, lang: str = 'en') -> dict:
    """最终兜底：纯搜索链接（不需要 AI，100% 可用）"""
    skill_encoded = skill.replace(' ', '%20')
    
    if lang == 'zh':
        return {
            "skill": skill,
            "category": "general",
            "industry": "",
            "free": [
                {"title": f"B站 - {skill}教程", "type": "视频", "url": f"https://search.bilibili.com/all?keyword={skill}", "desc": "B站海量中文教学视频", "level": "入门"},
                {"title": f"YouTube - {skill} Tutorial", "type": "视频", "url": f"https://www.youtube.com/results?search_query={skill_encoded}+tutorial", "desc": "英文视频教程", "level": "入门"},
                {"title": f"Coursera - {skill}", "type": "课程", "url": f"https://www.coursera.org/search?query={skill_encoded}", "desc": "顶尖大学在线课程", "level": "入门→进阶"},
            ],
            "paid": [
                {"title": f"Udemy - {skill}课程", "type": "在线课", "url": f"https://www.udemy.com/topic/{skill_encoded}/", "desc": "实操导向课程", "level": "进阶", "price_hint": "¥60-200"},
                {"title": f"LinkedIn Learning - {skill}", "type": "在线课", "url": f"https://www.linkedin.com/learning/topics/{skill_encoded}", "desc": "职业向技能课程", "level": "进阶", "price_hint": "月订阅"},
            ],
            "ai_generated": False
        }
    else:
        # English fallback - no Bilibili
        return {
            "skill": skill,
            "category": "general",
            "industry": "",
            "free": [
                {"title": f"YouTube - {skill} Tutorial", "type": "视频", "url": f"https://www.youtube.com/results?search_query={skill_encoded}+tutorial", "desc": "Free video tutorials", "level": "Beginner"},
                {"title": f"Coursera - {skill}", "type": "课程", "url": f"https://www.coursera.org/search?query={skill_encoded}", "desc": "Top university courses", "level": "Beginner → Intermediate"},
                {"title": f"edX - {skill}", "type": "课程", "url": f"https://www.edx.org/search?q={skill_encoded}", "desc": "Free online courses from MIT, Harvard", "level": "Beginner → Advanced"},
            ],
            "paid": [
                {"title": f"Udemy - {skill} Course", "type": "在线课", "url": f"https://www.udemy.com/topic/{skill_encoded}/", "desc": "Hands-on practical courses", "level": "Intermediate", "price_hint": "$10-20"},
                {"title": f"LinkedIn Learning - {skill}", "type": "在线课", "url": f"https://www.linkedin.com/learning/topics/{skill_encoded}", "desc": "Professional skill courses", "level": "Advanced", "price_hint": "Monthly subscription"},
            ],
            "ai_generated": False
        }


# ============================================================
# API 模型
# ============================================================
class LearningRecommendRequest(BaseModel):
    missing_skills: List[str]
    job_title: Optional[str] = ""
    industry: Optional[str] = ""
    language: Optional[str] = "zh"


class LearningRecommendResponse(BaseModel):
    success: bool
    total_skills: int
    recommendations: List[dict]
    ai_summary: str  # AI生成的整体学习建议


# ============================================================
# API 端点
# ============================================================
@router.post("/recommend", response_model=LearningRecommendResponse)
async def recommend_learning(req: LearningRecommendRequest):
    """
    根据缺失技能，推荐定制化学习资源
    策略：硬编码数据库命中 → 直接返回；未命中 → AI 动态生成
    """
    if not req.missing_skills:
        return LearningRecommendResponse(
            success=True,
            total_skills=0,
            recommendations=[],
            ai_summary="没有检测到技能缺口，无需额外学习。继续优化简历和求职信即可！"
        )

    recommendations = []
    ai_needed = []   # 需要 AI 处理的技能

    # 第一轮：查硬编码数据库
    for skill in req.missing_skills:
        skill_clean = re.sub(r'[\s\-–—]+', ' ', skill.strip())
        if len(skill_clean) < 2:
            continue
        rec = get_resources_for_skill(skill_clean)
        if rec:
            # English mode: remove Bilibili from hardcoded results
            if req.language != 'zh':
                rec['free'] = [r for r in rec.get('free', []) if 'bilibili' not in r.get('url', '').lower()]
                rec['paid'] = [r for r in rec.get('paid', []) if 'bilibili' not in r.get('url', '').lower()]
            recommendations.append(rec)
        else:
            ai_needed.append(skill_clean)

    # 第二轮：AI 批量生成未命中的技能
    if ai_needed:
        import asyncio
        tasks = [ai_generate_resources(skill, req.job_title or "") for skill in ai_needed]
        ai_results = await asyncio.gather(*tasks)
        for skill, result in zip(ai_needed, ai_results):
            if result:
                # English mode: remove Bilibili from AI results
                if req.language != 'zh':
                    result['free'] = [r for r in result.get('free', []) if 'bilibili' not in r.get('url', '').lower()]
                recommendations.append(result)
            else:
                # AI 也失败了 → 用搜索链接兜底（传入语言参数）
                recommendations.append(get_fallback_resources(skill, req.language or 'en'))

    # AI 总结
    industries = [r.get("industry", "") for r in recommendations if r.get("industry")]
    industry_text = "、".join(set(industries)) if industries else "通用职场"
    skill_names = "、".join(req.missing_skills[:5])
    if len(req.missing_skills) > 5:
        skill_names += f" 等{len(req.missing_skills)}项技能"
    ai_count = sum(1 for r in recommendations if r.get("ai_generated"))

    if req.language == 'zh':
        ai_summary = (
            f"根据您的求职目标（{req.job_title or '目标职位'}），"
            f"建议重点补充：{skill_names}。"
            f"B站有大量中文教程，Coursera可获国际认证。"
            f"优先选择带实操练习的内容，完成后记得更新简历！"
        )
    else:
        ai_summary = (
            f"For your target position ({req.job_title or 'target role'}), "
            f"focus on improving: {skill_names}. "
            f"Coursera offers internationally recognized certificates. "
            f"Prioritize hands-on courses and remember to update your resume after completion!"
        )

    return LearningRecommendResponse(
        success=True,
        total_skills=len(recommendations),
        recommendations=recommendations,
        ai_summary=ai_summary
    )


@router.get("/categories")
async def list_categories():
    """列出所有支持的技能分类"""
    categories = []
    for cat, data in LEARNING_DATABASE.items():
        categories.append({
            "id": cat,
            "name": cat.replace("_", " ").title(),
            "industry": data.get("industry", ""),
            "skill_count": len(data.get("keywords", [])),
        })
    return {"success": True, "categories": categories}
