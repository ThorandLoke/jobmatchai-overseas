#!/usr/bin/env python3
"""Translate index-zh.html to index-en.html"""

import re

# Read the Chinese version
with open('/Users/weili/WorkBuddy/Claw/JobMatchAI-Overseas/frontend/index-zh.html', 'r', encoding='utf-8') as f:
    content = f.read()

# Translation dictionary - key: Chinese, value: English
translations = {
    # Comments and meta
    '<!--\nJobMatchAI - 中丹求职助手\n支持：中文 🇨🇳 | 英文 🇬🇧 | 丹麦语 🇩🇰\nCopyright © 2026 JobMatchAI. All rights reserved.\n-->': '<!--\nJobMatchAI - China-Denmark Job Assistant\nSupport: 中文 🇨🇳 | English 🇬🇧 | Danish 🇩🇰\nCopyright © 2026 JobMatchAI. All rights reserved.\n-->',
    'lang="zh-CN"': 'lang="en"',
    'AI求职助手 - 智能简历分析、多语言翻译、职位匹配申请追踪': 'AI Job Assistant - Smart Resume Analysis, Multilingual Translation, Job Matching & Application Tracking',
    '求职,简历,AI,丹麦,瑞典,挪威': 'job,resume,AI,Denmark,Sweden,Norway',
    'JobMatchAI - 智能求职助手': 'JobMatchAI - Smart Job Assistant',
    'href="https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet"': 'href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;700&display=swap" rel="stylesheet"',

    # Header
    '📄 AI智能简历助手': '📄 AI Resume Assistant',
    '🔒 当前会话已隔离 <span style="color: #aaa; font-weight: 400;">（您的数据仅在本地处理，不会发送到服务器）</span>': '🔒 Session isolated <span style="color: #aaa; font-weight: 400;">(Your data is processed locally, not sent to servers)</span>',

    # Hero section
    '🚀 <span class="gradient-text">AI驱动 · 精准匹配 · 专属定制</span>': '🚀 <span class="gradient-text">AI-Powered · Precise Matching · Personalized for You</span>',
    '根据您的目标职位，智能优化简历，生成专属求职信': 'Smartly optimize your resume and generate personalized cover letters based on your target position',

    # Flow steps
    '①</span> 💼 <strong>选职位</strong>': '①</span> 💼 <strong>Choose Job</strong>',
    '②</span> 📄 <strong>精修简历</strong>': '②</span> 📄 <strong>Polish Resume</strong>',
    '③</span> ✉️ <strong>生成求职信</strong>': '③</span> ✉️ <strong>Generate Cover Letter</strong>',
    '④</span> 🎯 <strong>定向补强 · 技能 Gap</strong>': '④</span> 🎯 <strong>Skill Gap & Learning</strong>',
    '💼 从选职位开始 →': '💼 Start by Choosing a Job →',

    # Value props
    '职位导向精准优化': 'Job-Targeted Optimization',
    '根据目标职位要求，智能突出简历中最相关的技能与经验': 'Intelligently highlight the most relevant skills and experience based on job requirements',
    '专属求职信': 'Personalized Cover Letter',
    '基于职位与简历，生成独一无二的定制求职信，让招聘官眼前一亮': 'Generate unique, customized cover letters based on your job and resume to impress recruiters',

    # Tabs
    '💼 1. 意向职位': '💼 1. Target Position',
    '📄 2. 精修简历': '📄 2. Polish Resume',
    '✉️ 3. 专属求职信': '✉️ 3. Cover Letter',
    '📋 简历模版': '📋 Resume Templates',
    '📚 学习资源': '📚 Learning Resources',
    '⭐ 成为会员': '⭐ Become a Member',

    # Search tab header
    '💼 搜索或提供您的意向职位': '💼 Search or Provide Your Target Position',
    '搜索全球职位，或者提供给我们您想申请的职位信息，我们将据此精修简历并生成定制求职申请': 'Search global jobs or provide us with the position you want to apply for. We will polish your resume and generate a customized application based on this information',

    # Collection info
    '📋 我们需要收集以下信息：': '📋 We need to collect the following information:',
    '职位名称（Job Title）': 'Job Title',
    '公司名称（Company Name）': 'Company Name',
    '职位描述（Job Description）— 可粘贴全文或上传文档': 'Job Description — Paste full text or upload document',
    '工作地点、要求等补充信息': 'Work location, requirements, and other supplementary information',

    # Input tabs
    '🔍 搜索职位': '🔍 Search Jobs',
    '🔗 粘贴职位URL': '🔗 Paste Job URL',
    '📄 上传文档': '📄 Upload Document',
    '✏️ 粘贴文本': '✏️ Paste Text',

    # Search input
    '🔍</span>\n                            <span style="color: #6fcf97; font-weight: 600;">搜索职位空缺</span>': '🔍</span>\n                            <span style="color: #6fcf97; font-weight: 600;">Search Job Vacancies</span>',
    '输入职位关键词，从英国、美国、德国等招聘平台搜索真实职位': 'Enter job keywords to search real positions from job platforms in UK, US, Germany, etc.',
    '职位关键词': 'Job Keywords',
    '例如: Python Developer, Data Scientist, ERP Consultant': 'e.g., Python Developer, Data Scientist, ERP Consultant',
    '选择国家/地区': 'Select Country/Region',
    '🌐 所有支持国家': '🌐 All Supported Countries',
    '🇬🇧 英国': '🇬🇧 United Kingdom',
    '🇺🇸 美国': '🇺🇸 United States',
    '🇩🇪 德国': '🇩🇪 Germany',
    '🇦🇺 澳大利亚': '🇦🇺 Australia',
    '🇨🇦 加拿大': '🇨🇦 Canada',
    '🇫🇷 法国': '🇫🇷 France',
    '🇳🇱 荷兰': '🇳🇱 Netherlands',
    '🇧🇪 比利时': '🇧🇪 Belgium',
    '城市（可选）': 'City (Optional)',
    '例如: London, Berlin, New York': 'e.g., London, Berlin, New York',
    '🔍 搜索职位': '🔍 Search Jobs',

    # Search progress
    '🤖 正在搜索职位...': '🤖 Searching jobs...',

    # Search results
    '📋 搜索结果': '📋 Search Results',
    '✕ 关闭': '✕ Close',

    # Link input
    '粘贴招聘平台的职位链接：': 'Paste job posting link from recruitment platform:',
    '例如: https://careers.microsoft.com/job/xxx 或 https://careers.google.com/jobs/xxx': 'e.g., https://careers.microsoft.com/job/xxx or https://careers.google.com/jobs/xxx',
    '💡 LinkedIn、Jobindex、Indeed等职位信息请用「粘贴文本」': '💡 For LinkedIn, Jobindex, Indeed etc., please use "Paste Text"',
    '🔍 尝试抓取': '🔍 Try to Fetch',

    # Upload
    '上传职位描述文档：': 'Upload job description document:',
    '支持 PDF、DOCX、TXT 格式': 'Supports PDF, DOCX, TXT formats',

    # Paste text
    '✂️</span>\n                            <span style="color: #00d4ff; font-weight: 600;">粘贴职位描述文本</span>': '✂️</span>\n                            <span style="color: #00d4ff; font-weight: 600;">Paste Job Description Text</span>',
    '直接从招聘页面复制（Ctrl+A → Ctrl+C）粘贴即可': 'Copy directly from job posting page (Ctrl+A → Ctrl+C) and paste here',
    '职位名称（可选）': 'Job Title (Optional)',
    '公司名称（可选）': 'Company Name (Optional)',
    '在此粘贴完整的职位描述文本（包括职责、要求等）...': 'Paste complete job description here (including responsibilities, requirements, etc.)...',
    '✅ 确认并使用此职位': '✅ Confirm and Use This Position',

    # Job link card
    '📋 当前职位信息': '📋 Current Position Information',
    '职位名称': 'Job Title',
    '公司名称': 'Company Name',
    '职位描述...': 'Job Description...',

    # Saved jobs
    '📁 已保存的职位': '📁 Saved Positions',
    '📌 温馨提示：所有建议和模板仅供参考学习，鼓励用户撰写自己的申请材料。': '📌 Note: All suggestions and templates are for reference only. We encourage users to write their own application materials.',

    # Resume tab
    '📤 上传并精修简历': '📤 Upload & Polish Resume',
    '💡 请尽量在简历中提供完整的工作经历、培训、课程、参与的项目/活动等信息。': '💡 Please provide complete work experience, training, courses, projects/activities, etc. in your resume.',
    '⚠️': '⚠️',
    '<strong style="color: #ff6b6b;">请勿在简历中放入您的个人敏感信息</strong>（如完整身份证号、银行卡号等）。\n                            您可在 <strong style="color: #fff;">复制或下载简历后</strong>，再自行添加联系方式（电话、邮箱、LinkedIn）等信息，这样可以更好地保护您的隐私安全。': '<strong style="color: #ff6b6b;">Do not include personal sensitive information</strong> (such as full ID numbers, bank card numbers, etc.).\n                            You can add contact information (phone, email, LinkedIn) <strong style="color: #fff;">after copying or downloading your resume</strong> to better protect your privacy.',

    # Upload area
    '📎</div>\n                    <p style="font-size: 1.3rem; font-weight: 600; margin-bottom: 8px;">点击或拖拽上传简历</p>': '📎</div>\n                    <p style="font-size: 1.3rem; font-weight: 600; margin-bottom: 8px;">Click or drag to upload resume</p>',
    '支持 PDF、DOCX、TXT 格式': 'Supports PDF, DOCX, TXT formats',

    # Upload progress
    '上传中...': 'Uploading...',
    '📄 正在解析简历内容，请稍候': '📄 Parsing resume content, please wait',

    # Upload success
    '✅ 简历上传成功！': '✅ Resume uploaded successfully!',
    '👇🏻 点击下方按钮开始分析': '👇🏻 Click the button below to start analysis',

    # Privacy notice
    '<strong style="color: #fff;">隐私保护：</strong>您的简历仅在当前浏览器会话中使用，不会永久存储在我们的服务器上。\n                            如需保存，请下载到本地。': '<strong style="color: #fff;">Privacy Protection:</strong> Your resume is only used in the current browser session and will not be permanently stored on our servers.\n                            If you need to save it, please download to your local device.',

    # Resume text input
    '或粘贴简历内容：': 'Or paste resume content:',
    '将简历内容粘贴到这里...': 'Paste resume content here...',
    '✨ 专业分析简历': '✨ Analyze Resume',

    # Analyze progress
    '🤖 AI正在分析简历...': '🤖 AI is analyzing your resume...',
    '预计需要 10-20 秒，请稍候': 'Estimated 10-20 seconds, please wait',

    # Analysis result
    '📊 简历分析结果 <span id="detectedLang" class="lang-badge"></span>': '📊 Resume Analysis Results <span id="detectedLang" class="lang-badge"></span>',

    # Polish section
    '✨ 简历精修 <span id="polishProgress" style="font-size: 0.9rem; color: #ccc;"></span>': '✨ Resume Polishing <span id="polishProgress" style="font-size: 0.9rem; color: #ccc;"></span>',
    '高优先级': 'High Priority',
    '❌ 原版': '❌ Original',
    '✅ 建议版': '✅ Suggested',
    '💡 为什么要这样改：': '💡 Why make this change:',

    # Polish buttons
    '⏭️ 忽略这条': '⏭️ Skip This',
    '✅ 接受这条': '✅ Accept This',

    # Polish loading
    '🤖 AI正在分析简历，生成精修建议...': '🤖 AI is analyzing your resume and generating suggestions...',
    '预计需要 20-40 秒，请稍候': 'Estimated 20-40 seconds, please wait',

    # Polish complete
    '精修完成！': 'Polishing complete!',
    '已接受 <span id="acceptedCount">0</span> 条修改': 'Accepted <span id="acceptedCount">0</span> changes',

    # Polished resume
    '📝 精修后的简历（可编辑）：': '📝 Polished Resume (Editable):',
    '📋 复制': '📋 Copy',
    '💾 下载 ▾': '💾 Download ▾',
    '📘 Word': '📘 Word',
    '📄 PDF': '📄 PDF',
    '📝 文本': '📝 Text',
    '🔄 重新精修': '🔄 Polish Again',

    # Preview
    '📄 简历预览': '📄 Resume Preview',
    '📝 编辑简历内容<br>\n                                            <span style="font-size: 10px; color: #bbb;">实时预览效果</span>': '📝 Edit resume content<br>\n                                            <span style="font-size: 10px; color: #bbb;">Live preview</span>',
    '重置': 'Reset',

    # Translation section
    '🌐 一键转换简历语种': '🌐 One-Click Resume Translation',
    '🤖 AI正在翻译中...': '🤖 AI is translating...',
    '预计需要 15-30 秒，请稍候': 'Estimated 15-30 seconds, please wait',
    '🔄 开始转换': '🔄 Start Translation',
    '💡 不仅翻译，还根据当地职场文化调整表达方式': '💡 Not just translation, but also adapts expressions to local workplace culture',
    '📄 转换预览：': '📄 Translation Preview:',
    '📋 复制': '📋 Copy',
    '💡 PDF如有问题请下载其他格式': '💡 If PDF has issues, try other formats',
    '📄 Word文档 (.docx)': '📄 Word Document (.docx)',
    '📕 PDF文档 (.pdf)': '📕 PDF Document (.pdf)',
    '📝 文本文件 (.txt)': '📝 Text File (.txt)',

    # Templates tab
    '📋 简历模版库': '📋 Resume Template Library',
    '选择专业设计的简历模版，让您的求职申请更具竞争力。点击模版查看大图预览。': 'Choose professionally designed resume templates to make your job applications more competitive. Click template to see preview.',
    '经典专业型': 'Classic Professional',
    '经典专业型 · 适合金融/咨询行业': 'Classic Professional · Suitable for Finance/Consulting',
    '🎯 点击预览': '🎯 Click to Preview',
    '现代简约型': 'Modern Minimalist',
    '现代简约型 · 适合IT/科技行业': 'Modern Minimalist · Suitable for IT/Tech',
    '创意活力型': 'Creative Energetic',
    '创意活力型 · 适合创意/营销行业': 'Creative Energetic · Suitable for Creative/Marketing',
    '🌐 更多模版资源': '🌐 More Template Resources',
    '我们还推荐以下专业简历模版平台，点击图标前往选择：': 'We also recommend the following professional resume template platforms, click to visit:',

    # Learning tab
    '📚 学习资源库': '📚 Learning Resources',
    '根据您的简历和目标职位，为您推荐最相关的学习资源': 'Recommended learning resources based on your resume and target position',
    '搜索或选择技能关键词：': 'Search or select skill keywords:',
    '🔍 搜索学习资源...': '🔍 Search learning resources...',
    '🎯 为我推荐': '🎯 Recommend for Me',
    '🇨🇳 国内资源': '🇨🇳 Chinese Resources (Bilibili)',
    '🌍 国际资源': '🌍 International Resources',
    '💡 提示：': '💡 Tip:',
    '切换 Tab 查看不同来源的资源': 'Switch tabs to view resources from different sources',
    '🎯 核心技能': '🎯 Core Skills',
    '📈 进阶技能': '📈 Advanced Skills',
    '🌐 其他技能': '🌐 Other Skills',

    # Cover letter tab
    '✉️ 生成专属求职信': '✉️ Generate Personalized Cover Letter',
    '基于您上传的简历和目标职位，生成独一无二的定制求职信': 'Generate unique, personalized cover letters based on your uploaded resume and target position',
    '📄 上传您的简历（如已完成可跳过）': '📄 Upload Your Resume (Skip if already done)',
    '📋 输入目标职位信息（如已输入可跳过）': '📋 Enter Target Position (Skip if already entered)',
    '✨ 生成求职信': '✨ Generate Cover Letter',

    # Cover letter output
    '📝 求职信预览': '📝 Cover Letter Preview',
    '🔄 重新生成': '🔄 Regenerate',
    '📋 一键复制': '📋 Copy All',

    # Payment tab
    '⭐ 解锁全部高级功能': '⭐ Unlock All Premium Features',
    '终身免费升级，持续迭代': 'Free lifetime upgrades, continuous improvements',
    '✨ 全部功能': '✨ All Features',
    '📄 无限简历分析': '📄 Unlimited Resume Analysis',
    '✉️ 无限求职信生成': '✉️ Unlimited Cover Letters',
    '🌍 多语言支持': '🌍 Multilingual Support',
    '📊 高级分析报告': '📊 Advanced Analytics',
    '💼 专属客服支持': '💼 Priority Support',
    '💳 选择方案': '💳 Choose a Plan',
    '月付': 'Monthly',
    '年付 <span style="color: #6bcf7f;">(省40%)</span>': 'Yearly <span style="color: #6bcf7f;">(Save 40%)</span>',
    '立即开通': 'Subscribe Now',
    '已有账号? 登录': 'Already have an account? Login',

    # Footer
    '📧 联系我们：': '📧 Contact Us:',
    '使用即表示同意我们的': 'By using, you agree to our',
    '服务条款': 'Terms of Service',
    '和': 'and',
    '隐私政策': 'Privacy Policy',

    # Modal
    '💳 开通会员': '💳 Subscribe to Premium',
    '解锁全部高级功能，让求职更加高效': 'Unlock all premium features for more efficient job hunting',
    '💳 选择支付方式': '💳 Choose Payment Method',
    '💬 交流群': '💬 Community',
    '📧 邮箱': '📧 Email',

    # Beta/Early Bird
    '🧪 抢先体验': '🧪 Early Access',
    '测试版功能，可能存在不稳定': 'Beta features, may be unstable',
    '关闭提示': 'Close',

    # Error messages (JS)
    '请先上传简历或粘贴简历内容': 'Please upload a resume or paste resume content first',
    '请先提供职位信息': 'Please provide position information first',
    '简历上传中，请稍候...': 'Resume uploading, please wait...',
    '正在分析简历...': 'Analyzing resume...',
    '正在生成精修建议...': 'Generating polishing suggestions...',
    '正在翻译简历...': 'Translating resume...',
    '正在生成求职信...': 'Generating cover letter...',
    '正在搜索职位...': 'Searching jobs...',
    '正在抓取职位信息...': 'Fetching job information...',
    '职位抓取成功！': 'Job fetched successfully!',
    '职位抓取失败：': 'Job fetch failed:',
    '加载更多...': 'Load more...',
    '正在加载...': 'Loading...',
    '简历已复制到剪贴板': 'Resume copied to clipboard',
    '翻译简历已复制到剪贴板': 'Translated resume copied to clipboard',
    '求职信已复制到剪贴板': 'Cover letter copied to clipboard',
    '⏸️ 暂停': '⏸️ Pause',
    '▶️ 继续': '▶️ Resume',
    '所有建议已处理完成！': 'All suggestions processed!',
    '简历精修完成！': 'Resume polishing complete!',
    '精修建议加载中...': 'Loading polishing suggestions...',
    '正在加载职位详情...': 'Loading position details...',
    '职位信息已保存': 'Position saved',
    '职位信息加载中...': 'Loading position info...',
    '简历解析中...': 'Parsing resume...',
    '简历分析完成！': 'Resume analysis complete!',
    '简历分析失败：': 'Resume analysis failed:',
    '求职信生成失败：': 'Cover letter generation failed:',
    '没有找到匹配的技能': 'No matching skills found',
    '加载学习资源...': 'Loading learning resources...',
    '暂无相关学习资源': 'No relevant learning resources available',
    '正在加载职位列表...': 'Loading job list...',
    '没有找到相关职位': 'No relevant positions found',
    '展开': 'Expand',
    '收起': 'Collapse',
    '使用此职位': 'Use This Position',
    '删除': 'Delete',
    '保存': 'Save',
    '取消': 'Cancel',
    '确认': 'Confirm',
    '关闭': 'Close',
}

# Apply translations
for cn, en in translations.items():
    content = content.replace(cn, en)

# Additional regex replacements for dynamic content
content = re.sub(r'选择 (\w+) 行业', r'Select \\1 Industry', content)
content = re.sub(r'找到 (\d+) 条结果', r'Found \\1 results', content)
content = re.sub(r'正在搜索 (\w+)...', r'Searching \\1...', content)
content = re.sub(r'已保存 (\d+) 个职位', r'Saved \\1 positions', content)

# Write English version
with open('/Users/weili/WorkBuddy/Claw/JobMatchAI-Overseas/frontend/index-en.html', 'w', encoding='utf-8') as f:
    f.write(content)

print("Translation complete! Created index-en.html")
