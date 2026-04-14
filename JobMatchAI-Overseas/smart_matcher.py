"""
JobMatchAI Nordic - 智能职位匹配系统
核心功能：
1. 用户画像管理 - 持续学习用户技能和偏好
2. 职位智能匹配 - 根据用户画像给职位打分
3. 自动筛选推送 - 只推送高匹配度职位

Copyright © 2026 JobMatchAI. All rights reserved.
"""
import json
import re
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict, field
import hashlib


@dataclass
class ResumeHistoryEntry:
    """简历版本历史条目"""
    version: int
    timestamp: str
    resume_text: str  # 简历文本（完整）
    polish_summary: str  # 精修总结
    job_context: str  # 针对的职位
    match_score: float  # 当时的匹配评分
    skill_gaps: List[str]  # 当时的Skill Gap

@dataclass
class SkillGapEntry:
    """Skill Gap历史记录"""
    timestamp: str
    job_title: str
    job_description: str
    resume_skills: List[str]
    required_skills: List[str]
    missing_skills: List[str]
    match_score: float
    learning_recommendations: List[Dict]  # [{skill, resource_url, status}]

@dataclass  
class ApplicationEntry:
    """申请历史条目"""
    timestamp: str
    job_title: str
    company: str
    cover_letter: str
    application_status: str  # pending/sent/interview/rejected/offer
    interview_count: int = 0
    notes: str = ""

@dataclass
class LearningRecord:
    """学习资源浏览/完成记录"""
    timestamp: str
    skill: str
    resource_title: str
    resource_url: str
    status: str  # viewed/completed/bookmarked
    completion_percent: int = 0

@dataclass
class UserProfile:
    """用户画像 - 持续学习更新"""
    # 基础信息
    user_id: str
    created_at: str
    updated_at: str
    
    # 技能画像（带权重 0-1）
    skills: Dict[str, float]  # {"Python": 0.9, "ERP": 0.95, ...}
    
    # 经验信息
    total_years: int
    industries: List[str]  # 行业经验
    roles: List[str]  # 职位类型
    
    # 偏好设置
    preferred_locations: List[str]  # 偏好地点
    preferred_languages: List[str]  # 偏好语言
    min_salary: Optional[int] = None
    max_salary: Optional[int] = None
    
    # 行为数据（用于学习）
    viewed_jobs: List[str] = field(default_factory=list)  # 浏览过的职位ID
    saved_jobs: List[str] = field(default_factory=list)  # 收藏的职位
    applied_jobs: List[str] = field(default_factory=list)  # 申请过的职位
    ignored_jobs: List[str] = field(default_factory=list)  # 忽略/不感兴趣的职位
    
    # 学习到的关键词
    positive_keywords: List[str] = field(default_factory=list)  # 用户感兴趣的词
    negative_keywords: List[str] = field(default_factory=list)  # 用户不感兴趣的词
    
    # ========== 新增：用户粘性增强功能 ==========
    # 简历版本历史
    resume_history: List[Dict] = field(default_factory=list)
    
    # Skill Gap历史追踪
    skill_gap_history: List[Dict] = field(default_factory=list)
    
    # 申请历史
    application_history: List[Dict] = field(default_factory=list)
    
    # 学习记录
    learning_history: List[Dict] = field(default_factory=list)
    
    # 目标职位类型（用于个性化推荐）
    target_job_types: List[str] = field(default_factory=list)
    
    # 最近一次分析时间
    last_analysis_at: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'UserProfile':
        # 过滤掉不存在的字段（向后兼容）
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)


class UserProfileManager:
    """用户画像管理器 - 负责CRUD和持续学习"""
    
    def __init__(self, storage_dir: str = "./user_profiles"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
    
    def _get_profile_path(self, user_id: str) -> str:
        return os.path.join(self.storage_dir, f"{user_id}.json")
    
    def create_profile(self, user_id: str, initial_resume: str = "") -> UserProfile:
        """从简历创建初始用户画像"""
        # 解析简历提取初始信息
        skills = self._extract_skills_from_resume(initial_resume)
        years = self._extract_experience_years(initial_resume)
        industries = self._extract_industries(initial_resume)
        roles = self._extract_roles(initial_resume)
        
        profile = UserProfile(
            user_id=user_id,
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat(),
            skills=skills,
            total_years=years,
            industries=industries,
            roles=roles,
            preferred_locations=[],
            preferred_languages=[],
            viewed_jobs=[],
            saved_jobs=[],
            applied_jobs=[],
            ignored_jobs=[],
            positive_keywords=[],
            negative_keywords=[],
            resume_history=[],
            skill_gap_history=[],
            application_history=[],
            learning_history=[],
            target_job_types=[],
            last_analysis_at=None
        )
        
        self._save_profile(profile)
        return profile
    
    def get_profile(self, user_id: str) -> Optional[UserProfile]:
        """获取用户画像"""
        path = self._get_profile_path(user_id)
        if not os.path.exists(path):
            return None
        
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return UserProfile.from_dict(data)
    
    def _save_profile(self, profile: UserProfile):
        """保存用户画像"""
        path = self._get_profile_path(profile.user_id)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(profile.to_dict(), f, ensure_ascii=False, indent=2)
    
    def update_profile_from_resume(self, user_id: str, resume_text: str) -> UserProfile:
        """根据更新的简历刷新用户画像"""
        profile = self.get_profile(user_id)
        if not profile:
            return self.create_profile(user_id, resume_text)
        
        # 合并新旧技能（新技能权重稍低，表示需要验证）
        new_skills = self._extract_skills_from_resume(resume_text)
        for skill, weight in new_skills.items():
            if skill in profile.skills:
                # 已存在的技能，权重微调
                profile.skills[skill] = min(1.0, profile.skills[skill] + 0.05)
            else:
                # 新技能，初始权重0.7
                profile.skills[skill] = 0.7
        
        # 更新其他信息
        profile.total_years = self._extract_experience_years(resume_text)
        profile.industries = list(set(profile.industries + self._extract_industries(resume_text)))
        profile.roles = list(set(profile.roles + self._extract_roles(resume_text)))
        profile.updated_at = datetime.now().isoformat()
        
        self._save_profile(profile)
        return profile
    
    def learn_from_job_action(self, user_id: str, job: Dict, action: str):
        """
        根据用户对职位的操作学习偏好
        action: 'view', 'save', 'apply', 'ignore', 'reject'
        """
        profile = self.get_profile(user_id)
        if not profile:
            return
        
        job_id = job.get('id') or self._generate_job_id(job)
        job_text = f"{job.get('title', '')} {job.get('description', '')}"
        
        # 记录行为
        if action == 'view':
            if job_id not in profile.viewed_jobs:
                profile.viewed_jobs.append(job_id)
        elif action == 'save':
            if job_id not in profile.saved_jobs:
                profile.saved_jobs.append(job_id)
            # 从职位提取正向关键词
            keywords = self._extract_keywords(job_text)
            for kw in keywords:
                if kw not in profile.positive_keywords:
                    profile.positive_keywords.append(kw)
        elif action == 'apply':
            if job_id not in profile.applied_jobs:
                profile.applied_jobs.append(job_id)
            # 申请表示高度匹配，提升相关技能权重
            self._boost_related_skills(profile, job_text)
        elif action in ['ignore', 'reject']:
            if job_id not in profile.ignored_jobs:
                profile.ignored_jobs.append(job_id)
            # 提取负向关键词
            keywords = self._extract_keywords(job_text)
            for kw in keywords:
                if kw not in profile.negative_keywords:
                    profile.negative_keywords.append(kw)
        
        profile.updated_at = datetime.now().isoformat()
        self._save_profile(profile)
    
    def _boost_related_skills(self, profile: UserProfile, job_text: str):
        """提升与职位相关的技能权重"""
        job_lower = job_text.lower()
        for skill in list(profile.skills.keys()):
            if skill.lower() in job_lower:
                profile.skills[skill] = min(1.0, profile.skills[skill] + 0.1)
    
    # === 简历解析辅助方法 ===
    
    def _extract_skills_from_resume(self, text: str) -> Dict[str, float]:
        """从简历提取技能及初始权重"""
        skills = {}
        text_lower = text.lower()
        
        # 技能库（中英丹）
        skill_patterns = {
            # 技术技能
            'python': 0.9, 'java': 0.9, 'javascript': 0.9, 'sql': 0.9,
            'netsuite': 0.95, 'dynamics': 0.95, 'erp': 0.95, 'sap': 0.9,
            'aws': 0.85, 'azure': 0.85, 'docker': 0.8, 'kubernetes': 0.8,
            
            # 业务技能
            'project management': 0.85, 'projektledelse': 0.85, '项目管理': 0.85,
            'data analysis': 0.85, 'dataanalyse': 0.85, '数据分析': 0.85,
            'supply chain': 0.85, 'forsyningskæde': 0.85, '供应链': 0.85,
            'finance': 0.85, 'finans': 0.85, '财务': 0.85,
            
            # 软技能
            'leadership': 0.8, 'lederskab': 0.8, '领导力': 0.8,
            'communication': 0.8, 'kommunikation': 0.8, '沟通': 0.8,
        }
        
        for skill, base_weight in skill_patterns.items():
            if skill in text_lower:
                # 根据提及次数调整权重
                count = text_lower.count(skill)
                weight = min(1.0, base_weight + (count - 1) * 0.05)
                skills[skill.title()] = weight
        
        return skills
    
    def _extract_experience_years(self, text: str) -> int:
        """提取工作年限"""
        # 匹配 "5年", "5 years", "5 år"
        patterns = [
            r'(\d+)\s*年',
            r'(\d+)\s*years?',
            r'(\d+)\s*år',
        ]
        
        years = []
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            years.extend([int(m) for m in matches])
        
        return max(years) if years else 0
    
    def _extract_industries(self, text: str) -> List[str]:
        """提取行业经验"""
        industries = []
        text_lower = text.lower()
        
        industry_keywords = [
            'manufacturing', 'manufacturing', '制造业',
            'retail', 'detailhandel', '零售',
            'finance', 'finans', '金融',
            'healthcare', 'sundhed', '医疗',
            'technology', 'teknologi', '科技',
            'consulting', 'rådgivning', '咨询',
        ]
        
        for industry in industry_keywords:
            if industry in text_lower:
                industries.append(industry.title())
        
        return industries
    
    def _extract_roles(self, text: str) -> List[str]:
        """提取职位类型"""
        roles = []
        text_lower = text.lower()
        
        role_patterns = [
            'consultant', 'konsulent', '顾问',
            'manager', 'leder', '经理',
            'developer', 'udvikler', '开发',
            'analyst', 'analytiker', '分析师',
            'specialist', 'specialist', '专员',
        ]
        
        for role in role_patterns:
            if role in text_lower:
                roles.append(role.title())
        
        return roles
    
    def _extract_keywords(self, text: str) -> List[str]:
        """提取关键词"""
        # 简单的关键词提取（可以改进为TF-IDF或NER）
        words = re.findall(r'\b[A-Za-zÆØÅæøå]{4,}\b', text)
        # 过滤常见词
        stopwords = {'this', 'that', 'with', 'from', 'have', 'been', 'their', 'will'}
        keywords = [w for w in words if w.lower() not in stopwords]
        # 返回前10个
        return list(set(keywords))[:10]
    
    def _generate_job_id(self, job: Dict) -> str:
        """生成职位唯一ID"""
        content = f"{job.get('title', '')}{job.get('company', '')}{job.get('description', '')[:100]}"
        return hashlib.md5(content.encode()).hexdigest()[:12]
    
    # ========== 用户粘性增强功能 ==========
    
    def add_resume_history(self, user_id: str, resume_text: str, polish_summary: str, 
                          job_context: str, match_score: float, skill_gaps: List[str]) -> UserProfile:
        """添加简历版本到历史记录"""
        profile = self.get_profile(user_id)
        if not profile:
            profile = self.create_profile(user_id)
        
        # 计算版本号
        version = len(profile.resume_history) + 1
        
        entry = {
            'version': version,
            'timestamp': datetime.now().isoformat(),
            'resume_text': resume_text[:500] if resume_text else "",  # 保存前500字符
            'polish_summary': polish_summary,
            'job_context': job_context,
            'match_score': match_score,
            'skill_gaps': skill_gaps
        }
        
        profile.resume_history.append(entry)
        # 只保留最近10个版本
        if len(profile.resume_history) > 10:
            profile.resume_history = profile.resume_history[-10:]
        
        profile.last_analysis_at = datetime.now().isoformat()
        profile.updated_at = datetime.now().isoformat()
        self._save_profile(profile)
        
        return profile
    
    def add_skill_gap(self, user_id: str, job_title: str, job_description: str,
                     resume_skills: List[str], required_skills: List[str],
                     missing_skills: List[str], match_score: float,
                     learning_recommendations: List[Dict]) -> UserProfile:
        """记录Skill Gap分析结果"""
        profile = self.get_profile(user_id)
        if not profile:
            profile = self.create_profile(user_id)
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'job_title': job_title,
            'job_description': job_description[:200] if job_description else "",
            'resume_skills': resume_skills,
            'required_skills': required_skills,
            'missing_skills': missing_skills,
            'match_score': match_score,
            'learning_recommendations': learning_recommendations
        }
        
        profile.skill_gap_history.append(entry)
        # 只保留最近20条记录
        if len(profile.skill_gap_history) > 20:
            profile.skill_gap_history = profile.skill_gap_history[-20:]
        
        # 更新目标职位类型
        if job_title and job_title not in profile.target_job_types:
            profile.target_job_types.append(job_title)
        
        profile.updated_at = datetime.now().isoformat()
        self._save_profile(profile)
        
        return profile
    
    def add_application(self, user_id: str, job_title: str, company: str,
                        cover_letter: str, application_status: str = "sent") -> UserProfile:
        """记录申请历史"""
        profile = self.get_profile(user_id)
        if not profile:
            profile = self.create_profile(user_id)
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'job_title': job_title,
            'company': company,
            'cover_letter': cover_letter[:500] if cover_letter else "",  # 保存前500字符
            'application_status': application_status,
            'interview_count': 0,
            'notes': ''
        }
        
        profile.application_history.append(entry)
        # 只保留最近50条记录
        if len(profile.application_history) > 50:
            profile.application_history = profile.application_history[-50:]
        
        profile.updated_at = datetime.now().isoformat()
        self._save_profile(profile)
        
        return profile
    
    def update_application_status(self, user_id: str, index: int, status: str, 
                                  interview_count: int = None, notes: str = None) -> UserProfile:
        """更新申请状态"""
        profile = self.get_profile(user_id)
        if not profile or index >= len(profile.application_history):
            return profile
        
        profile.application_history[index]['application_status'] = status
        if interview_count is not None:
            profile.application_history[index]['interview_count'] = interview_count
        if notes is not None:
            profile.application_history[index]['notes'] = notes
        
        profile.updated_at = datetime.now().isoformat()
        self._save_profile(profile)
        
        return profile
    
    def add_learning_record(self, user_id: str, skill: str, resource_title: str,
                           resource_url: str, status: str = "viewed",
                           completion_percent: int = 0) -> UserProfile:
        """记录学习资源浏览/完成"""
        profile = self.get_profile(user_id)
        if not profile:
            profile = self.create_profile(user_id)
        
        entry = {
            'timestamp': datetime.now().isoformat(),
            'skill': skill,
            'resource_title': resource_title,
            'resource_url': resource_url,
            'status': status,
            'completion_percent': completion_percent
        }
        
        profile.learning_history.append(entry)
        # 只保留最近100条记录
        if len(profile.learning_history) > 100:
            profile.learning_history = profile.learning_history[-100:]
        
        profile.updated_at = datetime.now().isoformat()
        self._save_profile(profile)
        
        return profile
    
    def get_profile_summary(self, user_id: str) -> Dict:
        """获取用户画像摘要（用于前端展示）"""
        profile = self.get_profile(user_id)
        if not profile:
            return {'exists': False}
        
        # 计算Skill Gap改进趋势
        gap_trend = []
        if len(profile.skill_gap_history) >= 2:
            recent_gaps = profile.skill_gap_history[-3:]
            for gap in recent_gaps:
                gap_trend.append({
                    'timestamp': gap['timestamp'],
                    'job_title': gap['job_title'],
                    'match_score': gap['match_score'],
                    'missing_skills_count': len(gap.get('missing_skills', []))
                })
        
        # 计算申请成功率
        total_applications = len(profile.application_history)
        interviews = sum(1 for a in profile.application_history if a.get('interview_count', 0) > 0)
        interview_rate = (interviews / total_applications * 100) if total_applications > 0 else 0
        
        return {
            'exists': True,
            'user_id': profile.user_id,
            'created_at': profile.created_at,
            'updated_at': profile.updated_at,
            'skills_count': len(profile.skills),
            'top_skills': list(profile.skills.keys())[:5],
            'resume_versions': len(profile.resume_history),
            'latest_match_score': profile.resume_history[-1]['match_score'] if profile.resume_history else None,
            'gap_trend': gap_trend,
            'total_applications': total_applications,
            'interview_rate': round(interview_rate, 1),
            'learning_completed': sum(1 for l in profile.learning_history if l.get('status') == 'completed'),
            'target_jobs': profile.target_job_types[-5:],  # 最近5个目标职位
            'last_analysis_at': profile.last_analysis_at
        }


class SmartJobMatcher:
    """智能职位匹配器 - 根据用户画像给职位打分"""
    
    def __init__(self, profile_manager: UserProfileManager):
        self.profile_manager = profile_manager
    
    def calculate_match_score(self, user_id: str, job: Dict) -> Tuple[float, Dict]:
        """
        计算职位匹配度分数 (0-100)
        返回：(分数, 匹配详情)
        """
        profile = self.profile_manager.get_profile(user_id)
        if not profile:
            return 0.0, {"error": "User profile not found"}
        
        job_text = f"{job.get('title', '')} {job.get('description', '')}".lower()
        job_id = job.get('id') or self._generate_job_id(job)
        
        # 如果用户之前忽略过这个职位，直接返回低分
        if job_id in profile.ignored_jobs:
            return 5.0, {"reason": "Previously ignored"}
        
        scores = {}
        
        # 1. 技能匹配度 (40分)
        skill_score = self._calculate_skill_match(profile, job_text)
        scores['skills'] = skill_score * 40
        
        # 2. 经验匹配度 (20分)
        exp_score = self._calculate_experience_match(profile, job_text)
        scores['experience'] = exp_score * 20
        
        # 3. 地点匹配度 (15分)
        location_score = self._calculate_location_match(profile, job)
        scores['location'] = location_score * 15
        
        # 4. 语言匹配度 (10分)
        lang_score = self._calculate_language_match(profile, job)
        scores['language'] = lang_score * 10
        
        # 5. 关键词匹配度 (15分)
        keyword_score = self._calculate_keyword_match(profile, job_text)
        scores['keywords'] = keyword_score * 15
        
        # 总分
        total_score = sum(scores.values())
        
        # 生成匹配理由
        match_reasons = self._generate_match_reasons(scores, profile, job)
        
        return total_score, {
            'total_score': round(total_score, 1),
            'breakdown': {k: round(v, 1) for k, v in scores.items()},
            'reasons': match_reasons,
            'job_id': job_id
        }
    
    def _calculate_skill_match(self, profile: UserProfile, job_text: str) -> float:
        """计算技能匹配度 (0-1)"""
        if not profile.skills:
            return 0.5
        
        matched_weight = 0
        total_weight = 0
        
        for skill, weight in profile.skills.items():
            total_weight += weight
            if skill.lower() in job_text:
                matched_weight += weight
        
        return matched_weight / total_weight if total_weight > 0 else 0
    
    def _calculate_experience_match(self, profile: UserProfile, job_text: str) -> float:
        """计算经验匹配度"""
        # 提取职位要求的工作年限
        patterns = [
            r'(\d+)\+?\s*years?\s*(?:of\s*)?experience',
            r'(\d+)\+?\s*år\s*erfaring',
            r'(\d+)\+?\s*年\s*经验',
        ]
        
        required_years = None
        for pattern in patterns:
            match = re.search(pattern, job_text)
            if match:
                required_years = int(match.group(1))
                break
        
        if required_years is None:
            return 0.8  # 没有明确要求，默认匹配
        
        if profile.total_years >= required_years:
            return 1.0
        elif profile.total_years >= required_years * 0.8:
            return 0.8
        elif profile.total_years >= required_years * 0.5:
            return 0.5
        else:
            return 0.2
    
    def _calculate_location_match(self, profile: UserProfile, job: Dict) -> float:
        """计算地点匹配度"""
        job_location = job.get('location', '').lower()
        
        if not profile.preferred_locations:
            return 0.7  # 没有偏好，默认中等匹配
        
        for pref_loc in profile.preferred_locations:
            if pref_loc.lower() in job_location:
                return 1.0
        
        return 0.3
    
    def _calculate_language_match(self, profile: UserProfile, job: Dict) -> float:
        """计算语言匹配度"""
        job_lang = job.get('language', 'en')
        
        if not profile.preferred_languages:
            return 0.7
        
        if job_lang in profile.preferred_languages:
            return 1.0
        
        return 0.4
    
    def _calculate_keyword_match(self, profile: UserProfile, job_text: str) -> float:
        """计算关键词匹配度"""
        if not profile.positive_keywords:
            return 0.5
        
        positive_matches = sum(1 for kw in profile.positive_keywords if kw.lower() in job_text)
        negative_matches = sum(1 for kw in profile.negative_keywords if kw.lower() in job_text)
        
        score = positive_matches / max(len(profile.positive_keywords), 1)
        score -= negative_matches * 0.1  # 负向关键词扣分
        
        return max(0, min(1, score))
    
    def _generate_match_reasons(self, scores: Dict, profile: UserProfile, job: Dict) -> List[str]:
        """生成匹配理由（给用户看）"""
        reasons = []
        
        if scores['skills'] > 30:
            matched_skills = [s for s in profile.skills if s.lower() in job.get('description', '').lower()][:3]
            if matched_skills:
                reasons.append(f"✅ 技能高度匹配: {', '.join(matched_skills)}")
        
        if scores['experience'] > 15:
            reasons.append(f"✅ 经验匹配: 您有{profile.total_years}年相关经验")
        
        if scores['location'] > 10:
            reasons.append(f"✅ 地点匹配: {job.get('location', '')}")
        
        return reasons
    
    def filter_and_rank_jobs(self, user_id: str, jobs: List[Dict], min_score: float = 60.0) -> List[Dict]:
        """
        筛选并排序职位
        返回：按匹配度排序的职位列表（只返回高于min_score的）
        """
        scored_jobs = []
        
        for job in jobs:
            score, details = self.calculate_match_score(user_id, job)
            if score >= min_score:
                job['match_score'] = score
                job['match_details'] = details
                scored_jobs.append(job)
        
        # 按匹配度排序
        scored_jobs.sort(key=lambda x: x['match_score'], reverse=True)
        
        return scored_jobs
    
    def _generate_job_id(self, job: Dict) -> str:
        """生成职位唯一ID"""
        content = f"{job.get('title', '')}{job.get('company', '')}{job.get('description', '')[:100]}"
        return hashlib.md5(content.encode()).hexdigest()[:12]


class AutoJobProcessor:
    """自动职位处理器 - 定时读取邮件、筛选、推送"""
    
    def __init__(self, profile_manager: UserProfileManager, matcher: SmartJobMatcher):
        self.profile_manager = profile_manager
        self.matcher = matcher
    
    def process_email_jobs(self, user_id: str, email_jobs: List[Dict]) -> Dict:
        """
        处理从邮件读取的职位
        返回：筛选结果报告
        """
        # 1. 智能筛选（只保留匹配度>60分的）
        matched_jobs = self.matcher.filter_and_rank_jobs(user_id, email_jobs, min_score=60.0)
        
        # 2. 分类
        high_match = [j for j in matched_jobs if j['match_score'] >= 80]
        medium_match = [j for j in matched_jobs if 60 <= j['match_score'] < 80]
        
        # 3. 为高分职位预生成求职信
        for job in high_match[:3]:  # 只为前3个高分职位生成
            job['cover_letter_ready'] = True
        
        return {
            'total_received': len(email_jobs),
            'high_match': high_match,
            'medium_match': medium_match,
            'filtered_out': len(email_jobs) - len(matched_jobs),
            'summary': f"收到{len(email_jobs)}个职位，筛选出{len(high_match)}个高度匹配，{len(medium_match)}个中等匹配"
        }
    
    def generate_daily_digest(self, user_id: str, jobs: List[Dict]) -> str:
        """生成每日职位摘要（给用户看）"""
        result = self.process_email_jobs(user_id, jobs)
        
        digest = f"""📬 JobMatchAI 每日职位推送

{result['summary']}

"""
        
        if result['high_match']:
            digest += "🌟 高度匹配职位（推荐立即申请）：\n"
            for i, job in enumerate(result['high_match'][:5], 1):
                digest += f"\n{i}. {job.get('title')} @ {job.get('company')}"
                digest += f"\n   匹配度: {job['match_score']:.0f}%"
                digest += f"\n   地点: {job.get('location', 'N/A')}"
                if job.get('cover_letter_ready'):
                    digest += "\n   ✅ 求职信已准备就绪"
                digest += "\n"
        
        if result['medium_match']:
            digest += "\n📋 中等匹配职位（值得关注）：\n"
            for i, job in enumerate(result['medium_match'][:3], 1):
                digest += f"\n{i}. {job.get('title')} @ {job.get('company')}"
                digest += f"\n   匹配度: {job['match_score']:.0f}%\n"
        
        return digest


# === 使用示例 ===
if __name__ == '__main__':
    # 初始化
    pm = UserProfileManager()
    matcher = SmartJobMatcher(pm)
    processor = AutoJobProcessor(pm, matcher)
    
    # 示例：创建用户画像
    sample_resume = """
    姓名：张伟
    工作经验：8年
    技能：ERP, NetSuite, Dynamics AX, Python, SQL, 项目管理
    行业：制造业, 零售
    """
    
    profile = pm.create_profile("user_001", sample_resume)
    print(f"创建用户画像: {profile.user_id}")
    print(f"技能: {profile.skills}")
    
    # 示例：模拟从邮件读取的职位
    sample_jobs = [
        {
            'title': 'ERP Consultant',
            'company': 'ABC Company',
            'location': 'Copenhagen',
            'description': 'Looking for experienced ERP consultant with NetSuite and Dynamics knowledge. 5+ years experience required.',
            'language': 'en'
        },
        {
            'title': 'Software Developer',
            'company': 'Tech Startup',
            'location': 'Aarhus',
            'description': 'Python developer needed for web applications. 2+ years experience.',
            'language': 'en'
        },
        {
            'title': 'Sales Manager',
            'company': 'Sales Corp',
            'location': 'Odense',
            'description': 'Looking for sales professionals. No technical skills required.',
            'language': 'en'
        }
    ]
    
    # 处理职位
    result = processor.process_email_jobs("user_001", sample_jobs)
    print("\n" + "="*50)
    print(result['summary'])
    
    # 打印详细匹配结果
    for job in result['high_match'] + result['medium_match']:
        print(f"\n📌 {job['title']} @ {job['company']}")
        print(f"   匹配度: {job['match_score']:.1f}%")
        print(f"   详情: {job['match_details']['breakdown']}")
