#!/usr/bin/env python3
"""
Thor 的书籍整理工具
扫描所有位置，建立完整书库目录
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

# 需要排除的关键词（非书籍文件）
EXCLUDE_KEYWORDS = [
    "payslip", "Payslip", "CV_", "cv_", "合同", "发票", "离职", "Offer", "offer",
    "申请", "Ansøgning", "Skade", "Indbo", "ePayslip", "工资单", "收据", "账单",
    "Certificate", "证件", "证明", "领英", "LinkedIn", "学位", "毕业", "结婚",
    "户口", "身份证", "护照", "签证", "驾照", "行驶证", "报名", "成绩", "考题",
    "试卷", "习题", "答案", "模板", "模版", "样例", "sample", "example",
    "Købsaftale", "sælgeroplysning", "Salgsbudget", "Formidlingsaftale",
    "Tilbudsbreve", "Ejerskifteforsikring", "Tilstandsrapport",
    "ePayslip", "Retsbog", "Anmodning", "Genoptagelse",
]

# 需要包含的扩展名
VALID_EXTENSIONS = ['.pdf', '.epub', '.mobi', '.azw3', '.txt']

def should_exclude(filepath):
    """检查是否应该排除"""
    filepath_lower = filepath.lower()
    for keyword in EXCLUDE_KEYWORDS:
        if keyword.lower() in filepath_lower:
            return True
    return False

def extract_book_info(filepath):
    """提取书籍信息"""
    filename = os.path.basename(filepath)
    name_without_ext = os.path.splitext(filename)[0]

    # 清理文件名
    clean_name = re.sub(r'[_-]+', ' ', name_without_ext)
    clean_name = re.sub(r'\s+', ' ', clean_name).strip()

    # 获取文件大小
    try:
        size = os.path.getsize(filepath)
        size_str = format_size(size)
    except:
        size_str = "Unknown"

    # 获取修改时间
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
        "modified": mdate,
        "extension": os.path.splitext(filename)[1].lower()
    }

def format_size(size):
    """格式化文件大小"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024.0:
            return f"{size:.1f} {unit}"
        size /= 1024.0
    return f"{size:.1f} TB"

def categorize_book(book_info):
    """根据书名分类书籍"""
    name = book_info["clean_name"].lower()

    # 投资/金融
    if any(kw in name for kw in ['投资', '股票', '巴菲特', '黄金', '理财', '金融', '聪明', 'money', 'invest', 'finance', 'stock', 'trading', '周期']):
        return "💰 投资金融"
    # 自我提升/管理
    elif any(kw in name for kw in ['高效能', '习惯', '原则', '领导力', '思维', '思考', '成长', '成功', 'habit', 'success', 'leadership', 'think']):
        return "🚀 自我提升"
    # 心理学/大脑
    elif any(kw in name for kw in ['心理', '大脑', '情绪', 'emotion', 'brain', 'psychology', 'mind', '自我', '亲密']):
        return "🧠 心理学/大脑"
    # 信仰/宗教
    elif any(kw in name for kw in ['信仰', '神', '基督', '圣经', '上帝', 'church', 'christian', 'bible', 'god', '灵', '希伯来', '保罗', '罗马']):
        return "⛪ 信仰/宗教"
    # 育儿/教育
    elif any(kw in name for kw in ['父母', '育儿', '孩子', '教育', 'parent', 'kids', 'children', 'family', 'parenting']):
        return "👨‍👩‍👧 育儿/家庭"
    # 科技/商业
    elif any(kw in name for kw in ['科技', '技术', '商业', 'business', 'tech', 'digital', 'future', 'AI', '时代', '衰退']):
        return "💡 科技/商业"
    # 儿童读物
    elif any(kw in name for kw in ['儿童', '孩子', '绘本', '童话', 'kid', 'picture book', 'story', 'Smile', 'Lauren']):
        return "📚 儿童读物"
    # 历史/传记
    elif any(kw in name for kw in ['历史', '传记', '航海', 'colon', 'history', 'magellan', '周金涛', '周期']):
        return "📜 历史/传记"
    else:
        return "📖 其他"

def scan_books():
    """扫描所有书籍"""
    all_books = []
    seen_names = {}  # 用于检测重复书名

    for search_path in SEARCH_PATHS:
        if not os.path.exists(search_path):
            continue

        print(f"🔍 扫描: {search_path}")

        for root, dirs, files in os.walk(search_path):
            # 跳过排除目录
            dirs[:] = [d for d in dirs if not any(excl.lower() in d.lower() for excl in EXCLUDE_KEYWORDS)]

            for filename in files:
                filepath = os.path.join(root, filename)

                # 检查扩展名
                ext = os.path.splitext(filename)[1].lower()
                if ext not in VALID_EXTENSIONS:
                    continue

                # 检查是否应该排除
                if should_exclude(filepath):
                    continue

                # 提取书籍信息
                book_info = extract_book_info(filepath)

                # 检测重复
                name_key = book_info["clean_name"].lower()
                if name_key in seen_names:
                    book_info["duplicate_of"] = seen_names[name_key]
                else:
                    seen_names[name_key] = filepath

                # 分类
                book_info["category"] = categorize_book(book_info)

                all_books.append(book_info)

    return all_books

def generate_report(books):
    """生成整理报告"""

    # 按分类统计
    categories = {}
    for book in books:
        cat = book["category"]
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(book)

    # 统计信息
    total = len(books)
    duplicates = sum(1 for b in books if "duplicate_of" in b)

    report = f"""# 📚 Thor 的个人书库目录

> 生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}

## 📊 统计概览

- **总书籍数**: {total} 本
- **独立书名**: {total - duplicates} 本
- **重复版本**: {duplicates} 本

## 📁 按分类统计

"""

    for cat in sorted(categories.keys()):
        books_in_cat = categories[cat]
        report += f"\n### {cat} ({len(books_in_cat)} 本)\n\n"
        for book in sorted(books_in_cat, key=lambda x: x["clean_name"]):
            dup_mark = " [🔄 重复]" if "duplicate_of" in book else ""
            report += f"- **{book['clean_name']}**{dup_mark}\n"
            report += f"  - 格式: {book['extension']} | 大小: {book['size']} | 修改: {book['modified']}\n"
            report += f"  - 路径: `{book['path'][:80]}...`\n" if len(book['path']) > 80 else f"  - 路径: `{book['path']}`\n"

    report += """

## 📋 完整书单（按文件名）

"""

    # 按文件路径排序的完整列表
    for i, book in enumerate(sorted(books, key=lambda x: x["path"]), 1):
        dup_mark = " [🔄]" if "duplicate_of" in book else ""
        report += f"{i}. {book['clean_name']}{dup_mark}\n"

    report += f"""

## 💡 说明

- 重复版本保留原位置，不删除
- 分类仅供参考，部分书籍可能涉及多个主题
- 部分书籍可能需要下载阅读器才能打开

## 🔧 待办

- [ ] 确认 807 本书的完整位置
- [ ] 整理云端书库（如有）
- [ ] 补充缺失元数据（作者、出版社、ISBN）
"""

    return report

def main():
    print("📚 Thor 的书籍整理工具")
    print("=" * 50)

    # 扫描书籍
    books = scan_books()

    print(f"\n✅ 扫描完成，共找到 {len(books)} 本书")

    # 生成报告
    report = generate_report(books)

    # 保存报告
    report_path = "/Users/weili/WorkBuddy/Claw/ThorBooks/书库目录.md"
    os.makedirs(os.path.dirname(report_path), exist_ok=True)

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"📄 报告已保存: {report_path}")

    # 同时生成 JSON 数据
    json_path = "/Users/weili/WorkBuddy/Claw/ThorBooks/books.json"
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(books, f, ensure_ascii=False, indent=2)

    print(f"📊 JSON 数据: {json_path}")

    return books

if __name__ == "__main__":
    main()
