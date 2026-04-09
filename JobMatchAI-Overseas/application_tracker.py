"""
JobMatchAI - 申请追踪服务模块
提供完整的申请记录 CRUD 操作

申请状态流转：
- new: 新申请（待投递）
- applied: 已投递
- screening: 筛选中
- interview: 面试中
- offer: 已拿到offer
- rejected: 被拒绝
- withdrawn: 自己撤回
- accepted: 已接受

Copyright © 2026 JobMatchAI. All rights reserved.
"""

import sys
import os
from typing import Dict, Any, Optional, List
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))
from database import (
    create_application, get_application_by_id, get_user_applications,
    update_application, delete_application, get_application_statistics,
    create_cover_letter, get_user_cover_letters, get_cover_letter_by_id,
    update_cover_letter, delete_cover_letter, get_templates,
    create_resume, get_user_resumes, get_primary_resume
)

# 申请状态定义
APPLICATION_STATUSES = {
    "new": {"name": "新申请", "name_en": "New", "name_da": "Ny", "color": "#2196F3"},
    "applied": {"name": "已投递", "name_en": "Applied", "name_da": "Sendt", "color": "#4CAF50"},
    "screening": {"name": "筛选中", "name_en": "Screening", "name_da": "Screening", "color": "#FF9800"},
    "interview": {"name": "面试中", "name_en": "Interview", "name_da": "Samtale", "color": "#9C27B0"},
    "offer": {"name": "已拿到Offer", "name_en": "Offer", "name_da": "Tilbud", "color": "#00BCD4"},
    "rejected": {"name": "被拒绝", "name_en": "Rejected", "name_da": "Afvist", "color": "#F44336"},
    "withdrawn": {"name": "已撤回", "name_en": "Withdrawn", "name_da": "Trukket", "color": "#607D8B"},
    "accepted": {"name": "已接受", "name_en": "Accepted", "name_da": "Accepteret", "color": "#4CAF50"}
}

# 优先级定义
PRIORITY_LEVELS = {
    "high": {"name": "高优先级", "name_en": "High", "name_da": "Høj", "color": "#F44336"},
    "normal": {"name": "普通", "name_en": "Normal", "name_da": "Normal", "color": "#2196F3"},
    "low": {"name": "低优先级", "name_en": "Low", "name_da": "Lav", "color": "#9E9E9E"}
}


class ApplicationService:
    """申请服务"""
    
    def __init__(self):
        pass
    
    def add_application(
        self,
        user_id: str,
        job_title: str,
        company: str,
        job_id: str = "",
        company_website: str = "",
        job_url: str = "",
        salary_range: str = "",
        location: str = "",
        status: str = "new",
        priority: str = "normal",
        applied_date: str = "",
        deadline: str = "",
        contact_name: str = "",
        contact_email: str = "",
        contact_phone: str = "",
        notes: str = "",
        match_score: float = 0,
        resume_id: str = "",
        cover_letter_id: str = ""
    ) -> Dict[str, Any]:
        """添加申请记录"""
        # 验证状态
        if status not in APPLICATION_STATUSES:
            status = "new"
        
        # 验证优先级
        if priority not in PRIORITY_LEVELS:
            priority = "normal"
        
        # 设置默认申请日期
        if not applied_date:
            applied_date = datetime.now().strftime("%Y-%m-%d")
        
        app = create_application(
            user_id=user_id,
            job_id=job_id,
            job_title=job_title,
            company=company,
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
        
        if app:
            return {
                "success": True,
                "application": self._format_application(app),
                "message": "Application added successfully"
            }
        
        return {
            "success": False,
            "error": "Failed to add application"
        }
    
    def get_application(self, application_id: str, user_id: str) -> Dict[str, Any]:
        """获取单个申请记录"""
        app = get_application_by_id(application_id)
        
        if not app:
            return {
                "success": False,
                "error": "Application not found"
            }
        
        # 验证用户权限
        if app["user_id"] != user_id:
            return {
                "success": False,
                "error": "Access denied"
            }
        
        return {
            "success": True,
            "application": self._format_application(app)
        }
    
    def list_applications(
        self,
        user_id: str,
        status: str = "all",
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """获取申请列表"""
        apps = get_user_applications(user_id, status)
        
        # 分页
        total = len(apps)
        start = (page - 1) * page_size
        end = start + page_size
        paginated_apps = apps[start:end]
        
        return {
            "success": True,
            "applications": [self._format_application(app) for app in paginated_apps],
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": (total + page_size - 1) // page_size
        }
    
    def update_application(
        self,
        application_id: str,
        user_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """更新申请记录"""
        # 验证状态值
        if "status" in kwargs:
            if kwargs["status"] not in APPLICATION_STATUSES:
                return {
                    "success": False,
                    "error": f"Invalid status. Valid values: {', '.join(APPLICATION_STATUSES.keys())}"
                }
        
        # 验证优先级
        if "priority" in kwargs:
            if kwargs["priority"] not in PRIORITY_LEVELS:
                return {
                    "success": False,
                    "error": f"Invalid priority. Valid values: {', '.join(PRIORITY_LEVELS.keys())}"
                }
        
        app = update_application(application_id, user_id, **kwargs)
        
        if not app:
            return {
                "success": False,
                "error": "Application not found or access denied"
            }
        
        return {
            "success": True,
            "application": self._format_application(app),
            "message": "Application updated successfully"
        }
    
    def update_status(
        self,
        application_id: str,
        user_id: str,
        new_status: str,
        notes: str = ""
    ) -> Dict[str, Any]:
        """更新申请状态"""
        if new_status not in APPLICATION_STATUSES:
            return {
                "success": False,
                "error": f"Invalid status. Valid values: {', '.join(APPLICATION_STATUSES.keys())}"
            }
        
        update_data = {"status": new_status}
        if notes:
            update_data["notes"] = notes
        
        # 自动设置标志
        if new_status == "offer":
            update_data["offer_received"] = True
        if new_status == "rejected":
            update_data["rejected"] = True
        
        app = update_application(application_id, user_id, **update_data)
        
        if not app:
            return {
                "success": False,
                "error": "Application not found or access denied"
            }
        
        return {
            "success": True,
            "application": self._format_application(app),
            "message": f"Status updated to: {APPLICATION_STATUSES[new_status]['name']}"
        }
    
    def add_interview(
        self,
        application_id: str,
        user_id: str,
        interview_date: str,
        interview_notes: str = ""
    ) -> Dict[str, Any]:
        """添加面试信息"""
        app = update_application(
            application_id,
            user_id,
            interview_date=interview_date,
            interview_notes=interview_notes,
            status="interview"
        )
        
        if not app:
            return {
                "success": False,
                "error": "Application not found or access denied"
            }
        
        return {
            "success": True,
            "application": self._format_application(app),
            "message": "Interview added successfully"
        }
    
    def delete_application(self, application_id: str, user_id: str) -> Dict[str, Any]:
        """删除申请记录"""
        success = delete_application(application_id, user_id)
        
        if success:
            return {
                "success": True,
                "message": "Application deleted successfully"
            }
        
        return {
            "success": False,
            "error": "Application not found or access denied"
        }
    
    def get_statistics(self, user_id: str) -> Dict[str, Any]:
        """获取申请统计"""
        stats = get_application_statistics(user_id)
        
        # 添加状态详情
        status_details = {}
        for status_key, status_info in APPLICATION_STATUSES.items():
            count = stats.get("status_breakdown", {}).get(status_key, 0)
            status_details[status_key] = {
                **status_info,
                "count": count
            }
        
        return {
            "success": True,
            "statistics": {
                **stats,
                "status_details": status_details
            }
        }
    
    def get_upcoming_activities(self, user_id: str) -> Dict[str, Any]:
        """获取即将到来的活动"""
        apps = get_user_applications(user_id)
        upcoming = []
        
        for app in apps:
            # 面试
            if app.get("interview_date"):
                upcoming.append({
                    "type": "interview",
                    "application_id": app["application_id"],
                    "job_title": app["job_title"],
                    "company": app["company"],
                    "date": app["interview_date"],
                    "notes": app.get("interview_notes", "")
                })
            
            # 跟进
            if app.get("follow_up_date"):
                upcoming.append({
                    "type": "follow_up",
                    "application_id": app["application_id"],
                    "job_title": app["job_title"],
                    "company": app["company"],
                    "date": app["follow_up_date"],
                    "notes": ""
                })
            
            # 截止日期
            if app.get("deadline"):
                upcoming.append({
                    "type": "deadline",
                    "application_id": app["application_id"],
                    "job_title": app["job_title"],
                    "company": app["company"],
                    "date": app["deadline"],
                    "notes": "Application deadline"
                })
        
        # 按日期排序
        upcoming.sort(key=lambda x: x.get("date", ""))
        
        return {
            "success": True,
            "upcoming": upcoming[:10]
        }
    
    def get_status_options(self, language: str = "en") -> Dict[str, Any]:
        """获取状态选项列表"""
        result = {}
        for key, info in APPLICATION_STATUSES.items():
            if language == "zh":
                result[key] = info["name"]
            elif language == "da":
                result[key] = info["name_da"]
            else:
                result[key] = info["name_en"]
        
        return {
            "success": True,
            "statuses": result,
            "priorities": {
                k: v["name_en"] if language == "en" else (v["name"] if language == "zh" else v["name_da"])
                for k, v in PRIORITY_LEVELS.items()
            }
        }
    
    def _format_application(self, app: Dict) -> Dict:
        """格式化申请记录"""
        return {
            "application_id": app["application_id"],
            "user_id": app["user_id"],
            "job_id": app.get("job_id", ""),
            "job_title": app["job_title"],
            "company": app["company"],
            "company_website": app.get("company_website", ""),
            "job_url": app.get("job_url", ""),
            "salary_range": app.get("salary_range", ""),
            "location": app.get("location", ""),
            "status": app["status"],
            "status_name": APPLICATION_STATUSES.get(app["status"], {}).get(
                "name_en", app["status"]
            ),
            "priority": app.get("priority", "normal"),
            "priority_name": PRIORITY_LEVELS.get(app.get("priority", "normal"), {}).get(
                "name_en", "Normal"
            ),
            "applied_date": app.get("applied_date", ""),
            "deadline": app.get("deadline", ""),
            "contact_name": app.get("contact_name", ""),
            "contact_email": app.get("contact_email", ""),
            "contact_phone": app.get("contact_phone", ""),
            "notes": app.get("notes", ""),
            "interview_date": app.get("interview_date", ""),
            "interview_notes": app.get("interview_notes", ""),
            "offer_received": bool(app.get("offer_received", 0)),
            "rejected": bool(app.get("rejected", 0)),
            "follow_up_date": app.get("follow_up_date", ""),
            "match_score": app.get("match_score", 0),
            "resume_id": app.get("resume_id", ""),
            "cover_letter_id": app.get("cover_letter_id", ""),
            "created_at": app["created_at"],
            "updated_at": app.get("updated_at", app["created_at"])
        }


# 全局服务实例
application_service = ApplicationService()


# === 辅助函数 ===

def quick_add_application(
    user_id: str,
    job_title: str,
    company: str,
    location: str = "",
    job_url: str = "",
    status: str = "applied"
) -> Dict[str, Any]:
    """快速添加申请（简化接口）"""
    return application_service.add_application(
        user_id=user_id,
        job_title=job_title,
        company=company,
        location=location,
        job_url=job_url,
        status=status
    )


def bulk_update_status(
    user_id: str,
    application_ids: List[str],
    new_status: str
) -> Dict[str, Any]:
    """批量更新状态"""
    results = []
    for app_id in application_ids:
        result = application_service.update_status(app_id, user_id, new_status)
        results.append({
            "application_id": app_id,
            **result
        })
    
    success_count = sum(1 for r in results if r["success"])
    
    return {
        "success": True,
        "total": len(application_ids),
        "success_count": success_count,
        "failed_count": len(application_ids) - success_count,
        "results": results
    }
