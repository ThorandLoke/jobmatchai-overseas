import zipfile
import re
import os

base_path = "/Users/weili/Desktop/红色 2T MyPassport 硬盘/Backup-20230330/weixin-backup/d1dd9a0cf03f41b31039d96dbe41d75d/Message/MessageTemp/22a99b83ede14f9f0c812c99b6c19e4a/File"
os.makedirs("ThorBooks/extracted", exist_ok=True)

def extract_epub(filepath):
    """从epub文件提取文本"""
    text_parts = []
    with zipfile.ZipFile(filepath, 'r') as zf:
        for name in zf.namelist():
            if name.endswith('.html') or name.endswith('.xhtml') or name.endswith('.htm') or name.endswith('.xml'):
                try:
                    content = zf.read(name).decode('utf-8', errors='ignore')
                    # 去除HTML标签
                    clean = re.sub(r'<[^>]+>', ' ', content)
                    clean = re.sub(r'\s+', ' ', clean).strip()
                    if len(clean) > 50:
                        text_parts.append(clean)
                except:
                    pass
    return ' '.join(text_parts)

# 提取刻意练习
print("正在提取《刻意练习》(epub)...")
filepath = f"{base_path}/(刻意练习).epub"
text = extract_epub(filepath)
print(f"提取到 {len(text)} 字符")
with open("ThorBooks/extracted/刻意练习.txt", 'w') as f:
    f.write(text)

print("\n=== 《刻意练习》前3000字 ===")
print(text[:3000])
