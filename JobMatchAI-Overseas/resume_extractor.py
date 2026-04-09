"""
简历精准抓取模块 - ResumeExtractor
从简历文本提取结构化信息，并与职位进行智能匹配

核心功能：
1. 从简历文本提取：工作经历、技能、教育、证书等
2. 与目标职位进行匹配评分
3. 识别简历中的能力差距
4. 生成针对性的简历优化建议

Author: JobMatchAI
"""

import re
import json
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field, asdict


# ============================================================
# 数据模型
# ============================================================

@dataclass
class WorkExperience:
    """工作经历"""
    title: str
    company: str
    duration: str
    start_date: str = ""
    end_date: str = ""
    description: str = ""
    skills_used: List[str] = field(default_factory=list)
    achievements: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Education:
    """教育背景"""
    degree: str
    school: str
    field_of_study: str = ""
    graduation_year: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class Certificate:
    """证书/认证"""
    name: str
    issuer: str = ""
    year: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ResumeProfile:
    """完整简历画像"""
    name: str = ""
    email: str = ""
    phone: str = ""
    location: str = ""
    title: str = ""  # 目标职位
    summary: str = ""
    work_experiences: List[WorkExperience] = field(default_factory=list)
    education: List[Education] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)
    certificates: List[Certificate] = field(default_factory=list)
    total_years: int = 0

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "email": self.email,
            "phone": self.phone,
            "location": self.location,
            "title": self.title,
            "summary": self.summary,
            "work_experiences": [e.to_dict() for e in self.work_experiences],
            "education": [e.to_dict() for e in self.education],
            "skills": self.skills,
            "languages": self.languages,
            "certificates": [c.to_dict() for c in self.certificates],
            "total_years": self.total_years
        }


@dataclass
class JobRequirement:
    """职位要求"""
    title: str
    company: str = ""
    required_skills: List[str] = field(default_factory=list)
    preferred_skills: List[str] = field(default_factory=list)
    required_years: int = 0
    preferred_years: int = 0
    description: str = ""

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class MatchResult:
    """匹配结果"""
    overall_score: float  # 0-100
    skill_match_rate: float  # 0-100
    experience_match_rate: float  # 0-100
    matched_skills: List[str] = field(default_factory=list)
    missing_skills: List[str] = field(default_factory=list)
    partial_skills: List[str] = field(default_factory=list)  # 部分匹配
    gap_analysis: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    strengths: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return asdict(self)


# ============================================================
# 简历解析引擎
# ============================================================

class ResumeExtractor:
    """简历精准抓取引擎"""

    # 技能关键词库（多语言）
    SKILL_KEYWORDS = {
        # ERP & 财务系统
        'ERP': ['erp', 'sap', 'netsuite', 'dynamics', 'ax', '365', 'f&o', 'finops', 'oracle', 'sage'],
        'SAP': ['sap', 'sap erp', 'sap s/4hana', 'sap fi', 'sap co', 'sap mm', 'sap sd'],
        'NetSuite': ['netsuite', 'oracle netsuite', 'suitecloud', 'suitescript'],
        'Dynamics': ['dynamics', 'dynamics ax', 'dynamics 365', 'd365', 'axapta'],
        # 财务
        '财务': ['finance', 'financial', 'accounting', 'controlling', 'budgeting', 'forecasting', '财务', '会计', '预算'],
        '会计': ['accounting', 'gl', 'ap', 'ar', 'fixed assets', '总账', '应收', '应付'],
        # 技术
        'SQL': ['sql', 'mysql', 'postgresql', 't-sql', 'database'],
        'Python': ['python', 'pandas', 'numpy', 'django', 'flask'],
        'Excel': ['excel', 'vlookup', 'pivot', 'vba', 'macros'],
        'BI': ['powerbi', 'tableau', 'looker', 'bi', 'reporting', 'dashboard'],
        # 项目管理
        '项目管理': ['project management', 'pmp', 'prince2', 'scrum', 'agile', 'waterfall', '项目'],
        '咨询': ['consulting', 'advisory', 'implementation', 'consultant', '咨询', '实施'],
        # 供应链
        '供应链': ['supply chain', 'scm', 'logistics', 'procurement', 'purchasing', 'wms', '供应链', '采购'],
        # 语言
        '丹麦语': ['dansk', 'danish', '丹麦语'],
        '英语': ['english', 'engelsk', '英语', 'cet-6', 'cet-4', 'ielts', 'toefl'],
        '中文': ['chinese', 'mandarin', '中文', '普通话'],
        '德语': ['german', 'deutsch', '德语'],
        # 行业
        '制造业': ['manufacturing', 'production', 'industrial', '制造业', '生产'],
        '零售': ['retail', 'e-commerce', 'omni-channel', '零售', '电商'],
        '咨询业': ['consulting', 'advisory', 'consultancy', '咨询'],
    }

    # 强动词（成就导向）
    STRONG_VERBS = {
        'en': ['led', 'implemented', 'achieved', 'improved', 'reduced', 'increased', 'delivered',
               'transformed', 'optimized', 'established', 'launched', 'delivered', 'spearheaded',
               'architected', 'automated', 'streamlined', 'drove', 'orchestrated', 'pioneered'],
        'zh': ['主导', '实现', '达成', '提升', '降低', '增长', '推动', '优化', '建立',
               '发起', '设计', '自动化', '精简', '领导', '开拓', '架构'],
        'da': ['ledede', 'implementerede', 'opnåede', 'forbedrede', 'reducerede', 'øgede',
               'leverte', 'transformerede', 'optimerede', 'etablerede', 'lancerede']
    }

    # 弱动词
    WEAK_VERBS = {
        'en': ['did', 'was responsible for', 'worked on', 'helped with', 'assisted',
               'participated in', 'involved in', 'handled', 'managed'],
        'zh': ['做了', '负责了', '参与了', '协助', '帮助', '参与', '涉及'],
        'da': ['lavede', 'var ansvarlig for', 'arbejdede på', 'hjalp med', 'assisterede']
    }

    def __init__(self):
        pass

    def extract(self, resume_text: str) -> ResumeProfile:
        """从简历文本提取完整结构化信息"""
        profile = ResumeProfile()
        text = resume_text.strip()

        # 1. 提取基本信息
        profile.name = self._extract_name(text)
        profile.email = self._extract_email(text)
        profile.phone = self._extract_phone(text)
        profile.location = self._extract_location(text)

        # 2. 提取技能
        profile.skills = self._extract_skills(text)

        # 3. 提取工作经历
        profile.work_experiences = self._extract_work_experiences(text)
        profile.total_years = self._calculate_total_years(profile.work_experiences)

        # 4. 提取教育背景
        profile.education = self._extract_education(text)

        # 5. 提取证书
        profile.certificates = self._extract_certificates(text)

        # 6. 提取语言能力
        profile.languages = self._extract_languages(text)

        # 7. 提取个人简介
        profile.summary = self._extract_summary(text)

        return profile

    def _extract_name(self, text: str) -> str:
        """提取姓名（通常在第一行）"""
        lines = text.split('\n')
        for line in lines[:3]:
            line = line.strip()
            # 过滤掉邮箱、职位描述等
            if '@' in line or 'http' in line or len(line) > 50:
                continue
            # 姓名通常是2-4个汉字或2-3个英文单词
            chinese_name = re.findall(r'^[\u4e00-\u9fff]{2,4}$', line)
            if chinese_name:
                return chinese_name[0]
            english_name = re.findall(r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})$', line)
            if english_name:
                return english_name[0]
        return ""

    def _extract_email(self, text: str) -> str:
        """提取邮箱"""
        match = re.search(r'[\w.+-]+@[\w-]+\.[\w.-]+', text)
        return match.group(0) if match else ""

    def _extract_phone(self, text: str) -> str:
        """提取电话"""
        # 支持多种格式
        patterns = [
            r'\+?[\d\s\-\(\)]{10,20}',  # 国际格式
            r'[\d]{3,4}[-][\d]{7,8}',  # 中国格式
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text)
            for m in matches:
                digits = re.sub(r'\D', '', m)
                if 7 <= len(digits) <= 15:
                    return m
        return ""

    def _extract_location(self, text: str) -> str:
        """提取地点"""
        patterns = [
            r'(?:location|地址|所在地|based in|located in)[:\s]*([^\n,]+)',
            r'([\u4e00-\u9fff]{2,6}(?:市|省|区|县))',
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        return ""

    def _extract_skills(self, text: str) -> List[str]:
        """提取技能关键词"""
        text_lower = text.lower()
        found_skills = set()

        for category, keywords in self.SKILL_KEYWORDS.items():
            for kw in keywords:
                if kw.lower() in text_lower:
                    # 标准化技能名称
                    if category == 'ERP' and 'netsuite' in text_lower:
                        found_skills.add('NetSuite')
                    elif category == 'ERP' and 'dynamics' in text_lower:
                        found_skills.add('Dynamics 365')
                    elif category == 'ERP' and 'sap' in text_lower:
                        found_skills.add('SAP')
                    else:
                        found_skills.add(category)
                    break

        return sorted(list(found_skills))

    def _extract_work_experiences(self, text: str) -> List[WorkExperience]:
        """提取工作经历"""
        experiences = []

        # 尝试识别工作经历区块
        # 模式1: 公司名 + 职位 + 时间段
        exp_pattern = re.compile(
            r'(?:^|\n)([^@\n]+?)\s*(?:at|@|\||·|,)\s*([^\n]+?)\s*\n?\s*'
            r'(\d{4}[\s\-–]\w+[\s\-–]\d{4}|\d{4}[\s\-–]\w+|'
            r'\d{2}/\d{4}[\s\-–]\d{2}/\d{4}|\d{2}/\d{4}[\s\-–]now|'
            r'(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[\w]*\s*\d{4}[\s\-–](?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[\w]*\s*\d{4}|now))',
            re.IGNORECASE
        )

        # 简单模式：按行分割，查找包含职位关键词的行
        lines = text.split('\n')
        current_exp = None
        exp_buffer = []

        job_indicators = [
            'consultant', 'manager', 'director', 'specialist', 'engineer', 'analyst',
            '顾问', '经理', '总监', '专家', '工程师', '分析师',
            'implementation', 'project', 'senior', 'junior', 'lead', 'head'
        ]

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                if current_exp and exp_buffer:
                    # 收集描述行
                    current_exp.description += '\n'.join(exp_buffer)
                    exp_buffer = []
                continue

            # 检查是否是职位标题行
            line_lower = line.lower()
            has_job_indicator = any(ind in line_lower for ind in job_indicators)

            # 检查是否有时间范围
            has_date = bool(re.search(r'\d{4}', line) and any(
                sep in line for sep in ['-', '–', '~', '/']
            ))

            if has_job_indicator and (has_date or len(line) < 60):
                # 保存之前的经历
                if current_exp:
                    current_exp.description = '\n'.join(exp_buffer)
                    experiences.append(current_exp)
                    exp_buffer = []

                # 解析新职位
                current_exp = self._parse_experience_line(line)
            elif current_exp and len(line) > 20:
                # 作为描述行收集
                exp_buffer.append(line)

        # 保存最后一个
        if current_exp:
            current_exp.description = '\n'.join(exp_buffer)
            experiences.append(current_exp)

        # 如果没找到，尝试全文匹配
        if not experiences:
            experiences = self._extract_experiences_fallback(text)

        return experiences

    def _parse_experience_line(self, line: str) -> WorkExperience:
        """解析单行工作经历"""
        exp = WorkExperience(title="", company="", duration="")

        # 提取职位
        title_match = re.search(
            r'(?:^|\s)([\w\s\+\#]+?(?:consultant|manager|director|specialist|engineer|analyst|顾问|经理|总监|专家))',
            line, re.IGNORECASE
        )
        if title_match:
            exp.title = title_match.group(1).strip()

        # 提取公司
        company_patterns = [
            r'(?:at|@|\||·|,)\s*([A-Z][\w\s&]+?(?:Inc|Ltd|LLC|Corp|Solutions|Global|Technologies|Consulting)?)',
            r'([\u4e00-\u9fff]{2,20}(?:公司|集团|企业))',
        ]
        for pattern in company_patterns:
            match = re.search(pattern, line)
            if match:
                exp.company = match.group(1).strip()
                break

        # 提取时间
        date_match = re.search(
            r'(\w+\s*\d{4}\s*[-–~]\s*(?:\w+\s*\d{4}|Now|present|Present|现在))',
            line, re.IGNORECASE
        )
        if date_match:
            exp.duration = date_match.group(1).strip()
            # 提取起止日期
            dates = re.findall(r'(\w+\s*\d{4}|\d{4})', date_match.group(1))
            if len(dates) >= 2:
                exp.start_date = dates[0]
                exp.end_date = dates[1]
            elif len(dates) == 1:
                exp.start_date = dates[0]

        return exp

    def _extract_experiences_fallback(self, text: str) -> List[WorkExperience]:
        """备用方案：全文匹配工作经历"""
        experiences = []

        # 查找年份模式来识别工作时间段
        year_pattern = r'(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|一月|二月|三月|四月|五月|六月|七月|八月|九月|十月|十一月|十二月)[\s,]*)?(19|20)\d{2}\s*[-–~至]\s*(?:(19|20)\d{2}|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|一月|二月|三月|四月|五月|六月|七月|八月|九月|十月|十一月|十二月|现在|now|present)|(?:(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|一月|二月|三月|四月|五月|六月|七月|八月|九月|十月|十一月|十二月)\s*\d{4}))'
        matches = list(re.finditer(year_pattern, text, re.IGNORECASE))

        for i, match in enumerate(matches):
            start = match.start()
            end = matches[i + 1].start() if i + 1 < len(matches) else min(start + 500, len(text))

            segment = text[start:end]
            lines = [l.strip() for l in segment.split('\n') if l.strip()]

            exp = WorkExperience(
                title=lines[0] if lines else "",
                company="",
                duration=match.group(0)
            )

            # 提取技能
            exp.skills_used = [s for s in self._extract_skills(segment) if s]
            exp.description = ' '.join(lines[1:4]) if len(lines) > 1 else ""

            experiences.append(exp)

        return experiences[:5]  # 最多5段经历

    def _calculate_total_years(self, experiences: List[WorkExperience]) -> int:
        """计算总工作年限"""
        total = 0
        for exp in experiences:
            if exp.start_date and exp.end_date:
                try:
                    # 尝试提取年份
                    years = re.findall(r'(?:20|19)\d{2}', f"{exp.start_date} {exp.end_date}")
                    if len(years) >= 2:
                        total += int(years[-1]) - int(years[0])
                    elif len(years) == 1:
                        total += 1
                except:
                    pass
        return max(total, len(experiences))  # 至少有工作经历数作为兜底

    def _extract_education(self, text: str) -> List[Education]:
        """提取教育背景"""
        education = []

        degree_keywords = {
            '博士': ['phd', 'doctor', '博士', 'ph.d', 'd.phil'],
            '硕士': ['master', 'mba', 'msc', 'ma', 'm.sc', '硕士', 'mba'],
            '学士': ['bachelor', 'bsc', 'bs', 'b.sc', 'bachelor', '本科', '学士'],
            '大专': ['associate', 'college', '大专', '专科'],
        }

        school_patterns = [
            r'([A-Z][\w\s&]+?(?:University|College|Institute|School|Højskole|Universitet))',
            r'([\u4e00-\u9fff]{2,15}(?:大学|学院|学校|研究院))',
        ]

        lines = text.split('\n')
        edu_buffer = []

        for line in lines:
            line_lower = line.lower()
            if any(kw in line_lower for kw in ['education', 'academic', '学历', '教育']):
                continue

            has_degree = any(
                kw in line_lower
                for kws in degree_keywords.values()
                for kw in kws
            )

            has_school = any(re.search(p, line, re.IGNORECASE) for p in school_patterns)

            if has_degree or has_school:
                edu = Education(degree="", school="")
                for deg, kws in degree_keywords.items():
                    for kw in kws:
                        if kw in line_lower:
                            edu.degree = deg
                            break
                for p in school_patterns:
                    m = re.search(p, line, re.IGNORECASE)
                    if m:
                        edu.school = m.group(1).strip()
                        break
                year_m = re.search(r'(19|20)\d{2}', line)
                if year_m:
                    edu.graduation_year = year_m.group(0)
                education.append(edu)

        return education[:3]  # 最多3段教育

    def _extract_certificates(self, text: str) -> List[Certificate]:
        """提取证书"""
        cert_keywords = [
            'certified', 'certification', 'certificate', '认证', '证书',
            'pmp', 'cpa', 'cfa', 'acca', 'cma', 'pmi',
            'oracle certified', 'microsoft certified', 'sap certified',
            'netSuite certified', 'd365 certified'
        ]

        certificates = []
        text_lower = text.lower()

        for kw in cert_keywords:
            if kw in text_lower:
                cert = Certificate(name="")
                # 尝试扩展提取完整证书名
                idx = text_lower.find(kw)
                snippet = text[max(0, idx-10):idx+40]
                lines = snippet.split('\n')
                cert.name = lines[0].strip() if lines else kw.title()
                certificates.append(cert)

        return certificates

    def _extract_languages(self, text: str) -> List[str]:
        """提取语言能力"""
        languages = []
        lang_indicators = [
            ('英语', ['english', 'engelsk']),
            ('丹麦语', ['dansk', 'danish']),
            ('德语', ['german', 'deutsch']),
            ('中文', ['mandarin', 'chinese', '中文', '普通话']),
            ('法语', ['french', 'français']),
            ('瑞典语', ['swedish', 'svenska']),
            ('挪威语', ['norwegian', 'norsk']),
        ]

        text_lower = text.lower()
        for lang_name, keywords in lang_indicators:
            if any(kw in text_lower for kw in keywords):
                languages.append(lang_name)

        return languages

    def _extract_summary(self, text: str) -> str:
        """提取个人简介"""
        summary_patterns = [
            r'(?:summary|profile|about|概述|简介|个人)[:\s]*(.{50,300}?)(?:\n\n|\n[A-Z]|$)',
            r'^([\u4e00-\u9fff]{20,100})',
        ]

        for pattern in summary_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
            if match:
                return match.group(1).strip()[:200]

        return ""


# ============================================================
# 简历-职位匹配引擎
# ============================================================

class ResumeJobMatcher:
    """简历与职位的智能匹配"""

    def __init__(self):
        self.extractor = ResumeExtractor()

    def match(self, resume_text: str, job: Dict) -> MatchResult:
        """将简历与职位进行匹配"""
        # 1. 提取简历画像
        profile = self.extractor.extract(resume_text)

        # 2. 解析职位要求
        job_req = self._parse_job_requirements(job)

        # 3. 计算技能匹配度
        skill_result = self._match_skills(profile.skills, job_req)

        # 4. 计算经验匹配度
        exp_result = self._match_experience(profile, job_req)

        # 5. 综合评分
        overall = (skill_result['rate'] * 0.6 + exp_result['rate'] * 0.4)

        # 6. 生成建议
        suggestions = self._generate_suggestions(profile, job_req, skill_result)

        return MatchResult(
            overall_score=round(overall, 1),
            skill_match_rate=round(skill_result['rate'], 1),
            experience_match_rate=round(exp_result['rate'], 1),
            matched_skills=skill_result['matched'],
            missing_skills=skill_result['missing'],
            partial_skills=skill_result['partial'],
            gap_analysis=exp_result['gaps'],
            suggestions=suggestions,
            strengths=skill_result['matched'][:5]
        )

    def _parse_job_requirements(self, job: Dict) -> JobRequirement:
        """从职位信息解析职位要求"""
        desc = job.get('description', '') + ' ' + job.get('title', '')

        # 提取技能关键词
        extractor = ResumeExtractor()
        skills = extractor._extract_skills(desc)

        # 提取年限要求
        year_match = re.search(r'(\d+)\+?\s*(?:years?|års?|年)', desc, re.IGNORECASE)
        years = int(year_match.group(1)) if year_match else 0

        return JobRequirement(
            title=job.get('title', ''),
            company=job.get('company', ''),
            required_skills=skills[:8],  # 取前8个作为必须
            preferred_skills=skills[8:],  # 其余作为加分项
            required_years=years,
            description=desc
        )

    def _match_skills(self, resume_skills: List[str], job_req: JobRequirement) -> Dict:
        """匹配技能"""
        resume_set = {s.lower() for s in resume_skills}
        required_set = {s.lower() for s in job_req.required_skills}
        preferred_set = {s.lower() for s in job_req.preferred_skills}
        all_job_set = required_set | preferred_set

        matched = []
        missing = []
        partial = []

        for skill in all_job_set:
            if skill in resume_set:
                matched.append(skill)
            else:
                # 检查部分匹配
                found_partial = False
                for r_skill in resume_set:
                    if skill in r_skill or r_skill in skill:
                        partial.append(f"{r_skill} ≈ {skill}")
                        found_partial = True
                        break
                if not found_partial:
                    missing.append(skill)

        # 计算匹配率
        if all_job_set:
            match_rate = len(matched) / len(all_job_set) * 100
            match_rate += len(partial) / len(all_job_set) * 50  # 部分匹配得50%
        else:
            match_rate = 50

        return {
            'matched': matched,
            'missing': missing,
            'partial': partial,
            'rate': min(match_rate, 100)
        }

    def _match_experience(self, profile: ResumeProfile, job_req: JobRequirement) -> Dict:
        """匹配经验"""
        gaps = []

        # 年限匹配
        if job_req.required_years > 0:
            if profile.total_years >= job_req.required_years:
                gaps.append(f"✅ 工作经验 {profile.total_years}年 >= 要求 {job_req.required_years}年")
            else:
                gaps.append(f"⚠️ 工作经验 {profile.total_years}年 < 要求 {job_req.required_years}年（差 {job_req.required_years - profile.total_years} 年）")

        # 行业匹配检查
        exp_text = ' '.join([e.title + ' ' + e.description for e in profile.work_experiences]).lower()
        if job_req.title:
            title_lower = job_req.title.lower()
            if any(kw in exp_text for kw in ['consultant', 'erp', 'dynamics', 'netsuite', 'sap']):
                gaps.append("✅ 有ERP/咨询相关经验")
            else:
                gaps.append("⚠️ 缺乏直接相关的项目/咨询经验")

        # 计算经验匹配率
        rate = 70  # 基础分
        if profile.total_years >= job_req.required_years:
            rate += 15
        if any('erp' in s.lower() or 'dynamics' in s.lower() or 'netsuite' in s.lower()
               for s in profile.skills):
            rate += 15

        return {
            'rate': min(rate, 100),
            'gaps': gaps
        }

    def _generate_suggestions(self, profile: ResumeProfile, job_req: JobRequirement,
                               skill_result: Dict) -> List[str]:
        """生成简历优化建议"""
        suggestions = []

        # 缺失技能建议
        if skill_result['missing']:
            top_missing = skill_result['missing'][:3]
            suggestions.append(
                f"📚 建议补充技能：{', '.join(top_missing)}"
            )

        # 关键词优化
        if skill_result['matched']:
            suggestions.append(
                f"✅ 简历中已具备的优势技能：{', '.join(skill_result['matched'][:5])}"
            )

        # 经验描述优化
        if profile.work_experiences:
            latest_exp = profile.work_experiences[0]
            desc_lower = latest_exp.description.lower()
            strong_verbs_en = self.extractor.STRONG_VERBS.get('en', [])

            if not any(v in desc_lower for v in strong_verbs_en):
                suggestions.append(
                    "💡 建议：将工作描述中的动词替换为更有力的词汇（如：'Led'、'Achieved'、'Optimized'）"
                )

        # 针对NetSuite/Dynamics的特定建议
        if 'NetSuite' in job_req.required_skills:
            if 'NetSuite' not in profile.skills and 'Oracle' in profile.skills:
                suggestions.append(
                    "💡 您有Oracle经验，建议在简历中强调与NetSuite的关联性"
                )

        if not suggestions:
            suggestions.append("✅ 简历与职位匹配度良好，建议直接申请！")

        return suggestions


# ============================================================
# 批量职位匹配
# ============================================================

class BatchJobMatcher:
    """批量职位匹配器"""

    def __init__(self):
        self.matcher = ResumeJobMatcher()

    def rank_jobs(self, resume_text: str, jobs: List[Dict],
                   min_score: float = 50.0) -> List[Dict]:
        """对多个职位进行匹配排序"""
        results = []

        for job in jobs:
            try:
                match_result = self.matcher.match(resume_text, job)
                result = {
                    **job,
                    'match_score': match_result.overall_score,
                    'skill_match': match_result.skill_match_rate,
                    'experience_match': match_result.experience_match_rate,
                    'matched_skills': match_result.matched_skills,
                    'missing_skills': match_result.missing_skills,
                    'gap_analysis': match_result.gap_analysis,
                    'suggestions': match_result.suggestions
                }
                results.append(result)
            except Exception as e:
                print(f"匹配职位 '{job.get('title', 'Unknown')}' 时出错: {e}")

        # 按匹配分数排序
        results.sort(key=lambda x: x.get('match_score', 0), reverse=True)

        # 过滤低于最低分的职位
        return [r for r in results if r.get('match_score', 0) >= min_score]
