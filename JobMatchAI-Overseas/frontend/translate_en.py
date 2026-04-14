#!/usr/bin/env python3
"""英文版翻译脚本 - 读取 index-en.html，替换所有中文为英文"""

import re

# 翻译字典：中文 → 英文
TRANSLATIONS = {
    # Meta
    "AI求职助手 - 智能简历分析、多语言翻译、职位匹配申请追踪": "AI Job Assistant - Smart Resume Analysis, Multilingual Translation, Job Application Tracking",
    "求职,简历,AI,丹麦,瑞典,挪威": "job,resume,AI,Denmark,Sweden,Norway",
    "JobMatchAI - 智能求职助手": "JobMatchAI - Smart Job Assistant",

    # UI通用
    "专业简历精修 + 精准求职信，让每次申请都更有竞争力": "Professional Resume Polish + Tailored Cover Letters — Make Every Application Count",
    "🚀 专业简历精修 + 精准求职信": "🚀 Professional Resume Polish + Tailored Cover Letters",
    "节省时间精力，让每次申请都更有竞争力": "Save time and effort — make every application more competitive",
    "点击或拖拽上传简历": "Click or drag to upload your resume",
    "支持 PDF、DOCX、TXT 格式": "Supports PDF, DOCX, TXT formats",
    "点击或拖拽上传": "Click or drag to upload",

    # Tab标签
    "精修简历": "Polish Resume",
    "意向职位": "Target Position",
    "定制求职申请": "Cover Letter",
    "成为会员": "Go Premium",

    # 步骤
    "上传简历": "Upload Resume",
    "精修简历": "Polish Resume",
    "提供意向职位": "Enter Target Job",
    "生成定制申请": "Generate Application",

    # Hero
    "📄 立即开始：精修简历": "📄 Get Started: Polish Your Resume",

    # 价值主张
    "精准匹配职位": "Smart Job Matching",
    "根据您提供的意向职位，智能精修简历，让每一次申请都更有针对性": "Based on your target position, intelligently polish your resume to make every application more targeted",
    "专业简历精修": "Professional Resume Polish",
    "不过分夸大、不欺骗，在真实基础上优化表达，符合商务求职标准": "No exaggeration, no deception — optimize expressions on a truthful basis to meet professional standards",
    "定制求职申请": "Tailored Applications",
    "基于您的简历和职位信息，AI生成高度定制化的求职申请，省时省力": "AI generates highly tailored applications based on your resume and job info — saving time and effort",

    # 隐私
    "🔒 当前会话已隔离": "🔒 Current Session Isolated",
    "您的简历仅在当前浏览器会话中使用，不会永久存储在我们的服务器上。": "Your resume is only used in the current browser session and will never be permanently stored on our servers.",
    "您的简历和分析结果会自动保存": "Your resume and analysis results are automatically saved",

    # 职位页面
    "💼 提供您的意向职位": "💼 Enter Your Target Position",
    "告诉我们您想申请的职位，我们将据此精修简历并生成定制求职申请": "Tell us the position you're applying for, and we'll polish your resume and generate tailored applications accordingly",
    "职位名称（Job Title）": "Job Title",
    "职位描述（Job Description）— 可粘贴全文或上传文档": "Job Description — paste full text or upload a document",
    "粘贴招聘平台的职位链接": "Paste job posting URL from any job board",
    "从招聘链接抓取职位信息": "Fetch job info from posting URL",
    "粘贴职位描述文本": "Paste Job Description Text",
    "职位名称（可选）": "Job Title (optional)",
    "在此粘贴完整的职位描述文本（包括职责、要求等）...": "Paste the full job description here (including responsibilities, requirements, etc.)...",
    "上传文档": "Upload Document",
    "粘贴文本": "Paste Text",
    "职位链接": "Job URL",
    "上传职位描述文档": "Upload Job Description Document",
    "📋 当前职位信息": "📋 Current Position",
    "职位名称": "Job Title",
    "职位描述...": "Job Description...",
    "已保存的职位": "Saved Jobs",
    "📁 已保存的职位": "📁 Saved Jobs",
    "确认并使用此职位": "Confirm & Use This Position",
    "暂无保存的职位，请先添加": "No saved jobs yet, add one above",

    # 简历精修页面
    "📤 上传并精修简历": "📤 Upload & Polish Resume",
    "💡 支持 LinkedIn、Jobindex、Indeed 等 · Siemens/Workday 等请用「粘贴文本」": "💡 Supports LinkedIn, Jobindex, Indeed, etc. · For Siemens/Workday, use 'Paste Text'",
    "智能简历精修：我们会将您的简历内容与意向职位描述进行匹配，在不过分夸大、不欺骗的前提下，调整表达方式使其更迎合职位要求，并优化格式使其符合商务求职标准。": "Smart Resume Polish: We match your resume content with the job description. Without exaggeration or deception, we adjust expressions to better fit the role and optimize formatting to professional standards.",
    "请尽量在简历中提供完整的工作经历、培训、课程、参与的项目/活动等信息。": "Please provide complete work experience, training, courses, projects/activities etc. in your resume.",
    "⚠️ 隐私提醒：": "⚠️ Privacy Notice:",
    "请勿在简历中放入您的个人敏感信息（如完整身份证号、银行卡号等）。您可在复制或下载简历后，再自行添加联系方式（电话、邮箱、LinkedIn）等信息。": "Do NOT include sensitive personal info (full ID, bank card numbers, etc.) in your resume. You can add contact info (phone, email, LinkedIn) after downloading.",
    "✅ 简历上传成功！": "✅ Resume Uploaded!",
    "👇🏻 点击下方按钮开始分析": "👇🏻 Click the button below to analyze",
    "或粘贴简历内容：": "Or paste resume content:",
    "将简历内容粘贴到这里...": "Paste your resume content here...",
    "✨ 专业分析简历": "✨ Analyze Resume",
    "精修简历": "Polish Resume",
    "开始分析": "Start Analysis",

    # 分析结果
    "📊 简历分析结果": "📊 Resume Analysis",
    "📄 精修后简历": "📄 Polished Resume",
    "✨ 改进建议": "✨ Improvement Suggestions",
    "工作经历": "Work Experience",
    "教育背景": "Education",
    "技能特长": "Skills",
    "语言能力": "Languages",
    "综合评分": "Overall Score",
    "工作年限": "Years of Experience",
    "匹配度": "Match Score",
    "复制全文": "Copy All",
    "下载 Word": "Download Word",
    "复制成功！": "Copied!",
    "全选内容": "Select All",
    "复制成功": "Copied successfully",
    "暂无分析结果": "No analysis results yet",
    "请先上传或粘贴简历并点击分析": "Please upload or paste your resume and click Analyze",
    "正在分析简历，请稍候...": "Analyzing resume, please wait...",

    # 求职信页面
    "✉️ 生成定制求职信": "✉️ Generate Tailored Cover Letter",
    "在生成求职信之前，请先上传简历并分析：": "Please upload and analyze your resume first before generating a cover letter:",
    "上传简历": "Upload Resume",
    "分析简历": "Analyze Resume",
    "请提供以下信息来生成求职信：": "Provide the following info to generate your cover letter:",
    "收件人（如 HR 部门、招聘经理等）": "Recipient (e.g., HR Department, Hiring Manager)",
    "收件人公司名称": "Recipient Company Name",
    "收件人姓名（可选）": "Recipient Name (optional)",
    "语言": "Language",
    "中文": "Chinese",
    "英文": "English",
    "丹麦文": "Danish",
    "德文": "German",
    "瑞典文": "Swedish",
    "职位名称": "Position",
    "主要职责（可选）": "Main Responsibilities (optional)",
    "主要要求（可选）": "Key Requirements (optional)",
    "其他补充（可选）": "Additional Info (optional)",
    "✨ 生成求职信": "✨ Generate Cover Letter",
    "正在生成求职信...": "Generating cover letter...",

    # 求职信结果
    "✉️ 求职信预览": "✉️ Cover Letter Preview",
    "复制求职信": "Copy Cover Letter",
    "下载求职信": "Download Cover Letter",
    "重新生成": "Regenerate",
    "调整语气": "Adjust Tone",
    "质量评分": "Quality Score",
    "尚未生成求职信": "No cover letter generated yet",
    "请先填写信息并点击生成": "Please fill in the info and click Generate above",

    # 质量检测
    "🔍 质量检测": "🔍 Quality Check",
    "检测求职信质量": "Check Cover Letter Quality",
    "正在进行质量检测...": "Running quality check...",

    # 会员
    "⭐ 成为会员": "⭐ Go Premium",
    "解锁全部功能": "Unlock All Features",
    "月度会员": "Monthly",
    "季度会员": "Quarterly",
    "半年度会员": "Semi-Annual",
    "年度会员": "Annual",
    "折": "off",
    "立即订阅": "Subscribe Now",
    "已订阅": "Subscribed",
    "订阅": "Subscribe",
    "免费用户": "Free User",
    "免费用户权限说明": "Free User Features",
    "已订阅高级功能": "Premium Features",
    "✅ 已订阅": "✅ Subscribed",
    "高级功能：": "Premium Features:",
    "无限次简历精修": "Unlimited Resume Polishing",
    "无限次求职信生成": "Unlimited Cover Letters",
    "简历 Word 导出": "Resume Word Export",
    "申请进度追踪": "Application Tracking",
    "无限保存职位": "Unlimited Job Saving",
    "专属客服支持": "Priority Support",
    "基础功能：": "Basic Features:",
    "每天 3 次简历精修": "3 Resume Polishes / Day",
    "每天 1 次求职信生成": "1 Cover Letter / Day",
    "基础简历分析": "Basic Resume Analysis",
    "语言翻译：": "Language Translation:",
    "简历翻译（英/丹/中）": "Resume Translation (EN/DK/CN)",
    "订阅即表示您同意我们的": "By subscribing, you agree to our",
    "服务条款": "Terms of Service",
    "和": "and",
    "隐私政策": "Privacy Policy",
    "当前方案": "Current Plan",
    "订阅成功！": "Subscription successful!",
    "订阅失败，请重试": "Subscription failed, please try again",
    "订阅已取消": "Subscription cancelled",
    "每月": "/month",
    "每季度": "/quarter",
    "每半年": "/6 months",
    "每年": "/year",

    # 语种翻译
    "🌐 简历语种翻译": "🌐 Resume Translation",
    "简历翻译功能说明：": "Resume Translation Info:",
    "将您的简历内容翻译为目标语言，同时适配目标国家的职场表达习惯：": "Translate your resume to the target language, adapted to local workplace conventions:",
    "选择简历语言：": "Source Language:",
    "选择目标语言：": "Target Language:",
    "✨ 翻译简历": "✨ Translate Resume",
    "正在翻译...": "Translating...",

    # 职位搜索
    "🔍 搜索职位": "🔍 Search Jobs",
    "搜索": "Search",
    "关键词": "Keywords",
    "地点": "Location",
    "国家": "Country",
    "搜索结果": "Search Results",
    "加载更多": "Load More",
    "正在搜索...": "Searching...",
    "未找到职位": "No jobs found",
    "职位详情": "Job Details",
    "申请": "Apply",
    "收藏": "Save",
    "已收藏": "Saved",
    "职位描述": "Job Description",
    "职位链接": "Job Link",

    # 通知提示
    "简历已保存": "Resume saved",
    "分析结果已保存": "Analysis saved",
    "职位已保存": "Job saved",
    "求职信已保存": "Cover letter saved",
    "已复制到剪贴板": "Copied to clipboard",
    "请先上传简历": "Please upload a resume first",
    "请先分析简历": "Please analyze your resume first",
    "请填写职位名称": "Please enter the job title",
    "加载中...": "Loading...",

    # 底部
    "关于我们": "About Us",
    "服务条款": "Terms of Service",
    "隐私政策": "Privacy Policy",
    "联系邮箱": "Contact Email",
    "© 2026 JobMatchAI": "© 2026 JobMatchAI",
    "保留所有权利。": "All rights reserved.",

    # 弹窗
    "关闭": "Close",
    "取消": "Cancel",
    "确认": "Confirm",
    "保存": "Save",
    "删除": "Delete",
    "编辑": "Edit",

    # 错误提示
    "上传失败，请重试": "Upload failed, please try again",
    "生成失败，请重试": "Generation failed, please try again",
    "网络错误，请检查网络连接": "Network error, please check your connection",
    "请求超时，请重试": "Request timeout, please try again",
    "服务器错误，请稍后重试": "Server error, please try again later",

    # 注册/登录
    "登录": "Sign In",
    "注册": "Register",
    "邮箱": "Email",
    "密码": "Password",
    "确认密码": "Confirm Password",
    "已有账号？登录": "Already have an account? Sign In",
    "没有账号？注册": "Don't have an account? Register",
    "退出登录": "Sign Out",
    "用户名": "Username",

    # 申请追踪
    "📋 申请追踪": "📋 Application Tracker",
    "我的申请": "My Applications",
    "添加申请": "Add Application",
    "公司名称": "Company Name",
    "申请状态": "Status",
    "投递日期": "Applied Date",
    "跟进备注": "Notes",
    "待处理": "Pending",
    "已投递": "Applied",
    "已回复": "Replied",
    "已面试": "Interviewed",
    "已拒绝": "Rejected",
    "已录用": "Offer Received",
    "已完成": "Completed",

    # AI语种
    "系统检测": "Detected",
    "简体中文": "Simplified Chinese",
    "繁体中文": "Traditional Chinese",
    "英文": "English",
    "丹麦文": "Danish",
    "德文": "German",
    "瑞典文": "Swedish",
    "挪威文": "Norwegian",

    # 其他UI
    "查看详情": "View Details",
    "收起": "Collapse",
    "展开": "Expand",
    "下一步": "Next",
    "上一步": "Previous",
    "跳过": "Skip",
    "完成": "Done",
    "重置": "Reset",
    "刷新": "Refresh",
    "返回": "Back",
    "继续": "Continue",
    "提交": "Submit",
    "发送": "Send",
    "接收": "Receive",

    # 简历分析细节
    "姓名": "Name",
    "邮箱": "Email",
    "电话": "Phone",
    "简历原文": "Original Resume",
    "精修建议": "Polish Suggestions",
    "原文": "Original",
    "建议": "Suggested",
    "工作内容": "Work Content",
    "工作成果": "Achievements",
    "使用技能": "Skills Used",

    # 其他
    "推荐学习": "Recommended Learning",
    "职位缺口": "Job Gaps",
    "提升建议": "Improvement Tips",
    "建议您": "We recommend",
    "可参考": "You may refer to",
}

def translate_file(input_path, output_path):
    with open(input_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content

    # Sort by length descending to avoid partial replacements
    sorted_keys = sorted(TRANSLATIONS.keys(), key=len, reverse=True)

    for cn in sorted_keys:
        en = TRANSLATIONS[cn]
        content = content.replace(cn, en)

    # Also replace common patterns
    replacements = [
        # Remove leftover Chinese-only terms
        ("🌐", "🌐"),
        ("💡", "💡"),
        ("📄", "📄"),
        ("✉️", "✉️"),
        ("🚀", "🚀"),
        ("✅", "✅"),
        ("⚠️", "⚠️"),
        ("🔒", "🔒"),
        ("📊", "📊"),
        ("💼", "💼"),
        ("⭐", "⭐"),
        ("🔍", "🔍"),
        ("👇🏻", "👇🏻"),
        ("📋", "📋"),
        ("📁", "📁"),
    ]

    # Fix lang attribute
    content = content.replace('lang="zh-CN"', 'lang="en"')
    content = content.replace("html lang=\"zh-CN\"", "html lang=\"en\"")

    # Fix title
    content = content.replace(
        '<title>JobMatchAI - Smart Job Assistant</title>',
        '<title>JobMatchAI - Smart Job Assistant</title>'
    )

    changes = sum(1 for cn in TRANSLATIONS if cn in original)
    print(f"Made {changes} translations")

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Saved to {output_path}")

if __name__ == '__main__':
    translate_file(
        '/Users/weili/WorkBuddy/Claw/JobMatchAI-Overseas/frontend/index-en.html',
        '/Users/weili/WorkBuddy/Claw/JobMatchAI-Overseas/frontend/index-en-new.html'
    )
