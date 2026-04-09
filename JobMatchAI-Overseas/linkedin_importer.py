"""
LinkedIn 职位导入模块 - JobMatchAI Nordic
支持从 LinkedIn 职位 URL 抓取解析职位信息

功能：
1. 解析 LinkedIn 职位链接
2. 提取职位名称、公司名、描述、地点
3. 自动检测语言（中/英/丹）
4. 支持用户手动粘贴职位详情（备用方案）

方案说明：
- LinkedIn 无公开职位 API，OAuth 仅限官方合作企业
- 采用 URL 抓取解析方案（使用多种请求头模拟浏览器）
- 备选方案：用户手动粘贴职位信息

Copyright © 2026 JobMatchAI. All rights reserved.
"""

import re
import json
import requests
from typing import Dict, Optional, Tuple
from urllib.parse import urlparse, parse_qs


class LinkedInImporter:
    """LinkedIn 职位导入器"""

    # LinkedIn 职位 URL 正则
    LINKEDIN_JOB_PATTERNS = [
        r'linkedin\.com/jobs/view/(\d+)',
        r'linkedin\.com/jobs-guest/jobs/api/jobPosting/(\d+)',
        r'linkedin\.com/jobs/search\?.*currentJobId=(\d+)',
        r'linkedin\.com/view/jpt/.*jobId=(\d+)',
    ]

    def __init__(self):
        self.session = requests.Session()
        # 多组 User-Agent 轮换使用
        self.user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.3 Safari/605.1.15',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        ]
        self.session.headers.update({
            'Accept-Language': 'en-US,en;q=0.9,da;q=0.8,zh-CN;q=0.7',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })

    def _get_random_ua(self) -> str:
        import random
        return random.choice(self.user_agents)

    def validate_url(self, url: str) -> Tuple[bool, str]:
        """验证是否为有效的 LinkedIn 职位 URL
        
        Returns:
            (is_valid, job_id_or_error_message)
        """
        url = url.strip()
        if not url:
            return False, "URL 不能为空"

        # 检查是否为 LinkedIn 域名
        parsed = urlparse(url)
        if 'linkedin.com' not in parsed.hostname.lower() if parsed.hostname else True:
            return False, "不是 LinkedIn 链接"

        # 提取 job ID
        for pattern in self.LINKEDIN_JOB_PATTERNS:
            match = re.search(pattern, url)
            if match:
                return True, match.group(1)

        # URL 可能是搜索页或其他 LinkedIn 页面
        if '/jobs/' in url:
            return False, "无法从此 LinkedIn 页面提取职位 ID，请使用具体职位页链接"

        return False, "不是有效的 LinkedIn 职位链接"

    def parse_linkedin_url(self, url: str) -> Dict:
        """解析 LinkedIn 职位 URL，提取职位信息

        Args:
            url: LinkedIn 职位链接

        Returns:
            {
                "success": True/False,
                "job": {
                    "title": "职位名称",
                    "company": "公司名",
                    "location": "地点",
                    "description": "职位描述",
                    "url": "原始链接",
                    "source": "LinkedIn",
                    "job_id": "职位ID",
                    "language": "语言代码"
                },
                "error": "错误信息（如有）"
            }
        """
        is_valid, result = self.validate_url(url)
        if not is_valid:
            return {"success": False, "error": result}

        job_id = result
        return self._fetch_job_details(url, job_id)

    def _fetch_job_details(self, url: str, job_id: str) -> Dict:
        """抓取 LinkedIn 职位页面详情"""
        self.session.headers['User-Agent'] = self._get_random_ua()

        # 尝试多种方式获取职位信息
        job_info = self._try_j2query_api(job_id)
        if job_info:
            job_info['url'] = url
            job_info['source'] = 'LinkedIn'
            return {"success": True, "job": job_info}

        # 备选：尝试直接抓取页面
        job_info = self._try_direct_scrape(url)
        if job_info:
            job_info['url'] = url
            job_info['source'] = 'LinkedIn'
            return {"success": True, "job": job_info}

        return {
            "success": False,
            "error": "无法自动解析此 LinkedIn 职位。请手动复制职位信息后粘贴到下方。",
            "job_id": job_id,
            "fallback": True
        }

    def _try_j2query_api(self, job_id: str) -> Optional[Dict]:
        """尝试通过 LinkedIn 内部 API 获取职位信息"""
        try:
            api_url = f"https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/{job_id}"
            self.session.headers['User-Agent'] = self._get_random_ua()
            resp = self.session.get(api_url, timeout=10)

            if resp.status_code == 200:
                html = resp.text
                return self._parse_job_html(html, job_id)
            elif resp.status_code == 401:
                # 需要登录 — 尝试另一种方式
                pass
        except Exception as e:
            print(f"LinkedIn J2Query API 失败: {e}")

        return None

    def _try_direct_scrape(self, url: str) -> Optional[Dict]:
        """尝试直接抓取职位页面"""
        try:
            self.session.headers['User-Agent'] = self._get_random_ua()
            resp = self.session.get(url, timeout=15)

            if resp.status_code == 200 and len(resp.text) > 500:
                return self._parse_job_html(resp.text, "")
        except Exception as e:
            print(f"LinkedIn 直接抓取失败: {e}")

        return None

    def _parse_job_html(self, html: str, job_id: str) -> Optional[Dict]:
        """从 LinkedIn HTML 页面提取职位信息

        LinkedIn 使用 JSON-LD 和 meta 标签存储结构化数据
        """
        job = {}

        # 方法1：解析 JSON-LD（LinkedIn 在页面中嵌入结构化数据）
        jsonld_pattern = r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>'
        for match in re.finditer(jsonld_pattern, html, re.DOTALL | re.IGNORECASE):
            try:
                data = json.loads(match.group(1))
                if data.get('@type') == 'JobPosting' or 'title' in data:
                    job['title'] = data.get('title', '')
                    job['company'] = ''
                    # 公司名称可能在 hiringOrganization 里
                    org = data.get('hiringOrganization', {})
                    if isinstance(org, dict):
                        job['company'] = org.get('name', '')
                    elif isinstance(org, str):
                        job['company'] = org
                    job['location'] = data.get('jobLocation', {}).get('address', {}).get('addressLocality', '')
                    if data.get('description'):
                        # 清理 HTML 标签
                        desc = data['description']
                        desc = re.sub(r'<[^>]+>', ' ', desc)
                        desc = re.sub(r'\s+', ' ', desc).strip()
                        job['description'] = desc[:3000]
                    if job.get('title'):
                        return job
            except json.JSONDecodeError:
                continue

        # 方法2：解析 meta 标签
        if not job.get('title'):
            title_match = re.search(r'<title[^>]*>(.*?)</title>', html, re.DOTALL)
            if title_match:
                title_text = title_match.group(1).strip()
                # LinkedIn 职位标题格式: "职位名 | LinkedIn" 或 "职位名 - Company | LinkedIn"
                if '|' in title_text:
                    parts = title_text.split('|')
                    job_part = parts[0].strip()
                    if ' - ' in job_part:
                        title_company = job_part.split(' - ', 1)
                        job['title'] = title_company[0].strip()
                        job['company'] = title_company[1].strip()
                    else:
                        job['title'] = job_part

        if not job.get('company'):
            og_company = re.search(r'<meta[^>]*property="og:company_name"[^>]*content="([^"]*)"', html)
            if og_company:
                job['company'] = og_company.group(1)

        if not job.get('title'):
            og_title = re.search(r'<meta[^>]*property="og:title"[^>]*content="([^"]*)"', html)
            if og_title:
                job['title'] = og_title.group(1).strip()

        if not job.get('description'):
            og_desc = re.search(r'<meta[^>]*property="og:description"[^>]*content="([^"]*)"', html)
            if og_desc:
                job['description'] = og_desc.group(1)

        if not job.get('location'):
            # 尝试从 class 中提取位置
            loc_match = re.search(r'class="[^"]*topcard__location[^"]*"[^>]*>(.*?)</span>', html, re.DOTALL)
            if loc_match:
                job['location'] = loc_match.group(1).strip()
            else:
                # 备选 meta
                og_loc = re.search(r'<meta[^>]*name="description"[^>]*content="([^"]*)"', html)
                if og_loc:
                    desc_text = og_loc.group(1)
                    loc_in_desc = re.search(r'([^|,\-]+?)(?:\s*[|\-]\s*LinkedIn)', desc_text)
                    if loc_in_desc:
                        job['location'] = loc_in_desc.group(1).strip()

        # 方法3：从页面数据中提取描述
        if not job.get('description') or len(job.get('description', '')) < 50:
            desc_match = re.search(r'<div[^>]*class="[^"]*show-more[^"]*"[^>]*>(.*?)</div>', html, re.DOTALL)
            if desc_match:
                desc_html = desc_match.group(1)
                desc_text = re.sub(r'<[^>]+>', '\n', desc_html)
                desc_text = re.sub(r'\n\s*\n', '\n', desc_text).strip()
                job['description'] = desc_text[:3000]

        if job.get('title'):
            job['job_id'] = job_id
            job['language'] = detect_job_language(job.get('description', ''))
            return job

        return None

    def parse_manual_input(self, text: str) -> Dict:
        """解析用户手动粘贴的职位信息

        支持多种格式：
        - LinkedIn 职位页面复制文本
        - 自由格式职位描述

        Args:
            text: 粘贴的职位信息文本

        Returns:
            结构化职位信息
        """
        text = text.strip()
        if not text:
            return {"success": False, "error": "内容不能为空"}

        job = {
            "title": "",
            "company": "",
            "location": "",
            "description": text,
            "url": "",
            "source": "手动输入",
            "language": detect_job_language(text)
        }

        # 尝试从文本中提取结构化信息

        # 提取公司名：常见格式
        company_patterns = [
            r'(?:公司|Company|Virksomhed)[:：]\s*(.+)',
            r'(?:at|at|hos)\s+([A-Z][A-Za-zæøåÆØÅ0-9\s\-&]+)',
            r'^([A-Z][A-Za-zæøåÆØÅ0-9\s\-&]{2,30})\n',
        ]
        for pattern in company_patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                company_candidate = match.group(1).strip()
                # 排除明显的非公司名
                if len(company_candidate) > 2 and not company_candidate.lower().startswith(('the ', 'we ', 'our ')):
                    job['company'] = company_candidate
                    break

        # 提取职位名称
        title_patterns = [
            r'(?:职位|Position|Stilling|Job Title)[:：]\s*(.+)',
            r'(?:职位名称|Title)[:：]\s*(.+)',
            r'^([A-Z][A-Za-zæøåÆØÅ\s\-/]+(?:Consultant|Engineer|Manager|Developer|Analyst|Specialist|Director|Coordinator|Advisor|Lead))',
        ]
        for pattern in title_patterns:
            match = re.search(pattern, text, re.MULTILINE | re.IGNORECASE)
            if match:
                job['title'] = match.group(1).strip()
                break

        # 如果标题还是空，取第一行作为标题（如果是短文本）
        if not job['title']:
            first_line = text.split('\n')[0].strip()
            if len(first_line) < 80 and not first_line.endswith(('.', '。')):
                job['title'] = first_line

        # 提取地点
        location_patterns = [
            r'(?:地点|Location|Lokation|Sted)[:：]\s*(.+)',
            r'(?:工作地点)[:：]\s*(.+)',
        ]
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                job['location'] = match.group(1).strip()
                break

        # 如果还缺少关键信息，用 AI 辅助提取（如果可用）
        if not job['title'] or not job['company']:
            extracted = self._extract_with_rules(text)
            if not job['title'] and extracted.get('title'):
                job['title'] = extracted['title']
            if not job['company'] and extracted.get('company'):
                job['company'] = extracted['company']
            if not job['location'] and extracted.get('location'):
                job['location'] = extracted['location']

        return {"success": True, "job": job}

    def _extract_with_rules(self, text: str) -> Dict:
        """基于规则从自由文本中提取职位信息"""
        result = {}
        lines = [l.strip() for l in text.split('\n') if l.strip()]

        # 第一行通常是职位名或公司名
        if lines:
            first = lines[0]
            # 如果第一行很短且看起来像公司名
            if 3 < len(first) < 40 and not any(w in first.lower() for w in ['we are', 'looking', 'seeking', 'vi leder', 'responsibilities', 'qualifications']):
                # 可能是 "公司名 - 职位名" 格式
                if ' - ' in first or ' – ' in first or ' | ' in first:
                    sep = ' - ' if ' - ' in first else (' – ' if ' – ' in first else ' | ')
                    parts = first.split(sep, 1)
                    if len(parts) == 2:
                        result['company'] = parts[0].strip()
                        result['title'] = parts[1].strip()
                    else:
                        result['title'] = first
                elif re.match(r'^[A-Z][A-Za-z\s&]+$', first):
                    result['company'] = first
                else:
                    result['title'] = first

        # 查找地点关键词
        danish_cities = ['København', 'Aarhus', 'Odense', 'Aalborg', 'Esbjerg', 'Randers', 'Kolding', 'Horsens',
                         'Vejle', 'Roskilde', 'Herning', 'Hørsholm', 'Gentofte', 'Lyngby', 'Ballerup',
                         'Glostrup', 'Herlev', 'Brøndby', 'Albertslund', 'Gladsaxe', 'Rødovre',
                         'Frederiksberg', 'Vanløse', 'Nordhavn', 'Østerbro', 'Vesterbro', 'Nørrebro',
                         'Amager', 'Islands Brygge', 'Harndrup', 'Middelfart', 'Sønderborg', 'Viborg']
        for city in danish_cities:
            if city.lower() in text.lower():
                result['location'] = city
                break

        # 查找常见城市关键词
        city_patterns = [
            r'(Copenhagen|Aarhus|Odense|Aalborg|Helsinki|Stockholm|Oslo|Berlin|Malmö|Gothenburg)',
            r'(哥本哈根|奥胡斯|奥尔胡斯|欧登塞|奥尔堡|斯德哥尔摩|奥斯陆|赫尔辛基)',
            r'(Denmark|Sweden|Norway|Finland|Germany)',
            r'(丹麦|瑞典|挪威|芬兰|德国)',
        ]
        for pattern in city_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['location'] = match.group(1)
                break

        return result


def detect_job_language(text: str) -> str:
    """检测职位描述语言

    Returns:
        'zh': 中文, 'en': 英文, 'da': 丹麦文
    """
    if not text:
        return 'en'

    # 只分析前 2000 字符
    text = text[:2000]
    text_lower = text.lower()

    # 中文检测
    zh_chars = len(re.findall(r'[\u4e00-\u9fff]', text))
    if zh_chars > 10:
        return 'zh'

    # 丹麦语独特特征（排除与英语重叠的词）
    da_unique_words = ['og', 'på', 'til', 'af', 'år', 'arbejde', 'konsulent', 'ansøgning',
                       'stilling', 'erfaring', 'virksomhed', 'ansvarlig', 'udvikling',
                       'implementering', 'projektledelse', 'kvalifikationer', 'ansættelse',
                       'arbejdsopgaver', 'vi tilbyder', 'du har', 'du vil', 'blive en del']
    da_count = sum(1 for w in da_unique_words if w in text_lower)

    # 瑞典语特征（排除误判）
    sv_unique_words = ['och', 'för', 'erfarenhet', 'konsult', 'ansökan', 'tjänst',
                       'arbetsuppgifter', 'kvalifikationer', 'vi erbjuder', 'du har']
    sv_count = sum(1 for w in sv_unique_words if w in text_lower)

    # 德语特征
    de_unique_words = ['bei', 'jahren', 'verantwortlich', 'berater', 'bewerbung',
                       'stellenangebot', 'wir bieten', 'sie haben', 'wir suchen',
                       'qualifikationen', 'aufgabenbereich', 'arbeitgeber']
    de_count = sum(1 for w in de_unique_words if w in text_lower)

    # 丹麦语特殊字符
    da_chars = len(re.findall(r'[æøåÆØÅ]', text))

    # 判定优先级
    if da_count >= 2 and da_count > sv_count and da_count > de_count:
        return 'da'
    if da_count >= 2 and da_chars >= 2:
        return 'da'
    if sv_count >= 2 and sv_count > da_count:
        return 'sv'
    if de_count >= 2 and de_count > da_count:
        return 'de'

    # 默认英语（LinkedIn 国际职位多用英语）
    return 'en'


# 全局实例
linkedin_importer = LinkedInImporter()
