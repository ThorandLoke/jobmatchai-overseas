"""
JobMatchAI - 智能能力挖掘系统
通过用户行为数据挖掘隐性能力，发现被遗忘的经历

核心功能：
1. 数据收集：邮件、日历、文档、浏览记录
2. 能力挖掘：AI分析行为数据提取隐性技能
3. 遗忘提醒：提醒用户可能被遗忘的项目/培训/证书
4. 简历增强：根据行为数据给出简历优化建议
5. 动态调整：根据申请职位动态优化简历关键词

Copyright © 2026 JobMatchAI. All rights reserved.
"""
import json
import re
import os
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
import hashlib


# === 数据模型 ===

@dataclass
class BehaviorData:
    """用户行为数据"""
    user_id: str
    collected_at: str
    
    # 邮件数据
    email_subjects: List[str] = field(default_factory=list)
    email_sender_domains: List[str] = field(default_factory=list)
    email_keywords: List[str] = field(default_factory=list)
    
    # 日历事件
    calendar_events: List[str] = field(default_factory=list)
    meeting_titles: List[str] = field(default_factory=list)
    
    # 文档/笔记
    document_titles: List[str] = field(default_factory=list)
    notes_keywords: List[str] = field(default_factory=list)
    
    # 其他
    bookmarks: List[str] = field(default_factory=list)
    reading_list: List[str] = field(default_factory=list)


@dataclass
class HiddenSkill:
    """挖掘到的隐性能力"""
    skill_name: str
    confidence: float  # 0-1
    source: str  # "email", "calendar", "document", "bookmarks"
    evidence: List[str]  # 具体证据
    category: str  # "technical", "soft", "domain", "tool"
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class ForgottenExperience:
    """可能被遗忘的经历"""
    title: str
    type: str  # "project", "training", "certification", "course", "award"
    description: str
    confidence: float
    source: str
    suggestion: str  # 如何在简历中体现


@dataclass
class ResumeEnhancement:
    """简历增强建议"""
    hidden_skills: List[HiddenSkill] = field(default_factory=list)
    forgotten_experiences: List[ForgottenExperience] = field(default_factory=list)
    keyword_additions: List[str] = field(default_factory=list)
    keyword_weights: Dict[str, float] = field(default_factory=dict)  # 技能权重调整
    suggestions: List[str] = field(default_factory=list)
    ai_insights: str = ""  # AI综合分析


class BehaviorDataCollector:
    """行为数据收集器"""
    
    def __init__(self, storage_dir: str = "./behavior_data"):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
    
    def _get_data_path(self, user_id: str) -> str:
        return os.path.join(self.storage_dir, f"behavior_{user_id}.json")
    
    def collect_from_email(self, emails: List[Dict]) -> Dict:
        """从邮件收集数据"""
        subjects = []
        sender_domains = []
        keywords = []
        
        keyword_patterns = {
            'project': ['project', 'projekt', 'implementation', 'implementering', 'deployment'],
            'leadership': ['lead', 'leder', 'team', 'managed', 'coordinated'],
            'technical': ['python', 'sql', 'erp', 'sap', 'dynamics', 'api', 'integration'],
            'problem_solving': ['problem', 'issue', 'resolution', 'optimize', 'troubleshoot'],
            'collaboration': ['meeting', 'møde', 'workshop', 'stakeholder', 'client', 'kunde']
        }
        
        for email in emails:
            subject = email.get('subject', '')
            subjects.append(subject)
            
            sender = email.get('from', '')
            if '@' in sender:
                domain = sender.split('@')[-1].split('>')[0]
                sender_domains.append(domain)
            
            subject_lower = subject.lower()
            for category, patterns in keyword_patterns.items():
                if any(p in subject_lower for p in patterns):
                    keywords.append(category)
        
        return {
            'email_subjects': list(set(subjects)),
            'email_sender_domains': list(set(sender_domains)),
            'email_keywords': keywords
        }
    
    def collect_from_calendar(self, events: List[Dict]) -> Dict:
        """从日历收集数据"""
        event_titles = []
        keywords = []
        
        patterns = {
            'training': ['training', 'træning', 'course', 'kursus', 'certification', 'certifikat', 'workshop'],
            'meeting': ['meeting', 'møde', 'standup', 'review', 'sync', '1:1'],
            'project': ['kickoff', 'launch', 'go-live', 'migration', 'update'],
            'presentation': ['presentation', 'præsentation', 'demo', 'showcase']
        }
        
        for event in events:
            title = event.get('title', '') or event.get('summary', '')
            event_titles.append(title)
            
            title_lower = title.lower()
            for category, cats_patterns in patterns.items():
                if any(p in title_lower for p in cats_patterns):
                    keywords.append(category)
        
        return {
            'calendar_events': event_titles,
            'meeting_titles': [e for e in event_titles if any(p in e.lower() for p in ['meeting', 'møde'])]
        }
    
    def collect_from_documents(self, doc_titles: List[str], notes: List[str] = None) -> Dict:
        """从文档收集数据"""
        keywords = []
        
        skill_keywords = {
            'data_analysis': ['analytics', 'analyse', 'dashboard', 'reporting', 'bi'],
            'programming': ['python', 'javascript', 'api', 'sql', 'automation', 'script'],
            'management': ['agile', 'scrum', 'kanban', 'project management', 'stakeholder'],
            'communication': ['presentation', 'documentation', 'training', 'support'],
            'erp_systems': ['netsuite', 'sap', 'dynamics', 'erp', 'oracle', 'crm'],
            'cloud': ['azure', 'aws', 'gcp', 'cloud', 'saas']
        }
        
        all_text = ' '.join(doc_titles + (notes or []))
        all_lower = all_text.lower()
        
        for skill, patterns in skill_keywords.items():
            if any(p in all_lower for p in patterns):
                keywords.append(skill)
        
        return {
            'document_titles': doc_titles,
            'notes_keywords': list(set(keywords))
        }
    
    def save_behavior_data(self, user_id: str, data: BehaviorData):
        """保存行为数据"""
        path = self._get_data_path(user_id)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data.to_dict() if hasattr(data, 'to_dict') else asdict(data), f, ensure_ascii=False, indent=2)
    
    def load_behavior_data(self, user_id: str) -> Optional[BehaviorData]:
        """加载行为数据"""
        path = self._get_data_path(user_id)
        if not os.path.exists(path):
            return None
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return BehaviorData(**data)
    
    def to_dict(self) -> Dict:
        return asdict(self)


class HiddenSkillMiner:
    """隐性能力挖掘器 - AI驱动"""
    
    def __init__(self, ai_client=None):
        self.ai_client = ai_client
    
    def mine_from_emails(self, email_data: Dict, resume_skills: List[str]) -> List[HiddenSkill]:
        """从邮件中挖掘隐性能力"""
        hidden_skills = []
        resume_skills_lower = [s.lower() for s in resume_skills]
        
        # 1. 从邮件主题词分析项目经验
        subjects = email_data.get('email_subjects', [])
        if subjects:
            # 分析是否有简历中未提及的项目关键词
            project_indicators = [
                'implementation', 'migration', 'integration', 'upgrade',
                'deployment', 'rollout', 'optimization', 'automation'
            ]
            
            for subject in subjects:
                subject_lower = subject.lower()
                for indicator in project_indicators:
                    if indicator in subject_lower:
                        # 检查是否与简历技能相关
                        related = any(ind in s.lower() for s in resume_skills for ind in [indicator])
                        if not related:
                            hidden_skills.append(HiddenSkill(
                                skill_name=f"Project: {indicator.title()}",
                                confidence=0.6,
                                source="email",
                                evidence=[subject],
                                category="project"
                            ))
        
        # 2. 从发件人域名推断协作经验
        domains = email_data.get('email_sender_domains', [])
        external_domains = [d for d in domains if not any(
            d.endswith(ex) for ex in ['company.com', 'internal.com', 'corp.com']
        )]
        if external_domains:
            hidden_skills.append(HiddenSkill(
                skill_name="Stakeholder Management",
                confidence=0.5,
                source="email",
                evidence=[f"External communication with: {d}" for d in external_domains[:5]],
                category="soft"
            ))
        
        return self._deduplicate_skills(hidden_skills)
    
    def mine_from_calendar(self, calendar_data: Dict, resume_skills: List[str]) -> List[HiddenSkill]:
        """从日历中挖掘隐性能力"""
        hidden_skills = []
        events = calendar_data.get('calendar_events', [])
        
        training_keywords = ['training', 'træning', 'course', 'kursus', 'certification', 'workshop']
        leadership_keywords = ['standup', '1:1', 'review', 'planning']
        
        for event in events:
            event_lower = event.lower()
            
            # 培训类事件
            if any(k in event_lower for k in training_keywords):
                hidden_skills.append(HiddenSkill(
                    skill_name="Continuous Learning",
                    confidence=0.7,
                    source="calendar",
                    evidence=[event],
                    category="domain"
                ))
            
            # 领导力事件
            if any(k in event_lower for k in leadership_keywords):
                hidden_skills.append(HiddenSkill(
                    skill_name="Team Leadership",
                    confidence=0.5,
                    source="calendar",
                    evidence=[event],
                    category="soft"
                ))
        
        return self._deduplicate_skills(hidden_skills)
    
    def mine_from_documents(self, doc_data: Dict, resume_skills: List[str]) -> List[HiddenSkill]:
        """从文档中挖掘隐性能力"""
        hidden_skills = []
        titles = doc_data.get('document_titles', [])
        keywords = doc_data.get('notes_keywords', [])
        
        for keyword in keywords:
            if keyword not in [s.lower() for s in resume_skills]:
                hidden_skills.append(HiddenSkill(
                    skill_name=keyword.replace('_', ' ').title(),
                    confidence=0.6,
                    source="document",
                    evidence=titles[:3] if titles else [],
                    category="technical"
                ))
        
        return self._deduplicate_skills(hidden_skills)
    
    def _deduplicate_skills(self, skills: List[HiddenSkill]) -> List[HiddenSkill]:
        """去重合并相似技能"""
        unique = {}
        for skill in skills:
            key = skill.skill_name.lower()
            if key not in unique or skill.confidence > unique[key].confidence:
                if key not in unique:
                    unique[key] = skill
                else:
                    unique[key].evidence.extend(skill.evidence)
                    unique[key].evidence = list(set(unique[key].evidence))[:5]
        return list(unique.values())


class ForgottenExperienceFinder:
    """遗忘经历发现器"""
    
    def __init__(self):
        self.experience_patterns = {
            'certification': {
                'patterns': [
                    r'certified?\s+(?:in|as)?\s*(.+?)(?:\s|$|\.)',
                    r'certification\s+(?:in|as)?\s*(.+?)(?:\s|$|\.)',
                    r'(\w+\s+certification)',
                ],
                'keywords': ['certified', 'certification', 'certificate', 'certifikat', 'certificeret']
            },
            'project': {
                'patterns': [
                    r'(?:led|managed|participated in|contributed to)\s+(.+?)(?:\s|$|\.)',
                ],
                'keywords': ['project', 'projekt', 'implementation', 'rollout', 'migration']
            },
            'training': {
                'patterns': [
                    r'(?:attended|completed|finished)\s+(.+?)(?:training|course|workshop)(?:\s|$|\.)',
                ],
                'keywords': ['training', 'træning', 'course', 'kursus', 'workshop', 'seminar']
            },
            'award': {
                'patterns': [
                    r'(?:won|received|awarded)\s+(.+?)(?:\s|$|\.)',
                ],
                'keywords': ['award', 'prize', 'recognition', 'excellence']
            },
            'course': {
                'patterns': [
                    r'(?:studied|completed|took)\s+(.+?)(?:\s|$|\.)',
                ],
                'keywords': ['course', 'class', 'mooc', 'udemy', 'coursera', 'edx']
            }
        }
    
    def find_forgotten_experiences(self, 
                                    email_data: Dict, 
                                    calendar_data: Dict, 
                                    resume_text: str) -> List[ForgottenExperience]:
        """发现可能被遗忘的经历"""
        forgotten = []
        resume_lower = resume_text.lower()
        
        # 从邮件中查找
        subjects = email_data.get('email_subjects', [])
        for subject in subjects:
            subject_lower = subject.lower()
            
            # 检查证书提及
            for cert_pattern in self.experience_patterns['certification']['patterns']:
                matches = re.findall(cert_pattern, subject_lower)
                for match in matches:
                    if match.lower() not in resume_lower:
                        forgotten.append(ForgottenExperience(
                            title=f"可能遗忘的认证: {match}",
                            type="certification",
                            description=f"在邮件主题中发现认证提及: {subject}",
                            confidence=0.6,
                            source="email",
                            suggestion="建议添加到简历的'证书/培训'部分"
                        ))
            
            # 检查项目提及
            for proj_pattern in self.experience_patterns['project']['patterns']:
                matches = re.findall(proj_pattern, subject_lower)
                for match in matches:
                    if match.lower() not in resume_lower and len(match) > 5:
                        forgotten.append(ForgottenExperience(
                            title=f"可能参与的项目: {match.title()}",
                            type="project",
                            description=f"在邮件中发现项目相关提及: {subject}",
                            confidence=0.5,
                            source="email",
                            suggestion="如果参与了此项目，建议添加到简历的'项目经验'部分"
                        ))
        
        # 从日历中查找培训
        events = calendar_data.get('calendar_events', [])
        training_keywords = self.experience_patterns['training']['keywords']
        
        for event in events:
            event_lower = event.lower()
            if any(k in event_lower for k in training_keywords):
                # 检查是否在简历中
                event_words = event_lower.split()
                if not any(word in resume_lower for word in event_words if len(word) > 4):
                    forgotten.append(ForgottenExperience(
                        title=f"可能遗忘的培训: {event}",
                        type="training",
                        description=f"在日历中发现培训事件: {event}",
                        confidence=0.7,
                        source="calendar",
                        suggestion="建议确认是否已完成此培训，如果是则添加到简历"
                    ))
        
        # 去重
        unique = {}
        for exp in forgotten:
            key = exp.title[:30]
            if key not in unique or exp.confidence > unique[key].confidence:
                unique[key] = exp
        
        return list(unique.values())[:10]  # 最多返回10个


class ResumeEnhancer:
    """简历增强器 - 整合所有分析"""
    
    def __init__(self, ai_client=None):
        self.collector = BehaviorDataCollector()
        self.miner = HiddenSkillMiner(ai_client)
        self.finder = ForgottenExperienceFinder()
        self.ai_client = ai_client
    
    def analyze_and_enhance(self, 
                           user_id: str,
                           resume_text: str,
                           resume_skills: List[str],
                           email_data: Dict = None,
                           calendar_data: Dict = None,
                           doc_data: Dict = None,
                           target_job: Dict = None) -> ResumeEnhancement:
        """完整分析并生成增强建议"""
        
        # 如果有行为数据，先保存
        if any([email_data, calendar_data, doc_data]):
            behavior_data = BehaviorData(
                user_id=user_id,
                collected_at=datetime.now().isoformat(),
                email_subjects=email_data.get('email_subjects', []) if email_data else [],
                email_sender_domains=email_data.get('email_sender_domains', []) if email_data else [],
                calendar_events=calendar_data.get('calendar_events', []) if calendar_data else [],
                document_titles=doc_data.get('document_titles', []) if doc_data else []
            )
            self.collector.save_behavior_data(user_id, behavior_data)
        
        # 挖掘隐性能力
        hidden_skills = []
        if email_data:
            hidden_skills.extend(self.miner.mine_from_emails(email_data, resume_skills))
        if calendar_data:
            hidden_skills.extend(self.miner.mine_from_calendar(calendar_data, resume_skills))
        if doc_data:
            hidden_skills.extend(self.miner.mine_from_documents(doc_data, resume_skills))
        
        # 发现遗忘经历
        forgotten = []
        if email_data and calendar_data:
            forgotten = self.finder.find_forgotten_experiences(
                email_data, calendar_data, resume_text
            )
        
        # 生成关键词建议
        keyword_additions = self._suggest_keywords(
            hidden_skills, target_job, resume_skills
        )
        
        # 权重调整
        keyword_weights = self._calculate_weights(
            hidden_skills, target_job
        )
        
        # 生成建议
        suggestions = self._generate_suggestions(
            hidden_skills, forgotten, keyword_additions
        )
        
        # AI综合分析
        ai_insights = ""
        if self.ai_client:
            ai_insights = self._get_ai_insights(
                resume_text, hidden_skills, forgotten, target_job
            )
        
        return ResumeEnhancement(
            hidden_skills=hidden_skills,
            forgotten_experiences=forgotten,
            keyword_additions=keyword_additions,
            keyword_weights=keyword_weights,
            suggestions=suggestions,
            ai_insights=ai_insights
        )
    
    def _suggest_keywords(self, 
                         hidden_skills: List[HiddenSkill], 
                         target_job: Dict = None,
                         resume_skills: List[str] = None) -> List[str]:
        """建议添加的关键词"""
        suggestions = []
        resume_skills_lower = [s.lower() for s in (resume_skills or [])]
        
        for skill in hidden_skills:
            if skill.skill_name.lower() not in resume_skills_lower:
                suggestions.append(skill.skill_name)
        
        # 如果有目标职位，添加职位要求的关键词
        if target_job:
            job_desc = target_job.get('description', '').lower()
            common_erp_terms = [
                'stakeholder management', 'requirements gathering', 
                'business analysis', 'change management', 'process optimization',
                'data migration', 'testing', 'documentation', 'training',
                'go-live support', 'post-implementation'
            ]
            for term in common_erp_terms:
                if term in job_desc and term not in resume_skills_lower:
                    suggestions.append(term)
        
        return list(set(suggestions))
    
    def _calculate_weights(self, 
                          hidden_skills: List[HiddenSkill], 
                          target_job: Dict = None) -> Dict[str, float]:
        """计算技能权重"""
        weights = {}
        
        for skill in hidden_skills:
            weights[skill.skill_name] = skill.confidence * 0.8
        
        if target_job:
            # 根据目标职位调整权重
            job_title = target_job.get('title', '').lower()
            if 'senior' in job_title or 'lead' in job_title:
                weights['Leadership'] = weights.get('Leadership', 0) + 0.3
            if 'consultant' in job_title or 'advisory' in job_title:
                weights['Communication'] = weights.get('Communication', 0) + 0.2
        
        return weights
    
    def _generate_suggestions(self, 
                             hidden_skills: List[HiddenSkill],
                             forgotten: List[ForgottenExperience],
                             keywords: List[str]) -> List[str]:
        """生成简历优化建议"""
        suggestions = []
        
        if hidden_skills:
            suggestions.append(
                f"🔍 发现 {len(hidden_skills)} 个可能未体现在简历中的技能/项目经验"
            )
            for skill in hidden_skills[:3]:
                suggestions.append(
                    f"   • {skill.skill_name} (来源: {skill.source}, 置信度: {skill.confidence:.0%})"
                )
        
        if forgotten:
            suggestions.append(
                f"⏰ 发现 {len(forgotten)} 个可能被遗忘的经历"
            )
            for exp in forgotten[:3]:
                suggestions.append(
                    f"   • {exp.title} - {exp.suggestion}"
                )
        
        if keywords:
            suggestions.append(
                f"📝 建议添加 {len(keywords)} 个关键词以提升简历匹配度"
            )
        
        if not suggestions:
            suggestions.append("✅ 简历已覆盖主要经历，未发现明显遗漏")
        
        return suggestions
    
    def _get_ai_insights(self, 
                        resume_text: str,
                        hidden_skills: List[HiddenSkill],
                        forgotten: List[ForgottenExperience],
                        target_job: Dict = None) -> str:
        """获取AI综合分析"""
        try:
            prompt = f"""作为专业简历顾问，分析以下信息并给出改进建议：

## 当前简历摘要
{resume_text[:1500]}

## 从行为数据中挖掘到的隐性能力
{[s.to_dict() if hasattr(s, 'to_dict') else str(s) for s in hidden_skills[:5]]}

## 可能被遗忘的经历
{[f.to_dict() if hasattr(f, 'to_dict') else str(f) for f in forgotten[:5]]}

## 目标职位（如果有）
{target_job.get('title', 'N/A')} @ {target_job.get('company', 'N/A')}
{target_job.get('description', '')[:500]}

请给出简洁的3-5条简历优化建议，重点说明：
1. 如何更好地展示隐性能力
2. 如何补全可能的经历空白
3. 针对目标职位的关键词优化

用中文回答。"""
            
            response = self.ai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "你是专业简历顾问，给出实用、可操作的建议。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )
            
            return response.choices[0].message.content
        except Exception as e:
            return f"AI分析暂不可用 (Error: {str(e)[:50]})"


class DynamicResumeOptimizer:
    """动态简历优化器 - 根据目标职位调整简历"""
    
    def __init__(self, ai_client=None):
        self.enhancer = ResumeEnhancer(ai_client)
        self.ai_client = ai_client
    
    def optimize_for_job(self, 
                         user_id: str,
                         resume_text: str,
                         resume_skills: List[str],
                         target_job: Dict) -> Dict:
        """针对特定职位优化简历"""
        
        # 1. 分析简历与职位的匹配度
        match_score = self._calculate_match_score(resume_text, target_job)
        
        # 2. 获取增强建议
        enhancement = self.enhancer.analyze_and_enhance(
            user_id=user_id,
            resume_text=resume_text,
            resume_skills=resume_skills,
            target_job=target_job
        )
        
        # 3. 生成优化后的简历摘要
        optimized_summary = self._generate_optimized_summary(
            resume_text, target_job, enhancement
        )
        
        # 4. 生成申请该职位时的简历提示
        tips = self._generate_application_tips(resume_text, target_job, enhancement)
        
        return {
            'match_score': match_score,
            'enhancement': {
                'hidden_skills': [s.to_dict() if hasattr(s, 'to_dict') else s for s in enhancement.hidden_skills],
                'forgotten_experiences': [e.to_dict() if hasattr(e, 'to_dict') else e for e in enhancement.forgotten_experiences],
                'keyword_additions': enhancement.keyword_additions,
                'suggestions': enhancement.suggestions,
                'ai_insights': enhancement.ai_insights
            },
            'optimized_summary': optimized_summary,
            'application_tips': tips
        }
    
    def _calculate_match_score(self, resume_text: str, job: Dict) -> float:
        """计算简历与职位的匹配度"""
        resume_lower = resume_text.lower()
        job_desc = job.get('description', '').lower()
        
        # 提取关键词
        important_words = [
            'erp', 'netsuite', 'dynamics', 'sap', 'ax', '365', 'finance',
            'implementation', 'consulting', 'project', 'management',
            'stakeholder', 'analysis', 'sql', 'integration', 'cloud'
        ]
        
        matches = sum(1 for word in important_words 
                     if word in resume_lower and word in job_desc)
        
        return min(100, (matches / len(important_words)) * 100 + 20)
    
    def _generate_optimized_summary(self, 
                                    resume_text: str, 
                                    job: Dict,
                                    enhancement: ResumeEnhancement) -> str:
        """生成优化后的简历摘要"""
        base_summary = resume_text[:500]
        
        additions = []
        for keyword in enhancement.keyword_additions[:5]:
            additions.append(f"- {keyword}")
        
        return f"""## 针对 {job.get('title', '该职位')} 的简历优化建议

### 当前简历亮点（保留）
{base_summary}

### 建议强调的能力（从行为数据中发现）
{chr(10).join(additions) if additions else '无新增建议'}

### 关键词优化
针对该职位，建议在简历中更多强调：
{', '.join(enhancement.keyword_additions[:10]) if enhancement.keyword_additions else '简历已覆盖主要关键词'}
"""
    
    def _generate_application_tips(self, 
                                   resume_text: str, 
                                   job: Dict,
                                   enhancement: ResumeEnhancement) -> List[str]:
        """生成申请提示"""
        tips = []
        
        # 基础提示
        tips.append("📋 申请前检查清单：")
        tips.append("   □ 确认简历包含职位描述中的核心关键词")
        tips.append("   □ 添加从行为数据中发现的隐性能力")
        tips.append("   □ 确认没有遗漏的培训/证书经历")
        
        # 针对职位的提示
        job_title = job.get('title', '').lower()
        if 'senior' in job_title or 'lead' in job_title:
            tips.append("   □ 强调领导力和项目管理经验")
            tips.append("   □ 量化成果（如：管理X人团队/成功交付X个项目）")
        
        if 'consultant' in job_title:
            tips.append("   □ 突出沟通能力和客户管理经验")
            tips.append("   □ 准备具体的案例分享")
        
        # AI建议
        if enhancement.ai_insights:
            tips.append("")
            tips.append("💡 AI智能建议：")
            for line in enhancement.ai_insights.split('\n')[:5]:
                if line.strip():
                    tips.append(f"   {line}")
        
        return tips


# === 导出 ===
def create_resume_enhancer(ai_client=None) -> ResumeEnhancer:
    """创建简历增强器"""
    return ResumeEnhancer(ai_client)


def create_dynamic_optimizer(ai_client=None) -> DynamicResumeOptimizer:
    """创建动态简历优化器"""
    return DynamicResumeOptimizer(ai_client)
