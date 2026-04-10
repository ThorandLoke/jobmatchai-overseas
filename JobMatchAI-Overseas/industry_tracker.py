"""
申请追踪扩展服务 - 行业分类 + 求职信进化 + 薪资参考

新功能：
1. 行业自动识别 - 根据职位标题识别所属行业
2. 求职信版本追踪 - 记录每次申请信的改进点
3. 薪资范围参考 - 基于Adzuna数据 + 免责声明

Copyright © 2026 JobMatchAI. All rights reserved.
"""

import re
from typing import Dict, Any, List, Optional
from datetime import datetime

# 行业关键词映射
INDUSTRY_PATTERNS = {
    "it_tech": {
        "name_zh": "IT/科技",
        "name_en": "IT & Technology",
        "name_da": "IT & Teknologi",
        "keywords": [
            "software", "developer", "engineer", "data", "cloud", "devops", "security",
            "it ", "tech", "technology", "programming", "frontend", "backend", "fullstack",
            "python", "java", "javascript", "c#", ".net", "react", "angular", "vue",
            "aws", "azure", "gcp", "docker", "kubernetes", "linux", "database", "sql",
            "网络", "软件", "开发", "工程师", "数据", "云计算", "IT"
        ]
    },
    "finance": {
        "name_zh": "金融/银行",
        "name_en": "Finance & Banking",
        "name_da": "Finans & Bank",
        "keywords": [
            "finance", "financial", "accountant", "accounting", "bank", "banking",
            "investment", "cfo", "controller", "treasury", "audit", "tax",
            "金融", "财务", "会计", "银行", "投资", "审计", "税务"
        ]
    },
    "erp_sap": {
        "name_zh": "ERP/企业管理软件",
        "name_en": "ERP & Enterprise Software",
        "name_da": "ERP & Virksomhedssoftware",
        "keywords": [
            "erp", "sap", "netsuite", "dynamics", "axapta", "oracle", "crm", "c4c",
            "implementation", "functional", "technical", "consultant", "specialist",
            "SAP", "NetSuite", "Dynamics", "Oracle", "ERP实施", "功能顾问", "技术顾问"
        ]
    },
    "consulting": {
        "name_zh": "咨询/顾问",
        "name_en": "Consulting",
        "name_da": "Rådgivning",
        "keywords": [
            "consultant", "consulting", "advisory", "advisor", "strategy",
            "management", "business", "transformation", "advisor",
            "咨询", "顾问", "战略", "管理咨询", "业务转型"
        ]
    },
    "manufacturing": {
        "name_zh": "制造业",
        "name_en": "Manufacturing",
        "name_da": "Produktion",
        "keywords": [
            "manufacturing", "production", "operations", "supply chain", "logistics",
            "procurement", "quality", "lean", "six sigma", "process engineering",
            "制造", "生产", "运营", "供应链", "采购", "质量"
        ]
    },
    "retail": {
        "name_zh": "零售/电商",
        "name_en": "Retail & E-commerce",
        "name_da": "Detailhandel & E-handel",
        "keywords": [
            "retail", "ecommerce", "e-commerce", "sales", "marketing", "merchandising",
            "brand", "customer", "retail", "电商", "零售", "销售", "营销", "品牌"
        ]
    },
    "healthcare": {
        "name_zh": "医疗健康",
        "name_en": "Healthcare",
        "name_da": "Sundhedssektor",
        "keywords": [
            "health", "healthcare", "medical", "pharma", "pharmaceutical", "hospital",
            "biotech", "clinical", "regulatory",
            "医疗", "健康", "制药", "医院", "生物技术"
        ]
    },
    "energy": {
        "name_zh": "能源/环保",
        "name_en": "Energy & Sustainability",
        "name_da": "Energi & Bæredygtighed",
        "keywords": [
            "energy", "renewable", "solar", "wind", "sustainability", "environmental",
            "carbon", "climate", "green", "能源", "可再生能源", "环保", "绿色"
        ]
    },
    "education": {
        "name_zh": "教育/培训",
        "name_en": "Education & Training",
        "name_da": "Uddannelse & Træning",
        "keywords": [
            "education", "educational", "teacher", "teaching", "training", "academic",
            "university", "school", "learning", "development",
            "教育", "培训", "学术", "大学", "学习"
        ]
    },
    "other": {
        "name_zh": "其他",
        "name_en": "Other",
        "name_da": "Andet",
        "keywords": []
    }
}


def detect_industry(job_title: str, description: str = "") -> Dict[str, Any]:
    """根据职位标题和描述识别行业"""
    combined_text = (job_title + " " + description).lower()
    
    scores = {}
    for industry_id, industry_info in INDUSTRY_PATTERNS.items():
        if industry_id == "other":
            continue
        
        score = 0
        keywords = industry_info["keywords"]
        
        for keyword in keywords:
            # 计算关键词出现次数
            count = combined_text.lower().count(keyword.lower())
            score += count
        
        if score > 0:
            scores[industry_id] = score
    
    if not scores:
        return {
            "industry": "other",
            "name_zh": "其他",
            "name_en": "Other",
            "name_da": "Andet",
            "confidence": 0,
            "matched_keywords": []
        }
    
    # 取最高分
    best_industry = max(scores, key=scores.get)
    industry_info = INDUSTRY_PATTERNS[best_industry]
    
    # 计算匹配关键词
    matched = [kw for kw in industry_info["keywords"] 
               if kw.lower() in combined_text.lower()][:5]
    
    # 计算置信度
    max_score = max(scores.values())
    confidence = min(scores[best_industry] / max_score if max_score > 0 else 0, 1.0)
    
    return {
        "industry": best_industry,
        "name_zh": industry_info["name_zh"],
        "name_en": industry_info["name_en"],
        "name_da": industry_info["name_da"],
        "confidence": round(confidence * 100, 1),
        "matched_keywords": matched
    }


def get_industry_by_id(industry_id: str, language: str = "en") -> str:
    """根据行业ID获取名称"""
    industry = INDUSTRY_PATTERNS.get(industry_id, INDUSTRY_PATTERNS["other"])
    return industry.get(f"name_{language}", industry["name_en"])


def get_all_industries(language: str = "en") -> List[Dict[str, Any]]:
    """获取所有行业列表"""
    result = []
    for industry_id, info in INDUSTRY_PATTERNS.items():
        result.append({
            "id": industry_id,
            "name": info.get(f"name_{language}", info["name_en"])
        })
    return result


# ===== 求职信进化功能 =====

class CoverLetterEvolution:
    """求职信进化追踪器"""
    
    def __init__(self):
        self.previous_letters: List[Dict] = []
    
    def add_letter(self, company: str, job_title: str, content: str, 
                   industry: str = "") -> Dict[str, Any]:
        """记录一封求职信"""
        letter_info = {
            "company": company,
            "job_title": job_title,
            "industry": industry,
            "word_count": len(content.split()),
            "char_count": len(content),
            "has_quantitative": self._check_quantitative(content),
            "has_keywords": self._check_keywords(content),
            "created_at": datetime.now().isoformat()
        }
        
        self.previous_letters.append(letter_info)
        return letter_info
    
    def get_evolution_summary(self) -> Dict[str, Any]:
        """获取进化总结"""
        if not self.previous_letters:
            return {
                "total_letters": 0,
                "improvements": [],
                "tips": []
            }
        
        improvements = []
        tips = []
        
        # 分析量化指标
        avg_words = sum(l["word_count"] for l in self.previous_letters) / len(self.previous_letters)
        if len(self.previous_letters) >= 2:
            improvements.append(f"您已撰写 {len(self.previous_letters)} 封求职信")
        
        # 检查关键词使用
        companies = [l["company"] for l in self.previous_letters[-3:]]
        if len(set(companies)) > 1:
            tips.append("建议：每封求职信都要针对具体公司定制")
        
        return {
            "total_letters": len(self.previous_letters),
            "avg_word_count": round(avg_words),
            "recent_industries": list(set(l["industry"] for l in self.previous_letters[-5:])),
            "improvements": improvements,
            "tips": tips
        }
    
    def _check_quantitative(self, content: str) -> bool:
        """检查是否包含量化指标"""
        patterns = [
            r'\d+%',  # 百分比
            r'\d+\s*(?:个|年|月|人|次|客户|项目)',  # 中文数量
            r'\d+\s*(?:years?|months?|clients?|projects?|customers?)',  # 英文数量
            r'\d{4}',  # 年份
            r'DKK|EUR|USD|¥|\$',  # 货币
        ]
        return any(re.search(p, content, re.IGNORECASE) for p in patterns)
    
    def _check_keywords(self, content: str) -> List[str]:
        """检查关键词"""
        keywords = []
        content_lower = content.lower()
        
        important_keywords = {
            "leadership": ["led", "managed", "supervised", "管理", "负责", "领导"],
            "achievement": ["achieved", "increased", "improved", "reduced", "提高", "增加", "优化"],
            "collaboration": ["collaborated", "partnered", "worked with", "协作", "合作"],
            "impact": ["impact", "result", "outcome", "resulted in", "成果", "成效"]
        }
        
        for category, words in important_keywords.items():
            if any(word.lower() in content_lower for word in words):
                keywords.append(category)
        
        return keywords
    
    def suggest_improvements(self, new_job_title: str, new_industry: str = "") -> List[str]:
        """基于历史申请给出改进建议"""
        suggestions = []
        
        if not self.previous_letters:
            suggestions.append("这是您的第一封求职信，建议包含：职位相关经验、量化成果、为什么适合这个岗位")
            return suggestions
        
        # 检查长度
        recent = self.previous_letters[-3:]
        avg_words = sum(l["word_count"] for l in recent) / len(recent)
        if avg_words < 150:
            suggestions.append("建议增加求职信长度，当前平均 " + str(int(avg_words)) + " 词，目标 200-300 词")
        
        # 检查量化
        recent_quant = [l for l in recent if l.get("has_quantitative")]
        if len(recent_quant) / len(recent) < 0.5:
            suggestions.append("建议添加更多量化数据，如：'提高效率 30%'、'管理 5 人团队'")
        
        # 检查行业定制
        recent_industries = [l.get("industry") for l in recent]
        if new_industry and new_industry not in recent_industries:
            suggestions.append(f"这是一个新的行业({get_industry_by_id(new_industry, 'en')})，建议强调转行业相关经验")
        
        # 检查关键词
        recent_keywords = set()
        for l in recent:
            recent_keywords.update(l.get("has_keywords", []))
        
        if "leadership" not in recent_keywords:
            suggestions.append("建议强调领导力经验：'led a team of 5'、'负责管理...'")
        if "achievement" not in recent_keywords:
            suggestions.append("建议突出成就：'achieved X by doing Y'")
        
        return suggestions


# ===== 薪资范围查询功能 =====

# Adzuna API 配置
ADZUNA_APP_ID = "690f8e34"
ADZUNA_APP_KEY = "9e5d7db533450288d6780344c1c160ba"

# 国家代码映射
COUNTRY_TO_ADZUNA = {
    "DK": "dk",  # Denmark
    "SE": "se",  # Sweden
    "NO": "no",  # Norway
    "GB": "gb",  # UK
    "AU": "au",  # Australia
    "CA": "ca",  # Canada
    "FR": "fr",  # France
    "NL": "nl",  # Netherlands
    "BE": "be",  # Belgium
    "DE": "de",  # Germany
}

# 丹麦/北欧特定薪资范围参考（基于市场数据）
NORDIC_SALARY_RANGES = {
    "erp": {"min": 550000, "max": 850000, "currency": "DKK"},  # DKK/year
    "sap": {"min": 600000, "max": 900000, "currency": "DKK"},
    "netsuite": {"min": 550000, "max": 800000, "currency": "DKK"},
    "dynamics": {"min": 550000, "max": 850000, "currency": "DKK"},
    "consultant": {"min": 500000, "max": 750000, "currency": "DKK"},
    "developer": {"min": 450000, "max": 700000, "currency": "DKK"},
    "default": {"min": 400000, "max": 600000, "currency": "DKK"},
}

def get_salary_estimate(job_title: str, location: str = "", country: str = "DK") -> Dict[str, Any]:
    """获取薪资估算
    
    使用 Adzuna API 获取真实数据，或基于北欧市场数据估算
    返回数据仅供参考，不保证准确性
    """
    import requests
    
    # 默认返回值
    default_response = {
        "salary_min": None,
        "salary_max": None,
        "salary_median": None,
        "currency": "DKK",
        "country": country,
        "job_title": job_title,
        "location": location,
        "source": None,
        "disclaimer": "薪资数据仅供参考，实际薪资取决于公司、经验、谈判等因素。",
        "disclaimer_en": "Salary data is for reference only. Actual salary depends on company, experience, and negotiation.",
        "disclaimer_da": "Løndata er kun til reference. Faktisk løn afhænger af virksomhed, erfaring og forhandling."
    }
    
    if not job_title:
        return default_response
    
    # 尝试 Adzuna API
    adzuna_country = COUNTRY_TO_ADZUNA.get(country.upper())
    if adzuna_country:
        try:
            url = f"http://api.adzuna.com/v1/api/jobs/{adzuna_country}/search/1"
            params = {
                "app_id": ADZUNA_APP_ID,
                "app_key": ADZUNA_APP_KEY,
                "what": job_title,
                "results_per_page": 10,
                "content-type": "application/json"
            }
            
            response = requests.get(url, params=params, timeout=5)
            if response.status_code == 200:
                data = response.json()
                if data.get("results"):
                    salaries = []
                    for job in data["results"]:
                        salary = job.get("salary_min") or job.get("salary_max")
                        if salary:
                            salaries.append(salary)
                    
                    if salaries:
                        avg_salary = sum(salaries) / len(salaries)
                        min_salary = min(salaries)
                        max_salary = max(salaries)
                        
                        # 转换为年薪
                        if avg_salary < 10000:  # 可能是月薪
                            min_salary *= 12
                            max_salary *= 12
                            avg_salary *= 12
                        
                        return {
                            "salary_min": int(min_salary),
                            "salary_max": int(max_salary),
                            "salary_median": int(avg_salary),
                            "currency": "DKK" if country == "DK" else "EUR" if country in ["NL", "BE", "DE"] else "GBP",
                            "country": country,
                            "job_title": job_title,
                            "location": location,
                            "source": "Adzuna",
                            "disclaimer": "薪资数据仅供参考，实际薪资取决于公司、经验、谈判等因素。",
                            "disclaimer_en": "Salary data is for reference only. Actual salary depends on company, experience, and negotiation.",
                            "disclaimer_da": "Løndata er kun til reference. Faktisk løn afhænger af virksomhed, erfaring og forhandling."
                        }
        except Exception as e:
            print(f"Adzuna salary API error: {e}")
    
    # 使用北欧市场数据估算（当 API 失败时）
    job_lower = job_title.lower()
    
    # 根据职位关键词匹配薪资范围
    if any(k in job_lower for k in ["sap", "erp", "dynamics", "netsuite", "oracle", "ax"]):
        range_key = "sap" if "sap" in job_lower else "erp"
    elif "consultant" in job_lower or "advisor" in job_lower:
        range_key = "consultant"
    elif any(k in job_lower for k in ["developer", "engineer", "programmer"]):
        range_key = "developer"
    else:
        range_key = "default"
    
    salary_data = NORDIC_SALARY_RANGES[range_key]
    
    return {
        "salary_min": salary_data["min"],
        "salary_max": salary_data["max"],
        "salary_median": (salary_data["min"] + salary_data["max"]) // 2,
        "currency": salary_data["currency"],
        "country": country,
        "job_title": job_title,
        "location": location,
        "source": "Market Estimate (Nordic Region)",
        "disclaimer": "薪资数据仅供参考，实际薪资取决于公司、经验、谈判等因素。",
        "disclaimer_en": "Salary data is for reference only. Actual salary depends on company, experience, and negotiation.",
        "disclaimer_da": "Løndata er kun til reference. Faktisk løn afhænger af virksomhed, erfaring og forhandling."
    }


def format_salary_range(salary_data: Dict) -> str:
    """格式化薪资范围显示"""
    if not salary_data.get("salary_min"):
        return "薪资数据不可用"
    
    min_sal = salary_data["salary_min"]
    max_sal = salary_data["salary_max"]
    currency = salary_data.get("currency", "DKK")
    
    if currency == "DKK":
        # 丹麦通常报年薪
        if min_sal >= 100000:
            return f"DKK {min_sal/1000:.0f}K - {max_sal/1000:.0f}K / 年"
        else:
            return f"DKK {min_sal:.0f} - {max_sal:.0f} / 年"
    
    return f"{currency} {min_sal:,.0f} - {max_sal:,.0f}"


def get_salary_tips(country: str = "DK") -> List[str]:
    """获取薪资谈判建议"""
    tips_by_country = {
        "DK": [
            "丹麦薪资通常为年薪，包含度假金（feriepenge）12.5%",
            "面试时可以询问：整体包（total package）包含什么",
            "福利如养老金、健康保险等也需要计入总报酬",
            "试用期（prøvetid）薪资通常与正式薪资相同"
        ],
        "SE": [
            "瑞典薪资也是年薪制，谈判时可以要求 13 薪",
            "瑞典重视工作生活平衡，可以询问弹性工作时间",
            "养老金（tjänstepension）是重要组成部分"
        ],
        "NO": [
            "挪威薪资较高，但生活成本也高",
            "注意区分毛薪和净薪",
            "养老金（tjenestepensjon）是标配"
        ],
        "default": [
            "面试时询问整体报酬包（total compensation package）",
            "不要只谈基本工资，福利同样重要",
            "准备好你的薪资历史作为谈判依据",
            "了解行业平均水平，不要低于底线"
        ]
    }
    
    return tips_by_country.get(country, tips_by_country["default"])


# ===== 行业申请策略 =====

INDUSTRY_STRATEGIES = {
    "it_tech": {
        "name_zh": "IT/科技",
        "cv_focus": ["技术栈", "项目经验", "GitHub", "认证"],
        "cl_focus": ["解决问题的能力", "团队协作", "技术创新"],
        "common_questions": ["你最引以为豪的项目是什么？", "如何处理技术挑战？"]
    },
    "erp_sap": {
        "name_zh": "ERP/企业管理软件",
        "cv_focus": ["认证", "行业经验", "实施方法论"],
        "cl_focus": ["业务理解", "项目管理", "变革管理"],
        "common_questions": ["你实施过哪些模块？", "如何处理用户抵制？"]
    },
    "consulting": {
        "name_zh": "咨询/顾问",
        "cv_focus": ["案例分析", "行业专长", "客户案例"],
        "cl_focus": ["问题诊断能力", "沟通技巧", "价值主张"],
        "common_questions": ["你如何理解客户需求？", "举个成功的咨询案例"]
    },
    "finance": {
        "name_zh": "金融/银行",
        "cv_focus": ["证书", "财务指标", "合规经验"],
        "cl_focus": ["数字敏感度", "风险意识", "法规了解"],
        "common_questions": ["你如何评估风险？", "解释一个财务模型"]
    }
}


def get_industry_strategy(industry_id: str) -> Dict[str, Any]:
    """获取行业特定的申请策略"""
    return INDUSTRY_STRATEGIES.get(industry_id, {
        "name_zh": "通用",
        "cv_focus": ["核心技能", "项目经验", "成果量化"],
        "cl_focus": ["为何适合", "能为公司带来什么"],
        "common_questions": []
    })
