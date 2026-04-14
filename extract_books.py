import struct
import re
import os

base_path = "/Users/weili/Desktop/红色 2T MyPassport 硬盘/Backup-20230330/weixin-backup/d1dd9a0cf03f41b31039d96dbe41d75d/Message/MessageTemp/22a99b83ede14f9f0c812c99b6c19e4a/File"

os.makedirs("ThorBooks/extracted", exist_ok=True)

def extract_mobi(filepath):
    """从mobi文件提取文本"""
    with open(filepath, 'rb') as f:
        data = f.read()
    
    # 读取记录偏移表
    num_records = struct.unpack_from('>H', data, 76)[0]
    records = []
    for i in range(num_records):
        offset, attrs = struct.unpack_from('>LL', data, 78 + i * 8)
        records.append((offset, attrs & 0xFFFFFF))
    
    # 提取文本
    text_parts = []
    for i in range(1, min(150, len(records))):
        start = records[i][0]
        end = records[i+1][0] if i+1 < len(records) else len(data)
        chunk = data[start:end]
        try:
            text = chunk.decode('utf-8', errors='ignore')
            text_parts.append(text)
        except:
            pass
    
    full_text = '\n'.join(text_parts)
    
    # 去除HTML标签
    clean_text = re.sub(r'<[^>]+>', '', full_text)
    clean_text = re.sub(r'\s+', ' ', clean_text)
    return clean_text.strip()

# 提取刻意练习
print("正在提取《刻意练习》...")
filepath = f"{base_path}/(刻意练习).epub"
text = extract_mobi(filepath)
print(f"提取到 {len(text)} 字符")
with open("ThorBooks/extracted/刻意练习.txt", 'w') as f:
    f.write(text)

# 显示前2000字
print("\n=== 《刻意练习》前2000字 ===")
print(text[:2000])
