import zipfile
import re
import os

base_path = "/Users/weili/Desktop/红色 2T MyPassport 硬盘/Backup-20230330/weixin-backup/d1dd9a0cf03f41b31039d96dbe41d75d/Message/MessageTemp/22a99b83ede14f9f0c812c99b6c19e4a/File"
os.makedirs("ThorBooks/extracted", exist_ok=True)

def extract_epub(filepath):
    text_parts = []
    with zipfile.ZipFile(filepath, 'r') as zf:
        for name in zf.namelist():
            if name.endswith(('.html', '.xhtml', '.htm')):
                try:
                    content = zf.read(name).decode('utf-8', errors='ignore')
                    clean = re.sub(r'<[^>]+>', ' ', content)
                    clean = re.sub(r'\s+', ' ', clean).strip()
                    if len(clean) > 50:
                        text_parts.append(clean)
                except:
                    pass
    return ' '.join(text_parts)

# 提取更多epub书籍
books = [
    ("5%的改变.epub", "5%的改变"),
    ("傲慢与偏见.epub", "傲慢与偏见"),
    ("精神与爱欲.epub", "精神与爱欲"),
]

for filename, bookname in books:
    filepath = f"{base_path}/{filename}"
    if os.path.exists(filepath):
        print(f"正在提取《{bookname}》...")
        text = extract_epub(filepath)
        print(f"  提取到 {len(text)} 字符")
        with open(f"ThorBooks/extracted/{bookname}.txt", 'w') as f:
            f.write(text)
    else:
        print(f"《{bookname}》文件不存在")

print("\n已完成所有epub提取")
