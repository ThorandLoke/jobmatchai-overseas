"""
JobMatchAI Nordic - 邮件职位读取模块
支持从用户邮箱读取招聘邮件并提取职位信息

Copyright © 2026 JobMatchAI. All rights reserved.
"""
import imaplib
import email
from email.header import decode_header
from typing import List, Dict, Optional
import re

class JobEmailReader:
    """招聘邮件读取器"""
    
    # 支持的招聘平台发件人
    JOB_PLATFORMS = {
        # 国际平台
        'linkedin.com': 'LinkedIn',
        'jobindex.dk': 'Jobindex',
        'jobnet.dk': 'Jobnet',
        'stepstone.dk': 'StepStone',
        'stepstone.de': 'StepStone',
        'indeed.com': 'Indeed',
        'glassdoor.com': 'Glassdoor',
        'monster.com': 'Monster',
        'xing.com': 'Xing',
        # 中国平台
        'zhipin.com': 'BOSS直聘',
        'mail.zhipin.com': 'BOSS直聘',
        'zhaopin.com': '智联招聘',
        'mail.zhaopin.com': '智联招聘',
        '51job.com': '前程无忧',
        'mail.51job.com': '前程无忧',
        'liepin.com': '猎聘',
        'mail.liepin.com': '猎聘',
        'lagou.com': '拉勾网',
        'mail.lagou.com': '拉勾网',
        'mohrss.gov.cn': '中国公共招聘网',
    }
    
    # 中国招聘邮件主题关键词
    CHINA_JOB_KEYWORDS = [
        'BOSS直聘职位推荐',
        '有新的职位推荐给你',
        '智联招聘',
        '职位推荐',
        '高薪职位',
        '前程无忧',
        '51job推荐',
        '猎聘',
        '拉勾',
        '热门职位',
        '中国公共招聘网',
        '事业单位招聘',
    ]
    
    def __init__(self, email_address: str, password: str, imap_server: str = None):
        """
        初始化邮件读取器
        
        Args:
            email_address: 邮箱地址
            password: 邮箱密码或应用专用密码
            imap_server: IMAP服务器地址（自动检测常见邮箱）
        """
        self.email_address = email_address
        self.password = password
        self.imap_server = imap_server or self._detect_imap_server(email_address)
        self.mail = None
    
    def _detect_imap_server(self, email: str) -> str:
        """根据邮箱地址自动检测IMAP服务器"""
        domain = email.split('@')[1].lower()
        
        servers = {
            'gmail.com': 'imap.gmail.com',
            'outlook.com': 'outlook.office365.com',
            'hotmail.com': 'outlook.office365.com',
            'live.com': 'outlook.office365.com',
            'yahoo.com': 'imap.mail.yahoo.com',
            'icloud.com': 'imap.mail.me.com',
            'me.com': 'imap.mail.me.com',
            'qq.com': 'imap.qq.com',
            '163.com': 'imap.163.com',
            '126.com': 'imap.126.com',
        }
        
        return servers.get(domain, 'imap.' + domain)
    
    def connect(self) -> bool:
        """连接邮箱服务器"""
        try:
            self.mail = imaplib.IMAP4_SSL(self.imap_server)
            self.mail.login(self.email_address, self.password)
            return True
        except Exception as e:
            print(f"邮箱连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        if self.mail:
            self.mail.close()
            self.mail.logout()
    
    def is_job_email(self, sender: str, subject: str) -> bool:
        """
        判断是否为招聘邮件
        
        Args:
            sender: 发件人地址
            subject: 邮件主题
            
        Returns:
            是否为招聘邮件
        """
        sender_lower = sender.lower()
        subject_lower = subject.lower()
        
        # 检查发件人域名
        for domain in self.JOB_PLATFORMS.keys():
            if domain in sender_lower:
                return True
        
        # 检查中国招聘邮件主题关键词
        for keyword in self.CHINA_JOB_KEYWORDS:
            if keyword in subject:
                return True
        
        # 检查通用主题关键词
        job_keywords = [
            'job', 'jobs', 'position', 'career', 'hiring', 'recruitment',
            'stilling', 'jobansøgning', 'ansættelse',  # 丹麦语
            '职位', '招聘', '工作机会', '面试邀请',  # 中文
        ]
        
        for keyword in job_keywords:
            if keyword in subject_lower:
                return True
        
        return False
    
    def extract_job_info(self, email_body: str, subject: str, sender: str) -> Dict:
        """
        从邮件内容提取职位信息
        
        Args:
            email_body: 邮件正文
            subject: 邮件主题
            sender: 发件人
            
        Returns:
            职位信息字典
        """
        job_info = {
            'title': '',
            'company': '',
            'location': '',
            'description': '',
            'source': self._detect_source(sender),
            'url': '',
            'language': 'en'
        }
        
        # 从主题提取职位名称
        job_info['title'] = self._extract_job_title(subject)
        
        # 从正文提取信息
        job_info['company'] = self._extract_company(email_body)
        job_info['location'] = self._extract_location(email_body)
        job_info['description'] = self._extract_description(email_body)
        job_info['url'] = self._extract_url(email_body)
        job_info['language'] = self._detect_language(email_body)
        
        return job_info
    
    def _detect_source(self, sender: str) -> str:
        """检测职位来源平台"""
        sender_lower = sender.lower()
        for domain, name in self.JOB_PLATFORMS.items():
            if domain in sender_lower:
                return name
        return 'Email'
    
    def _extract_job_title(self, subject: str) -> str:
        """从主题提取职位名称"""
        # 移除常见前缀
        prefixes = [
            'New job:', 'Job alert:', 'Recommended job:',
            'Ny stilling:', 'Jobanbefaling:',  # 丹麦语
            '新职位:', '职位推荐:',  # 中文
        ]
        
        title = subject
        for prefix in prefixes:
            if prefix.lower() in title.lower():
                title = title.split(prefix)[-1].strip()
        
        # 移除方括号内容
        title = re.sub(r'\[.*?\]', '', title).strip()
        
        return title or 'Unknown Position'
    
    def _extract_company(self, body: str) -> str:
        """提取公司名称"""
        # 常见模式
        patterns = [
            r'(?:Company|Firma|公司)\s*[:：]\s*([^\n]+)',
            r'(?:at|hos|在)\s+([A-Z][A-Za-z0-9\s&]+)(?:\s+in|\s+location|$)',
            r'([A-Z][A-Za-z0-9\s&]+)\s+(?:is hiring|søger|招聘)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ''
    
    def _extract_location(self, body: str) -> str:
        """提取地点"""
        patterns = [
            r'(?:Location|Sted|地点)\s*[:：]\s*([^\n]+)',
            r'(?:in|i)\s+([A-Z][a-z]+(?:,\s*[A-Za-z]+)?)',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, body, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return ''
    
    def _extract_description(self, body: str) -> str:
        """提取职位描述"""
        # 清理HTML标签
        text = re.sub(r'<[^>]+>', ' ', body)
        
        # 提取前1000字符作为描述
        text = re.sub(r'\s+', ' ', text).strip()
        return text[:1500]
    
    def _extract_url(self, body: str) -> str:
        """提取职位链接"""
        # 匹配URL
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        match = re.search(url_pattern, body)
        if match:
            return match.group(0)
        return ''
    
    def _detect_language(self, text: str) -> str:
        """检测文本语言"""
        # 丹麦语特征
        da_patterns = ['æ', 'ø', 'å', 'og', 'det', 'en', 'er', 'til', 'på']
        da_count = sum(1 for p in da_patterns if p in text.lower())
        
        # 中文字符
        zh_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
        
        if da_count >= 3:
            return 'da'
        elif zh_chars > 50:
            return 'zh'
        else:
            return 'en'
    
    def fetch_job_emails(self, folder: str = 'INBOX', limit: int = 50) -> List[Dict]:
        """
        获取招聘邮件
        
        Args:
            folder: 邮箱文件夹
            limit: 最多读取邮件数
            
        Returns:
            职位信息列表
        """
        if not self.mail:
            if not self.connect():
                return []
        
        jobs = []
        
        try:
            # 选择文件夹
            self.mail.select(folder)
            
            # 搜索邮件（最近30天）
            _, search_data = self.mail.search(None, 'SINCE', '01-Jan-2026')
            email_ids = search_data[0].split()
            
            # 限制数量
            email_ids = email_ids[-limit:]
            
            for e_id in email_ids:
                _, msg_data = self.mail.fetch(e_id, '(RFC822)')
                raw_email = msg_data[0][1]
                
                # 解析邮件
                msg = email.message_from_bytes(raw_email)
                
                # 获取发件人和主题
                sender = self._decode_header(msg.get('From', ''))
                subject = self._decode_header(msg.get('Subject', ''))
                
                # 判断是否为招聘邮件
                if self.is_job_email(sender, subject):
                    # 获取邮件正文
                    body = self._get_email_body(msg)
                    
                    # 提取职位信息
                    job_info = self.extract_job_info(body, subject, sender)
                    job_info['email_date'] = msg.get('Date', '')
                    job_info['email_id'] = e_id.decode()
                    
                    jobs.append(job_info)
        
        except Exception as e:
            print(f"读取邮件失败: {e}")
        
        return jobs
    
    def _decode_header(self, header: str) -> str:
        """解码邮件头"""
        decoded_parts = decode_header(header)
        result = []
        
        for part, charset in decoded_parts:
            if isinstance(part, bytes):
                result.append(part.decode(charset or 'utf-8', errors='ignore'))
            else:
                result.append(part)
        
        return ' '.join(result)
    
    def _get_email_body(self, msg) -> str:
        """获取邮件正文"""
        body = ''
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == 'text/plain':
                    try:
                        body = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        break
                    except:
                        pass
                elif content_type == 'text/html':
                    try:
                        html = part.get_payload(decode=True).decode('utf-8', errors='ignore')
                        # 简单HTML到文本转换
                        body = re.sub(r'<[^>]+>', ' ', html)
                        break
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode('utf-8', errors='ignore')
            except:
                pass
        
        return body


# === 使用示例 ===
if __name__ == '__main__':
    # 示例：读取Gmail中的招聘邮件
    # 注意：Gmail需要使用应用专用密码
    
    reader = JobEmailReader(
        email_address='your.email@gmail.com',
        password='your-app-password',
    )
    
    # 获取职位
    jobs = reader.fetch_job_emails(limit=20)
    
    print(f"找到 {len(jobs)} 个职位")
    for job in jobs:
        print(f"\n--- {job['title']} ---")
        print(f"公司: {job['company']}")
        print(f"地点: {job['location']}")
        print(f"来源: {job['source']}")
        print(f"语言: {job['language']}")
    
    # 断开连接
    reader.disconnect()
