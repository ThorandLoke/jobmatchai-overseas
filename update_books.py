import json
import os

# 现有书库
with open('ThorBooks/books.json', 'r') as f:
    existing_books = json.load(f)

existing_names = {b['clean_name'] for b in existing_books}

# 移动硬盘上的新书
hdd_books = [
    {'name': '刻意练习', 'clean_name': '刻意练习', 'category': '学习方法', 'format': 'epub', 'size': '7MB', 'kids_value': 5},
    {'name': '穷查理宝典（完整版）', 'clean_name': '穷查理宝典', 'category': '思维模型', 'format': 'mobi', 'size': '623KB', 'kids_value': 5},
    {'name': '纳瓦尔宝典', 'clean_name': '纳瓦尔宝典', 'category': '财富/幸福', 'format': 'mobi', 'size': '827KB', 'kids_value': 5},
    {'name': '当下的力量', 'clean_name': '当下的力量', 'category': '心灵/情绪', 'format': 'mobi', 'size': '391KB', 'kids_value': 4},
    {'name': '5%的改变', 'clean_name': '5%的改变', 'category': '心理学', 'format': 'epub/pdf', 'size': '3.7MB', 'kids_value': 4},
    {'name': '乌合之众', 'clean_name': '乌合之众', 'category': '社会心理学', 'format': 'pdf', 'size': '1.9MB', 'kids_value': 4},
    {'name': '置身事内', 'clean_name': '置身事内', 'category': '经济/政治', 'format': 'mobi', 'size': '3MB', 'kids_value': 4},
    {'name': '战略历程', 'clean_name': '战略历程', 'category': '商业/战略', 'format': 'mobi', 'size': '8.5MB', 'kids_value': 4},
    {'name': '怪诞行为学', 'clean_name': '怪诞行为学', 'category': '行为经济', 'format': 'pdf', 'size': '47MB', 'kids_value': 4},
    {'name': '洞察力的秘密', 'clean_name': '洞察力的秘密', 'category': '决策科学', 'format': 'azw3', 'size': '4.6KB', 'kids_value': 5},
    {'name': '王阳明一切心法', 'clean_name': '王阳明一切心法', 'category': '东方智慧', 'format': 'mobi', 'size': '1.4MB', 'kids_value': 4},
    {'name': '王阳明的六次突围', 'clean_name': '王阳明的六次突围', 'category': '东方智慧', 'format': 'mobi', 'size': '970KB', 'kids_value': 4},
    {'name': '王阳明心学', 'clean_name': '王阳明心学', 'category': '东方智慧', 'format': 'mobi', 'size': '1.4MB', 'kids_value': 4},
    {'name': '王阳明的心学功夫', 'clean_name': '王阳明的心学功夫', 'category': '东方智慧', 'format': 'mobi', 'size': '720KB', 'kids_value': 4},
    {'name': '孙子略解', 'clean_name': '孙子略解', 'category': '东方智慧', 'format': 'txt', 'size': '35KB', 'kids_value': 3},
]

# 添加新书
new_count = 0
for book in hdd_books:
    if book['clean_name'] not in existing_names:
        book['source'] = 'My Passport'
        book['added_date'] = '2026-04-10'
        new_count += 1
        existing_books.append(book)

print(f"添加了 {new_count} 本新书")
print(f"书库总计: {len(existing_books)} 本")

with open('ThorBooks/books.json', 'w') as f:
    json.dump(existing_books, f, ensure_ascii=False, indent=2)

print("已更新 ThorBooks/books.json")
