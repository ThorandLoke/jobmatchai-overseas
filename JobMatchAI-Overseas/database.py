"""
JobMatchAI - 数据库模块
使用 Turso (SQLite 兼容) 云端数据库

表结构：
- users: 用户表
- resumes: 简历表
- jobs: 职位表
- applications: 申请记录表
- cover_letters: 求职信表

本地开发：USE_LOCAL_SQLITE=true → 本地 SQLite
生产部署：USE_LOCAL_SQLITE=false → Turso 云端

Copyright © 2026 JobMatchAI. All rights reserved.
"""

import os
import json
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

# 优先从 turso_client 导入（支持本地/云端自动切换）
try:
    from turso_client import get_db_connection
except ImportError:
    # 如果 turso_client 不可用，回退到本地 sqlite3（不应在生产环境发生）
    import sqlite3
    DB_PATH = os.path.join(os.path.dirname(__file__), "data", "jobmatchai.db")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    def get_db_connection():
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn


@contextmanager
def get_db():
    """上下文管理器：自动管理数据库连接"""
    conn = get_db_connection()
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_database():
    """初始化数据库表"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 用户表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                name TEXT,
                phone TEXT,
                country TEXT,
                city TEXT,
                preferred_language TEXT DEFAULT 'en',
                subscription_plan TEXT DEFAULT 'free',
                subscription_expires_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        # 简历表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS resumes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resume_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                title TEXT,
                content TEXT NOT NULL,
                language TEXT DEFAULT 'en',
                file_name TEXT,
                file_type TEXT,
                is_primary INTEGER DEFAULT 0,
                ats_score INTEGER,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # 职位表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT UNIQUE NOT NULL,
                source TEXT,
                title TEXT NOT NULL,
                company TEXT NOT NULL,
                location TEXT,
                description TEXT,
                requirements TEXT,
                url TEXT,
                salary_range TEXT,
                job_type TEXT,
                language TEXT DEFAULT 'en',
                match_score REAL,
                saved_by_user_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (saved_by_user_id) REFERENCES users(user_id)
            )
        """)
        
        # 申请记录表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                application_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                job_id TEXT,
                job_title TEXT NOT NULL,
                company TEXT NOT NULL,
                company_website TEXT,
                job_url TEXT,
                salary_range TEXT,
                location TEXT,
                status TEXT DEFAULT 'new',
                priority TEXT DEFAULT 'normal',
                applied_date TEXT,
                deadline TEXT,
                contact_name TEXT,
                contact_email TEXT,
                contact_phone TEXT,
                notes TEXT,
                interview_date TEXT,
                interview_notes TEXT,
                offer_received INTEGER DEFAULT 0,
                rejected INTEGER DEFAULT 0,
                follow_up_date TEXT,
                match_score REAL,
                resume_id TEXT,
                cover_letter_id TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (job_id) REFERENCES jobs(job_id)
            )
        """)
        
        # 求职信表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cover_letters (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cover_letter_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                application_id TEXT,
                job_title TEXT,
                company TEXT NOT NULL,
                content TEXT NOT NULL,
                language TEXT DEFAULT 'en',
                is_template INTEGER DEFAULT 0,
                quality_score REAL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (application_id) REFERENCES applications(application_id)
            )
        """)
        
        # 创建索引
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_user_id ON users(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_resumes_user_id ON resumes(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_applications_user_id ON applications(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_cover_letters_user_id ON cover_letters(user_id)")
        
        # 会话绑定表 - 将匿名会话绑定到注册用户
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_bindings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                anonymous_session_id TEXT UNIQUE NOT NULL,
                user_id TEXT NOT NULL,
                bound_at TEXT NOT NULL,
                session_data TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        """)
        
        # 用户会话数据临时存储表
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS session_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT UNIQUE NOT NULL,
                data_type TEXT NOT NULL,
                data_content TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            )
        """)
        
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_bindings_session ON session_bindings(anonymous_session_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_bindings_user ON session_bindings(user_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_session_data_session ON session_data(session_id)")
        
        conn.commit()
        print("✅ 数据库初始化完成（" + ("本地 SQLite" if os.environ.get("USE_LOCAL_SQLITE","true")=="true" else "Turso 云端") + "）")


def generate_id(prefix: str) -> str:
    """生成唯一ID"""
    import uuid
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    short_uuid = str(uuid.uuid4())[:8]
    return f"{prefix}_{timestamp}_{short_uuid}"


# === 用户操作 ===

def create_user(
    user_id: str,
    email: str,
    password_hash: str,
    name: str = "",
    phone: str = "",
    country: str = "",
    city: str = ""
) -> Dict[str, Any]:
    """创建新用户"""
    now = datetime.now().isoformat()
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (user_id, email, password_hash, name, phone, country, city, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (user_id, email, password_hash, name, phone, country, city, now, now))
        conn.commit()
        return get_user_by_id(user_id)


def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """根据用户ID获取用户"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """根据邮箱获取用户"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


def update_user(user_id: str, **kwargs) -> Optional[Dict[str, Any]]:
    """更新用户信息"""
    allowed_fields = ['name', 'phone', 'country', 'city', 'preferred_language', 
                      'subscription_plan', 'subscription_expires_at']
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
    
    if not updates:
        return get_user_by_id(user_id)
    
    updates['updated_at'] = datetime.now().isoformat()
    
    set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values()) + [user_id]
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE users SET {set_clause} WHERE user_id = ?", values)
        conn.commit()
        return get_user_by_id(user_id)


def verify_user_password(email: str, password_hash: str) -> Optional[Dict[str, Any]]:
    """验证用户密码"""
    user = get_user_by_email(email)
    if user and user['password_hash'] == password_hash:
        return user
    return None


# === 简历操作 ===

def create_resume(
    user_id: str,
    content: str,
    title: str = "",
    language: str = "en",
    file_name: str = "",
    file_type: str = "",
    is_primary: bool = False
) -> Dict[str, Any]:
    """创建简历记录"""
    now = datetime.now().isoformat()
    resume_id = generate_id("resume")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 如果设为主要简历，先取消其他主要简历
        if is_primary:
            cursor.execute("UPDATE resumes SET is_primary = 0 WHERE user_id = ?", (user_id,))
        
        cursor.execute("""
            INSERT INTO resumes (resume_id, user_id, title, content, language, file_name, file_type, is_primary, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (resume_id, user_id, title, content, language, file_name, file_type, 1 if is_primary else 0, now, now))
        conn.commit()
        
        return get_resume_by_id(resume_id)


def get_resume_by_id(resume_id: str) -> Optional[Dict[str, Any]]:
    """根据简历ID获取简历"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM resumes WHERE resume_id = ?", (resume_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


def get_user_resumes(user_id: str) -> List[Dict[str, Any]]:
    """获取用户的所有简历"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM resumes WHERE user_id = ? ORDER BY is_primary DESC, created_at DESC", (user_id,))
        return [dict(row) for row in cursor.fetchall()]


def get_primary_resume(user_id: str) -> Optional[Dict[str, Any]]:
    """获取用户的主要简历"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM resumes WHERE user_id = ? AND is_primary = 1", (user_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        # 如果没有主要简历，返回最新的
        cursor.execute("SELECT * FROM resumes WHERE user_id = ? ORDER BY created_at DESC LIMIT 1", (user_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


def update_resume(resume_id: str, **kwargs) -> Optional[Dict[str, Any]]:
    """更新简历"""
    allowed_fields = ['title', 'content', 'language', 'file_name', 'file_type', 'is_primary', 'ats_score']
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
    
    if not updates:
        return get_resume_by_id(resume_id)
    
    updates['updated_at'] = datetime.now().isoformat()
    
    # 如果设为主要简历，先取消其他主要简历
    if updates.get('is_primary'):
        resume = get_resume_by_id(resume_id)
        if resume:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("UPDATE resumes SET is_primary = 0 WHERE user_id = ? AND resume_id != ?", 
                            (resume['user_id'], resume_id))
    
    set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values()) + [resume_id]
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE resumes SET {set_clause} WHERE resume_id = ?", values)
        conn.commit()
        return get_resume_by_id(resume_id)


def delete_resume(resume_id: str) -> bool:
    """删除简历"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM resumes WHERE resume_id = ?", (resume_id,))
        conn.commit()
        return cursor.rowcount > 0


# === 职位操作 ===

def save_job(
    user_id: str,
    title: str,
    company: str,
    source: str = "",
    location: str = "",
    description: str = "",
    requirements: str = "",
    url: str = "",
    salary_range: str = "",
    job_type: str = "",
    language: str = "en",
    match_score: float = 0
) -> Dict[str, Any]:
    """保存职位"""
    now = datetime.now().isoformat()
    job_id = generate_id("job")
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO jobs (job_id, source, title, company, location, description, requirements, url, salary_range, job_type, language, match_score, saved_by_user_id, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (job_id, source, title, company, location, description, requirements, url, salary_range, job_type, language, match_score, user_id, now, now))
        conn.commit()
        
        return get_job_by_id(job_id)


def get_job_by_id(job_id: str) -> Optional[Dict[str, Any]]:
    """根据职位ID获取职位"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


def get_user_saved_jobs(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
    """获取用户保存的职位"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE saved_by_user_id = ? ORDER BY created_at DESC LIMIT ?", (user_id, limit))
        return [dict(row) for row in cursor.fetchall()]


def delete_saved_job(job_id: str, user_id: str) -> bool:
    """删除保存的职位"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM jobs WHERE job_id = ? AND saved_by_user_id = ?", (job_id, user_id))
        conn.commit()
        return cursor.rowcount > 0


# === 申请记录操作 ===

def create_application(
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
    """创建申请记录"""
    now = datetime.now().isoformat()
    application_id = generate_id("app")
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO applications (
                application_id, user_id, job_id, job_title, company, company_website, job_url,
                salary_range, location, status, priority, applied_date, deadline,
                contact_name, contact_email, contact_phone, notes, match_score,
                resume_id, cover_letter_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            application_id, user_id, job_id, job_title, company, company_website, job_url,
            salary_range, location, status, priority, applied_date, deadline,
            contact_name, contact_email, contact_phone, notes, match_score,
            resume_id, cover_letter_id, now, now
        ))
        conn.commit()
        
        return get_application_by_id(application_id)


def get_application_by_id(application_id: str) -> Optional[Dict[str, Any]]:
    """根据申请ID获取申请记录"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM applications WHERE application_id = ?", (application_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


def get_user_applications(user_id: str, status: str = "all") -> List[Dict[str, Any]]:
    """获取用户的申请记录"""
    with get_db() as conn:
        cursor = conn.cursor()
        if status == "all":
            cursor.execute("""
                SELECT * FROM applications WHERE user_id = ? 
                ORDER BY 
                    CASE priority 
                        WHEN 'high' THEN 0 
                        WHEN 'normal' THEN 1 
                        WHEN 'low' THEN 2 
                    END,
                    match_score DESC,
                    created_at DESC
            """, (user_id,))
        else:
            cursor.execute("""
                SELECT * FROM applications WHERE user_id = ? AND status = ?
                ORDER BY 
                    CASE priority 
                        WHEN 'high' THEN 0 
                        WHEN 'normal' THEN 1 
                        WHEN 'low' THEN 2 
                    END,
                    match_score DESC,
                    created_at DESC
            """, (user_id, status))
        return [dict(row) for row in cursor.fetchall()]


def update_application(application_id: str, user_id: str, **kwargs) -> Optional[Dict[str, Any]]:
    """更新申请记录"""
    allowed_fields = [
        'job_title', 'company', 'company_website', 'job_url', 'salary_range', 'location',
        'status', 'priority', 'applied_date', 'deadline', 'contact_name', 'contact_email',
        'contact_phone', 'notes', 'interview_date', 'interview_notes', 'offer_received',
        'rejected', 'follow_up_date', 'match_score', 'resume_id', 'cover_letter_id'
    ]
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
    
    if not updates:
        return get_application_by_id(application_id)
    
    updates['updated_at'] = datetime.now().isoformat()
    
    # 处理布尔值
    if 'offer_received' in updates:
        updates['offer_received'] = 1 if updates['offer_received'] else 0
    if 'rejected' in updates:
        updates['rejected'] = 1 if updates['rejected'] else 0
    
    set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values()) + [application_id, user_id]
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE applications SET {set_clause} WHERE application_id = ? AND user_id = ?", values)
        conn.commit()
        return get_application_by_id(application_id)


def delete_application(application_id: str, user_id: str) -> bool:
    """删除申请记录"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM applications WHERE application_id = ? AND user_id = ?", (application_id, user_id))
        conn.commit()
        return cursor.rowcount > 0


def get_application_statistics(user_id: str) -> Dict[str, Any]:
    """获取申请统计"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 总数
        cursor.execute("SELECT COUNT(*) as total FROM applications WHERE user_id = ?", (user_id,))
        total = cursor.fetchone()['total']
        
        # 各状态数量
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM applications WHERE user_id = ? 
            GROUP BY status
        """, (user_id,))
        status_counts = {row['status']: row['count'] for row in cursor.fetchall()}
        
        # 本周申请数
        cursor.execute("""
            SELECT COUNT(*) as count FROM applications 
            WHERE user_id = ? AND created_at >= date('now', '-7 days')
        """, (user_id,))
        this_week = cursor.fetchone()['count']
        
        # 响应率
        responded = sum(1 for s in status_counts if s not in ['new', 'applied'])
        response_rate = round(responded / total * 100, 1) if total > 0 else 0
        
        return {
            'total_applications': total,
            'status_breakdown': status_counts,
            'this_week': this_week,
            'response_rate': response_rate,
            'pending': status_counts.get('new', 0) + status_counts.get('applied', 0),
            'interviews': status_counts.get('interview', 0),
            'offers': status_counts.get('offer', 0),
            'rejections': status_counts.get('rejected', 0)
        }


# === 求职信操作 ===

def create_cover_letter(
    user_id: str,
    company: str,
    content: str,
    job_title: str = "",
    application_id: str = "",
    language: str = "en",
    is_template: bool = False,
    quality_score: float = 0
) -> Dict[str, Any]:
    """创建求职信"""
    now = datetime.now().isoformat()
    cover_letter_id = generate_id("cl")
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO cover_letters (cover_letter_id, user_id, application_id, job_title, company, content, language, is_template, quality_score, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (cover_letter_id, user_id, application_id, job_title, company, content, language, 1 if is_template else 0, quality_score, now, now))
        conn.commit()
        
        return get_cover_letter_by_id(cover_letter_id)


def get_cover_letter_by_id(cover_letter_id: str) -> Optional[Dict[str, Any]]:
    """根据求职信ID获取求职信"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM cover_letters WHERE cover_letter_id = ?", (cover_letter_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
    return None


def get_user_cover_letters(user_id: str, application_id: str = "") -> List[Dict[str, Any]]:
    """获取用户的求职信"""
    with get_db() as conn:
        cursor = conn.cursor()
        if application_id:
            cursor.execute("""
                SELECT * FROM cover_letters 
                WHERE user_id = ? AND (application_id = ? OR application_id = '')
                ORDER BY created_at DESC
            """, (user_id, application_id))
        else:
            cursor.execute("SELECT * FROM cover_letters WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        return [dict(row) for row in cursor.fetchall()]


def get_templates(user_id: str) -> List[Dict[str, Any]]:
    """获取用户的求职信模板"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM cover_letters 
            WHERE user_id = ? AND is_template = 1 
            ORDER BY created_at DESC
        """, (user_id,))
        return [dict(row) for row in cursor.fetchall()]


def update_cover_letter(cover_letter_id: str, **kwargs) -> Optional[Dict[str, Any]]:
    """更新求职信"""
    allowed_fields = ['content', 'language', 'is_template', 'quality_score', 'job_title']
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
    
    if not updates:
        return get_cover_letter_by_id(cover_letter_id)
    
    updates['updated_at'] = datetime.now().isoformat()
    
    set_clause = ", ".join([f"{k} = ?" for k in updates.keys()])
    values = list(updates.values()) + [cover_letter_id]
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(f"UPDATE cover_letters SET {set_clause} WHERE cover_letter_id = ?", values)
        conn.commit()
        return get_cover_letter_by_id(cover_letter_id)


def delete_cover_letter(cover_letter_id: str, user_id: str) -> bool:
    """删除求职信"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM cover_letters WHERE cover_letter_id = ? AND user_id = ?", (cover_letter_id, user_id))
        conn.commit()
        return cursor.rowcount > 0


# === 会话绑定功能 ===

def save_session_data(session_id: str, data_type: str, data_content: str) -> bool:
    """保存会话临时数据（简历、求职信等）"""
    now = datetime.now().isoformat()
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 尝试更新已存在的记录
        cursor.execute("""
            UPDATE session_data 
            SET data_content = ?, updated_at = ?
            WHERE session_id = ? AND data_type = ?
        """, (data_content, now, session_id, data_type))
        
        if cursor.rowcount == 0:
            # 插入新记录
            cursor.execute("""
                INSERT INTO session_data (session_id, data_type, data_content, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (session_id, data_type, data_content, now, now))
        
        conn.commit()
        return True


def get_session_data(session_id: str, data_type: str = None) -> Optional[Dict[str, Any]]:
    """获取会话数据"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        if data_type:
            cursor.execute("""
                SELECT * FROM session_data 
                WHERE session_id = ? AND data_type = ?
            """, (session_id, data_type))
            row = cursor.fetchone()
            if row:
                return dict(row)
        else:
            cursor.execute("""
                SELECT * FROM session_data 
                WHERE session_id = ?
            """, (session_id,))
            rows = cursor.fetchall()
            if rows:
                return [dict(row) for row in rows]
        
        return None


def get_all_session_data(session_id: str) -> Dict[str, str]:
    """获取会话的所有数据，返回 {data_type: content} 字典"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT data_type, data_content FROM session_data 
            WHERE session_id = ?
        """, (session_id,))
        rows = cursor.fetchall()
        return {row['data_type']: row['data_content'] for row in rows}


def bind_session_to_user(anonymous_session_id: str, user_id: str) -> bool:
    """将会话绑定到注册用户
    
    1. 创建绑定记录
    2. 将session_data转移到user_id下
    3. 更新resume、cover_letter等表的user_id
    """
    now = datetime.now().isoformat()
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        # 1. 检查是否已存在绑定
        cursor.execute("""
            SELECT user_id FROM session_bindings 
            WHERE anonymous_session_id = ?
        """, (anonymous_session_id,))
        existing = cursor.fetchone()
        
        if existing:
            # 已绑定，直接返回
            return True
        
        # 2. 创建绑定记录
        cursor.execute("""
            INSERT INTO session_bindings (anonymous_session_id, user_id, bound_at)
            VALUES (?, ?, ?)
        """, (anonymous_session_id, user_id, now))
        
        # 3. 转移会话数据到用户
        session_data = get_all_session_data(anonymous_session_id)
        
        if 'resume' in session_data:
            # 创建用户简历
            resume_content = session_data['resume']
            resume_lang = session_data.get('resume_lang', 'en')
            create_resume(
                user_id=user_id,
                title="我的简历",
                content=resume_content,
                language=resume_lang,
                is_primary=True
            )
        
        if 'job_description' in session_data:
            # 保存职位描述
            import json
            job_data = json.loads(session_data['job_description'])
            save_job(
                user_id=user_id,
                title=job_data.get('title', ''),
                company=job_data.get('company', ''),
                description=job_data.get('description', ''),
                url=job_data.get('url', '')
            )
        
        # 4. 删除临时会话数据
        cursor.execute("DELETE FROM session_data WHERE session_id = ?", (anonymous_session_id,))
        
        conn.commit()
        return True


def get_user_by_session(session_id: str) -> Optional[Dict[str, Any]]:
    """通过会话ID获取绑定的用户"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT u.* FROM users u
            JOIN session_bindings sb ON u.user_id = sb.user_id
            WHERE sb.anonymous_session_id = ?
        """, (session_id,))
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def cleanup_session_data(max_age_hours: int = 24) -> int:
    """清理过期的会话数据"""
    from datetime import timedelta
    cutoff = (datetime.now() - timedelta(hours=max_age_hours)).isoformat()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM session_data WHERE updated_at < ?", (cutoff,))
        deleted = cursor.rowcount
        conn.commit()
        return deleted


# 初始化数据库
init_database()
