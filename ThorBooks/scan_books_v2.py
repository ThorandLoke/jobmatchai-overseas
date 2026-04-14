#!/usr/bin/env python3
"""
Thor 的书籍整理工具 v2
更好的中文支持分类
"""

import os
import re
from pathlib import Path
from datetime import datetime
import json

# 定义所有搜索路径
SEARCH_PATHS = [
    "/Users/weili/Downloads",
    "/Users/weili/Desktop",
    "/Users/weili/Documents",
    "/Users/weili/Library/Mobile Documents",
    "/Users/weili/Desktop/红色 2T MyPassport 硬盘/Backup-20230330/iCloud 云盘（归档）",
]

# 需要排除的关键词
EXCLUDE_KEYWORDS = [
    "payslip", "Payslip", "CV_", "cv_", "合同", "发票", "离职", "Offer", "offer",
    "申请", "Ansøgning", "Skade", "Indbo", "ePayslip", "工资单", "收据", "账单",
    "Certificate", "证件", "证明", "领英", "LinkedIn", "学位", "毕业", "结婚",
    "户口", "身份证", "护照", "签证", "驾照", "行驶证", "报名", "成绩", "考题",
    "试卷", "习题", "答案", "template", "模版", "样例", "sample",
    "Købsaftale", "sælgeroplysning", "Salgsbudget", "Formidlingsaftale",
    "Tilbudsbreve", "Ejerskifteforsikring", "Tilstandsrapport",
    "ePayslip", "Retsbog", "Anmodning", "Genoptagelse", "download",
    "调档函", "纳税记录", "应税收入", "个人所得税", "税",
]

VALID_EXTENSIONS = ['.pdf', '.epub', '.mobi', '.azw3']

def should_exclude(filepath):
    filepath_lower = filepath.lower()
    for keyword in EXCLUDE_KEYWORDS:
        if keyword.lower() in filepath_lower:
            return True
    return False

def extract_book_info(filepath):
    filename = os.path.basename(filepath)
    name_without_ext = os.path.splitext(filename)[0]
    clean_name = re.sub(r'[_-]+', ' ', name_without_ext)
    clean_name = re.sub(r'\s+', ' ', clean_name).strip()

    try:
        size = os.path.getsize(filepath)
        size_str = format_size(size)
    except:
        size_str = "Unknown"

    try:
        mtime = os.path.getmtime(filepath)
        mdate = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
    except:
        mdate = "Unknown"

    return {
        "filename": filename,
        "clean_name": clean_name,
        "path": filepath,
        "size": size_str,
        "size_bytes": os.path.getsize(filepath) if os.path.exists(filepath) else 0,
        "modified": mdate,
        "extension": os.path.splitext(filename)[1].lower()
    }

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def categorize_book(book_info):
    """根据书名智能分类"""
    name = book_info["clean_name"].lower()

    # 投资/金融 (优先)
    if any(kw in name for kw in ['投资', '股票', '巴菲特', '黄金', '理财', '金融', 'money', 'invest', 'finance', 'stock', 'trading', '债券', 'bank']):
        return "💰 投资金融"
    # 穷查理/纳瓦尔
    elif any(kw in name for kw in ['穷查理', '纳瓦尔', '芒格']):
        return "🧠 思维智慧"
    # 思维/自我提升
    elif any(kw in name for kw in ['思维', '思考', '高效能', '七个习惯', '原则', '领导力', '成长', '成功', 'habit', 'success', 'leadership', 'think', '认知']):
        return "🚀 自我提升"
    # 心理学/大脑
    elif any(kw in name for kw in ['心理', '大脑', '情绪', 'emotion', 'brain', 'psychology', 'mind', '心智', '心智']):
        return "🧠 心理学/大脑"
    # 信仰/宗教
    elif any(kw in name for kw in ['信仰', '神', '基督', '圣经', '上帝', 'church', 'christian', 'bible', 'god', '灵', '希伯来', '保罗', '罗马', '祷告', '教会', '牧师', '耶稣', '新生命']):
        return "⛪ 信仰/宗教"
    # 科学/科普
    elif any(kw in name for kw in ['科学', '物理', '生物', '化学', '医学', '病毒', '进化', '生命', '大脑', '科普', 'science', 'physics', 'biology']):
        return "🔬 科学/科普"
    # 数学
    elif any(kw in name for kw in ['数学', 'math', '统计', '概率']):
        return "🔢 数学"
    # 育儿/教育
    elif any(kw in name for kw in ['父母', '育儿', '孩子', '教育', 'parent', 'kids', 'children', 'family', ' parenting', '绘本', '妻子', '婚姻', '亲密']):
        return "👨‍👩‍👧 育儿/家庭"
    # 商业/管理
    elif any(kw in name for kw in ['商业', 'business', '管理', '创业', '企业', '战略', 'marketing', '营销', '冲突', '叶茂中']):
        return "💼 商业/管理"
    # 科技/数字
    elif any(kw in name for kw in ['科技', '技术', 'tech', 'digital', 'future', 'AI', '时代', '数字', '互联网', '计算机']):
        return "💡 科技/数字"
    # 儿童/绘本
    elif any(kw in name for kw in ['绘本', '童话', '儿童', 'kid', 'picture book', 'story', 'Smile', 'Lauren', '小说', '文学', '文学']):
        return "📚 儿童/文学"
    # 历史/传记
    elif any(kw in name for kw in ['历史', '传记', '航海', 'colon', 'history', 'magellan', '周金涛', '周期', '民国', '老鼠', '金雀花', '不平等']):
        return "📜 历史/传记"
    # 医学/健康
    elif any(kw in name for kw in ['医学', '健康', '医生', '减肥', '高血', '高血', '高尿', 'medical', 'health', '跑法', '健身']):
        return "🏥 医学/健康"
    else:
        return "📖 其他"

def scan_books():
    all_books = []
    seen_names = {}

    for search_path in SEARCH_PATHS:
        if not os.path.exists(search_path):
            continue

        print(f"🔍 扫描: {search_path}")

        for root, dirs, files in os.walk(search_path):
            dirs[:] = [d for d in dirs if not any(excl.lower() in d.lower() for excl in EXCLUDE_KEYWORDS)]

            for filename in files:
                filepath = os.path.join(root, filename)
                ext = os.path.splitext(filename)[1].lower()
                if ext not in VALID_EXTENSIONS:
                    continue
                if should_exclude(filepath):
                    continue

                book_info = extract_book_info(filepath)
                name_key = book_info["clean_name"].lower()
                if name_key in seen_names:
                    book_info["duplicate_of"] = seen_names[name_key]
                else:
                    seen_names[name_key] = filepath

                book_info["category"] = categorize_book(book_info)
                all_books.append(book_info)

    return all_books

def generate_report(books):
    categories = {}
    for book in books:
        cat = book["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(book)

    total = len(books)
    duplicates = sum(1 for b in books if "duplicate_of" in b)
    total_size = sum(b["size_bytes"] for b in books)

    report = f"""# 📚 Thor 的个人书库目录

> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}
> 扫描位置: Downloads, Desktop, Documents, iCloud

---

## 📊 统计概览

| 项目 | 数量 |
|------|------|
| 总书籍数 | {total} 本 |
| 独立书名 | {total - duplicates} 本 |
| 重复版本 | {duplicates} 本 |
| 总占用空间 | {format_size(total_size)} |

---

## 📁 分类目录

"""

    # 按数量排序
    sorted_cats = sorted(categories.items(), key=lambda x: len(x[1]), reverse=True)

    for cat, cat_books in sorted_cats:
        report += f"\n### {cat} ({len(cat_books)} 本)\n\n"
        for book in sorted(cat_books, key=lambda x: x["clean_name"]):
            dup_mark = " 🔄" if "duplicate_of" in book else ""
            report += f"- **{book['clean_name']}**{dup_mark}\n"
            report += f"  - {book['extension']} | {book['size']}\n"

    # 重点书籍推荐（适合 Kids365Science 的）
    report += """

---

## ⭐ Kids365Science 重点书籍

以下是适合开发儿童财商、思维训练内容的核心书籍：

"""

    key_keywords = ['穷查理', '纳瓦尔', '巴菲特', '黄金', '投资', '思维', '思考', '高效能',
                   '科学', '物理', '生物', '数学', '进化', '生命', '经济', '周期',
                   '心理', '大脑', '情绪', '历史', '哲学', '芒格']

    key_books = [b for b in books if any(kw.lower() in b['clean_name'].lower() for kw in key_keywords)]
    key_books = sorted(key_books, key=lambda x: x['clean_name'])

    for i, book in enumerate(key_books, 1):
        dup_mark = " 🔄" if "duplicate_of" in book else ""
        report += f"{i}. **{book['clean_name']}**{dup_mark} [{book['category']}]\n"

    report += f"""

---

## 📋 完整书单

"""

    for i, book in enumerate(sorted(books, key=lambda x: x["path"]), 1):
        dup_mark = " 🔄" if "duplicate_of" in book else ""
        report += f"{i}. {book['clean_name']}{dup_mark}\n"

    report += f"""

---

## 💡 说明

- 重复版本保留原位置，不删除
- 部分微信备份中的文件可能是从网络下载的
- 建议定期备份重要书籍到云端

## 🔧 下一步

- [ ] 确认 807 本书的完整位置
- [ ] 深入阅读重点书籍，提取儿童教育内容
- [ ] 定期更新书库目录
"""

    return report

def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def main():
    print("📚 Thor 的书籍整理工具 v2")
    print("=" * 50)

    books = scan_books()
    print(f"\n✅ 扫描完成，共找到 {len(books)} 本书")

    report = generate_report(books)

    report_path = "/Users/weili/WorkBuddy/Claw/ThorBooks/书库目录.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f"📄 报告已保存: {report_path}")

    json_path = "/Users/weili/WorkBuddy/Claw/ThorBooks/books.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(books, f, ensure_ascii=False, indent=2)
    print(f"📊 JSON 数据: {json_path}")

    return books

if __name__ == "__main__":
    main()
