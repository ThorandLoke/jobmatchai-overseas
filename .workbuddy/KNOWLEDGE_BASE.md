# Claw 跨项目知识库

> 维护规则：解决了一个技术问题后，在此记录。格式见下方模板。
> 适用场景：在 A 项目遇到问题 → 先查此文件 → 是否已在 B 项目解决过？
> 制定日期：2026-04-07

---

## 查询索引

| 技术问题 | 位置 | 验证状态 |
|---------|------|---------|
| PDF 解析（简历/文档） | → #pdf-解析 | ✅ 已验证 |
| Next.js 部署 Vercel | → #nextjs-vercel-部署 | ✅ 已验证 |
| 三语界面切换 | → #多语言界面 | ✅ 已验证 |
| Drag & Drop 上传 | → #拖拽上传 | ✅ 已验证 |
| Python FastAPI 后端 | → #fastapi-后端 | ✅ 已验证 |
| LinkedIn 职位导入 | → #linkedin-职位抓取 | ✅ 已验证 |
| 丹麦语字符处理 | → #国际化-丹麦语 | ✅ 已验证 |

---

## 📄 PDF 解析

**问题**：从用户上传的 PDF 简历中提取文字（用于 AI 分析）

**首次解决**：JobMatchAI-Nordic | 2026-04-01
**被复用**：—

**方案**：
```python
# 三级备用方案（按优先级）
1. PyMuPDF (fitz) — 速度最快，支持中文
2. pdfplumber — 表格提取更好
3. PyPDF2 — 最后的兜底

import fitz  # PyMuPDF
doc = fitz.open(file_path)
text = ""
for page in doc:
    text += page.get_text()
```

**注意事项**：
- PyMuPDF 对中文 PDF 效果最好
- 如果文字是图片扫描件，需要 OCR（tesseract）
- pdfplumber 对表格结构保留更好

---

## 🌐 Next.js Vercel 部署

**问题**：Next.js 项目部署到 Vercel，并配置自定义域名

**首次解决**：BoligBeregner-Danmark | 2026-04-03

**方案**：
1. `vercel` CLI 登录：`vercel login`
2. 项目目录运行：`vercel`（预览部署）
3. 正式部署：`vercel --prod`
4. 域名绑定：Vercel Dashboard → Settings → Domains

**注意事项**：
- Next.js 默认需要 Node.js 环境，Vercel 自动识别
- 如需 SSR，保留默认；如只需静态导出，`next.config.ts` 加 `output: 'export'`
- `.env` 文件不自动上传，需在 Vercel Dashboard 设置环境变量
- GitHub 仓库可绑定 Vercel 实现自动部署（每次 main 分支 push 触发）

---

## 🌐 多语言界面（HTML + JS）

**问题**：单文件 HTML 前端需要中/英/丹三语切换

**首次解决**：JobMatchAI-Nordic | 2026-04-07

**方案**：
```javascript
// 1. 定义翻译对象
const translations = {
  en: { "hero_title": "Find Your Dream Job", ... },
  zh: { "hero_title": "找到理想工作", ... },
  da: { "hero_title": "Find Din Drømmejobbet", ... }
};

// 2. 语言切换函数（支持 data-i18n 和 data-i18n-placeholder）
function switchLanguage(lang) {
  currentLang = lang;
  localStorage.setItem('lang', lang);
  document.querySelectorAll('[data-i18n]').forEach(el => {
    el.textContent = translations[lang][el.dataset.i18n] || el.textContent;
  });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    el.placeholder = translations[lang][el.dataset.i18nPlaceholder] || el.placeholder;
  });
}

// 3. 页面加载时恢复语言
document.addEventListener('DOMContentLoaded', () => {
  switchLanguage(localStorage.getItem('lang') || 'zh');
});
```

**HTML 使用方式**：
```html
<h1 data-i18n="hero_title">找到理想工作</h1>
<input data-i18n-placeholder="job_input_placeholder" placeholder="输入职位...">
```

**注意事项**：
- 所有文本不要写死在 HTML 里，全部用 `data-i18n` 标记
- placeholder 需要单独处理（HTML 原生 placeholder 不支持 `data-i18n`）
- 语言选择保存在 `localStorage`，刷新后保持

---

## 📤 拖拽上传（Drag & Drop）

**问题**：HTML 文件上传区需要支持拖拽，但子元素触发 `dragleave` 导致样式异常

**首次解决**：JobMatchAI | 2026-04-01
**被复用**：JobMatchAI-Nordic

**方案**：使用 `dragCounter` 计数器
```javascript
let dragCounter = 0;

uploadArea.addEventListener('dragenter', (e) => {
  e.preventDefault();
  dragCounter++;
  uploadArea.classList.add('drag-over');
});

uploadArea.addEventListener('dragleave', (e) => {
  e.preventDefault();
  dragCounter--;
  if (dragCounter === 0) {
    uploadArea.classList.remove('drag-over');
  }
});

uploadArea.addEventListener('drop', (e) => {
  e.preventDefault();
  dragCounter = 0;
  uploadArea.classList.remove('drag-over');
  // 处理文件...
});
```

**注意事项**：
- 不用 `dragCounter` 时，直接用 `dragover/dragleave` 会因为子元素导致闪烁
- `dragCounter === 0` 判断放在 `dragleave` 里，确保只在真正离开区域时才移除样式

---

## ⚡ FastAPI 后端

**问题**：Python FastAPI 作为后端，静态文件（HTML/JS/CSS）需要正确挂载

**首次解决**：JobMatchAI-Nordic | 2026-04-01

**方案**：
```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI()

# 挂载静态文件目录（前端资源）
app.mount("/static", StaticFiles(directory="static"), name="static")

# 根路由返回 index.html（避免直接访问 /api 时返回 JSON）
@app.get("/")
async def root():
    return FileResponse("frontend/index.html")

# API 路由
@app.get("/api/jobs")
async def search_jobs(...):
    ...
```

**注意事项**：
- `app.mount()` 用于挂载目录（如 `/static`）
- `FileResponse` 用于返回单个文件（如 `index.html`）
- 根路由 `/` 必须返回 `index.html`，否则刷新页面会 404

---

## 🔗 LinkedIn 职位抓取

**问题**：从 LinkedIn 职位页面 URL 提取职位信息

**首次解决**：JobMatchAI-Nordic | 2026-04-01

**方案**：
1. 用户复制 LinkedIn 职位链接
2. 用 Playwright/Selenium 访问并提取页面内容
3. 正则匹配关键字段（职位名、公司、描述）

**注意事项**：
- LinkedIn 有反爬机制，需要用真实浏览器（Playwright）
- 部分职位信息需要登录才能看到
- 建议提示用户用 LinkedIn PDF 导出功能（Resources → Save to PDF）作为备选

---

## 🇩🇰 国际化 - 丹麦语特殊字符

**问题**：丹麦语特殊字符（ø/æ/å/Ø/Æ/Å）在 PDF、网页、数据库中可能乱码

**首次解决**：BoligBeregner-Danmark | 2026-04-03

**注意事项**：
- 全程使用 UTF-8 编码（HTML `<meta charset="UTF-8">`、Python `encoding='utf-8'`）
- 数据库字段设为 `TEXT` 或 `NVARCHAR`（避免 VARCHAR 长度问题）
- PDF 导出时确认字体支持 Unicode（如 Noto Sans）

---

## 🗄️ SQLite 数据库设计

**问题**：项目中需要本地数据库存储用户数据（简历、职位、申请记录）

**首次解决**：JobMatchAI-Nordic | 2026-04-01

**方案**：
```python
import sqlite3

conn = sqlite3.connect('data/app.db', check_same_thread=False)
conn.execute('''
    CREATE TABLE IF NOT EXISTS submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT,
        resume_text TEXT,
        job_url TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()
```

**注意事项**：
- `check_same_thread=False` 允许多线程访问（FastAPI 并发场景）
- 数据库文件放在 `data/` 目录（已在 .gitignore）
- 定期备份 `.db` 文件

---

## 🔄 部署到 Render（Python 应用）

**问题**：Python FastAPI 应用部署到 Render 平台

**首次解决**：JobMatchAI-Nordic | 2026-04-01

**关键步骤**：
1. `render.yaml` 定义构建命令和运行环境
2. 环境变量在 Render Dashboard 设置（不要写在代码里）
3. Build Command：`pip install -r requirements.txt`
4. Start Command：`uvicorn main:app --host 0.0.0.0 --port $PORT`

**注意事项**：
- Render 免费版休眠（30分钟无活动），访问时首次响应慢
- `$PORT` 是 Render 分配的端口，必须使用，不能写死 8000
- GitHub 仓库绑定 Render 实现自动部署

---

*最后更新：2026-04-07 by Loke*
*格式：每条记录包含首次解决项目、日期、方案代码、注意事项*
