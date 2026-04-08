"""
用户数据收集模块 - Early Bird Beta 测试
用于收集用户提交的简历、职位链接、社交账号等信息，
帮助优化算法和积累训练数据。

收集的数据：
- 简历文本/文件
- 已申请/关注的职位链接
- 社交媒体账号（LinkedIn、GitHub等）
- 联系方式
- 求职目标

所有数据用于本地AI处理，不会泄露给第三方。
"""

import json
import os
import sqlite3
import uuid
import subprocess
from datetime import datetime
from typing import List, Optional, Dict
from dataclasses import dataclass, asdict
from pathlib import Path

# 邮件通知配置
NOTIFY_EMAIL = os.getenv("NOTIFY_EMAIL", "wei.li@outlook.dk")
NOTIFY_ENABLED = os.getenv("NOTIFY_ENABLED", "false").lower() == "true"

def send_notification_email(submission: Dict) -> bool:
    """当有新提交时发送邮件通知"""
    if not NOTIFY_ENABLED:
        print(f"📧 新提交通知（通知已禁用）: {submission.get('email', 'N/A')}")
        return False

    try:
        email_body = f"""
🎉 新的 Early Bird Beta 提交！

📧 邮箱: {submission.get('email', 'N/A')}
👤 姓名: {submission.get('name', '未填写')}
📱 电话: {submission.get('phone', '未填写')}
🌍 国家/城市: {submission.get('country', '')} / {submission.get('city', '')}

📎 简历: {'有' if submission.get('resumes') else '无'}
🔗 职位链接: {len(submission.get('job_links', []))} 个
💬 备注: {submission.get('notes', '无')}

🆔 提交ID: {submission.get('id', 'N/A')}
⏰ 时间: {submission.get('created_at', 'N/A')}

---
直接回复此邮件查看详情
        """.strip()

        # 使用 SMTP 发送邮件
        result = subprocess.run([
            "node",
            "/Users/weili/.workbuddy/skills/imap-smtp-email/scripts/smtp.js",
            "send",
            "--to", NOTIFY_EMAIL,
            "--subject", f"🎉 新Beta测试提交: {submission.get('email', 'N/A')}",
            "--body", email_body
        ], capture_output=True, text=True, timeout=30)

        if result.returncode == 0:
            print(f"✅ 邮件通知已发送: {submission.get('email', 'N/A')}")
            return True
        else:
            print(f"⚠️ 邮件通知发送失败: {result.stderr}")
            return False

    except Exception as e:
        print(f"⚠️ 发送通知邮件失败: {e}")
        return False

# 数据库路径
DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
os.makedirs(DATA_DIR, exist_ok=True)
DB_PATH = os.path.join(DATA_DIR, "submissions.db")


def init_database():
    """初始化SQLite数据库"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 用户提交表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id TEXT PRIMARY KEY,
            email TEXT NOT NULL,
            name TEXT,
            phone TEXT,
            country TEXT,
            city TEXT,
            created_at TEXT NOT NULL,
            status TEXT DEFAULT 'pending',
            notes TEXT,
            source TEXT DEFAULT 'website'
        )
    """)
    
    # 简历表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS resumes (
            id TEXT PRIMARY KEY,
            submission_id TEXT NOT NULL,
            raw_text TEXT,
            file_name TEXT,
            file_path TEXT,
            parsed_data TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (submission_id) REFERENCES submissions(id)
        )
    """)
    
    # 职位链接表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS job_links (
            id TEXT PRIMARY KEY,
            submission_id TEXT NOT NULL,
            url TEXT,
            company TEXT,
            job_title TEXT,
            platform TEXT,
            status TEXT DEFAULT 'saved',
            notes TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (submission_id) REFERENCES submissions(id)
        )
    """)
    
    # 社交账号表
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS social_accounts (
            id TEXT PRIMARY KEY,
            submission_id TEXT NOT NULL,
            platform TEXT NOT NULL,
            username TEXT,
            profile_url TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (submission_id) REFERENCES submissions(id)
        )
    """)
    
    # 处理记录表（追踪我们的处理进度）
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processing_log (
            id TEXT PRIMARY KEY,
            submission_id TEXT NOT NULL,
            action TEXT NOT NULL,
            result TEXT,
            processed_at TEXT NOT NULL,
            FOREIGN KEY (submission_id) REFERENCES submissions(id)
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"✅ 数据库初始化完成: {DB_PATH}")


# 初始化数据库
init_database()


@dataclass
class UserSubmission:
    """用户提交记录"""
    id: str
    email: str
    name: str
    phone: str
    country: str
    city: str
    created_at: str
    status: str
    notes: str
    source: str

    def to_dict(self) -> Dict:
        return asdict(self)


class EarlyBirdCollector:
    """早期测试数据收集器"""

    def __init__(self):
        self.db_path = DB_PATH

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def submit_form(
        self,
        email: str,
        name: str = "",
        phone: str = "",
        country: str = "",
        city: str = "",
        resume_text: str = "",
        resume_file_name: str = "",
        job_links: List[Dict] = None,
        social_accounts: List[Dict] = None,
        notes: str = "",
        source: str = "website"
    ) -> Dict:
        """提交表单数据
        
        Args:
            email: 用户邮箱（必填）
            name: 姓名
            phone: 电话
            country: 国家
            city: 城市
            resume_text: 简历文本
            resume_file_name: 简历文件名
            job_links: 职位链接列表 [{"url": "", "company": "", "title": "", "platform": ""}]
            social_accounts: 社交账号列表 [{"platform": "", "username": "", "url": ""}]
            notes: 备注
            source: 来源（website/xiaohongshu/xiianyu/facebook）
        
        Returns:
            提交结果
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 1. 创建提交记录
            submission_id = str(uuid.uuid4())[:8].upper()
            created_at = datetime.now().isoformat()

            cursor.execute("""
                INSERT INTO submissions (id, email, name, phone, country, city, created_at, status, notes, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (submission_id, email, name, phone, country, city, created_at, "pending", notes, source))

            # 2. 保存简历
            if resume_text or resume_file_name:
                resume_id = str(uuid.uuid4())[:8].upper()
                cursor.execute("""
                    INSERT INTO resumes (id, submission_id, raw_text, file_name, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (resume_id, submission_id, resume_text, resume_file_name, created_at))

            # 3. 保存职位链接
            if job_links:
                for link in job_links:
                    if link.get("url"):
                        link_id = str(uuid.uuid4())[:8].upper()
                        cursor.execute("""
                            INSERT INTO job_links (id, submission_id, url, company, job_title, platform, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            link_id,
                            submission_id,
                            link.get("url", ""),
                            link.get("company", ""),
                            link.get("title", ""),
                            link.get("platform", ""),
                            created_at
                        ))

            # 4. 保存社交账号
            if social_accounts:
                for account in social_accounts:
                    if account.get("platform"):
                        account_id = str(uuid.uuid4())[:8].upper()
                        cursor.execute("""
                            INSERT INTO social_accounts (id, submission_id, platform, username, profile_url, created_at)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            account_id,
                            submission_id,
                            account.get("platform", ""),
                            account.get("username", ""),
                            account.get("url", ""),
                            created_at
                        ))

            conn.commit()

            # 获取完整提交信息用于通知
            full_submission = self.get_submission(submission_id) or {}

            # 发送邮件通知
            send_notification_email(full_submission)

            return {
                "success": True,
                "submission_id": submission_id,
                "message": "提交成功！我们会尽快处理您的信息。",
                "email": email,
                "created_at": created_at
            }

        except Exception as e:
            conn.rollback()
            return {
                "success": False,
                "error": str(e)
            }
        finally:
            conn.close()

    def get_submission(self, submission_id: str) -> Optional[Dict]:
        """获取提交详情"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 获取基本信息
            cursor.execute("SELECT * FROM submissions WHERE id = ?", (submission_id,))
            row = cursor.fetchone()
            if not row:
                return None

            columns = [desc[0] for desc in cursor.description]
            submission = dict(zip(columns, row))

            # 获取简历
            cursor.execute("SELECT * FROM resumes WHERE submission_id = ?", (submission_id,))
            resume_rows = cursor.fetchall()
            resume_columns = [desc[0] for desc in cursor.description]
            submission["resumes"] = [dict(zip(resume_columns, r)) for r in resume_rows]

            # 获取职位链接
            cursor.execute("SELECT * FROM job_links WHERE submission_id = ?", (submission_id,))
            link_rows = cursor.fetchall()
            link_columns = [desc[0] for desc in cursor.description]
            submission["job_links"] = [dict(zip(link_columns, l)) for l in link_rows]

            # 获取社交账号
            cursor.execute("SELECT * FROM social_accounts WHERE submission_id = ?", (submission_id,))
            account_rows = cursor.fetchall()
            account_columns = [desc[0] for desc in cursor.description]
            submission["social_accounts"] = [dict(zip(account_columns, a)) for a in account_rows]

            return submission

        finally:
            conn.close()

    def list_submissions(
        self,
        status: str = "all",
        source: str = "all",
        limit: int = 50
    ) -> List[Dict]:
        """获取提交列表"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            query = "SELECT * FROM submissions WHERE 1=1"
            params = []

            if status != "all":
                query += " AND status = ?"
                params.append(status)

            if source != "all":
                query += " AND source = ?"
                params.append(source)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            cursor.execute(query, params)
            rows = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

            return [dict(zip(columns, r)) for r in rows]

        finally:
            conn.close()

    def update_status(self, submission_id: str, status: str, notes: str = "") -> bool:
        """更新处理状态"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            if notes:
                cursor.execute(
                    "UPDATE submissions SET status = ?, notes = ? WHERE id = ?",
                    (status, notes, submission_id)
                )
            else:
                cursor.execute(
                    "UPDATE submissions SET status = ? WHERE id = ?",
                    (status, submission_id)
                )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def log_processing(self, submission_id: str, action: str, result: str = "") -> bool:
        """记录处理日志"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            log_id = str(uuid.uuid4())[:8].upper()
            cursor.execute("""
                INSERT INTO processing_log (id, submission_id, action, result, processed_at)
                VALUES (?, ?, ?, ?, ?)
            """, (log_id, submission_id, action, result, datetime.now().isoformat()))
            conn.commit()
            return True
        finally:
            conn.close()

    def get_statistics(self) -> Dict:
        """获取统计数据"""
        conn = self._get_connection()
        cursor = conn.cursor()

        try:
            # 总提交数
            cursor.execute("SELECT COUNT(*) FROM submissions")
            total = cursor.fetchone()[0]

            # 按状态统计
            cursor.execute("SELECT status, COUNT(*) FROM submissions GROUP BY status")
            status_stats = dict(cursor.fetchall())

            # 按来源统计
            cursor.execute("SELECT source, COUNT(*) FROM submissions GROUP BY source")
            source_stats = dict(cursor.fetchall())

            # 有简历的提交数
            cursor.execute("SELECT COUNT(DISTINCT submission_id) FROM resumes")
            with_resume = cursor.fetchone()[0]

            # 有职位链接的提交数
            cursor.execute("SELECT COUNT(DISTINCT submission_id) FROM job_links")
            with_jobs = cursor.fetchone()[0]

            # 今日提交
            today = datetime.now().strftime("%Y-%m-%d")
            cursor.execute(
                "SELECT COUNT(*) FROM submissions WHERE created_at LIKE ?",
                (f"{today}%",)
            )
            today_count = cursor.fetchone()[0]

            return {
                "total_submissions": total,
                "status_breakdown": status_stats,
                "source_breakdown": source_stats,
                "with_resume": with_resume,
                "with_job_links": with_jobs,
                "today_submissions": today_count
            }
        finally:
            conn.close()


# 初始化收集器
collector = EarlyBirdCollector()
