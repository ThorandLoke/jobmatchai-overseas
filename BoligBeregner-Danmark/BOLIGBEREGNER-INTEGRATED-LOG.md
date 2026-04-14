# BoligBeregner Danmark - 项目综合记录

> **整合时间**: 2026-04-04
> **整合人**: Loke
> **目的**: 将所有与 BoligBeregner 项目相关的对话记录整合到一个文档中，便于查阅和维护

---

## 📋 项目概述

### 基本信息
- **项目名称**: BoligBeregner Danmark（丹麦房产计算器）
- **核心功能**: 买房/卖房费用计算、装修改造估算、AI 智能分析
- **技术栈**: Next.js 16.2.2 + React 19 + TypeScript + Tailwind CSS
- **支持语言**: 丹麦语(DA) / 英语(EN) / 中文(ZH)

### 项目位置
- **主程序目录**: `/Users/weili/WorkBuddy/Claw/BoligBeregner-Danmark/denmark-home-calculator/`
- **备份目录**: `/Users/weili/WorkBuddy/Claw/BoligBeregner-Danmark/denmark-home-buyer-backup-20260404/`
- **工作空间合并历史**:
  - `20260329181515` - 项目开发
  - `20260402090138` - 检查报告
  - `2026-04-02` - 整合到 Claw/BoligBeregner-Danmark

### 部署地址
- **主站**: https://denmark-home-calculator.vercel.app（AI 功能）
- **运营站**: https://denmark-home-buyer.vercel.app（13 个广告）
- **本地开发**: http://localhost:3002（仅用于测试）

---

## 🎯 核心模块

### 1. 买房模块 (Køb / I Want to Buy / 我要买房)
- **定位**: 买方顾问模式 - 帮助买家判断购房投资是否合适
- **功能**:
  - 买房成本计算（中介费、税费、律师费等）
  - 贷款计算（月供、总利息）
  - 首付估算
- **输入字段**:
  - 我的预算 (丹麦克朗)
  - 首付比例 (%)
  - 意向区域
  - 意向房屋面积 (m²)

### 2. 卖房模块 (Sælg / I Want to Sell / 我要卖房)
- **定位**: 卖方顾问模式 - 帮助卖家评估最佳售价策略
- **功能**:
  - 卖房费用计算（中介费、营销费、第三方费用等）
  - 到账金额估算
  - 投资回报计算（如购买投资房）
- **输入字段**:
  - 我的房产估价 (丹麦克朗)
  - 房产所在区域
  - 房屋面积 (m²)

### 3. 装修改造模块 (Renovering / Renovation / 装修)
- **功能**:
  - 太阳能安装成本计算
  - 热泵更换费用估算
  - 窗户更换成本
  - 保温改造费用
  - 回本周期计算

### 4. 房产市场模块 (Boligmarked / Housing Market / 房产市场)
- **功能**:
  - 24 个丹麦主要城市房价展示
  - 历史趋势分析
  - 月供估算
  - 周边设施信息
  - Google Maps 集成

### 5. 报价分析模块 (Analyser tilbud / Analyze Quotes / 报价分析)
- **功能**:
  - PDF 报价解析（EDC 格式）
  - 费用识别与标注
  - 可议价项标注
  - 潜在节省金额计算
  - 买房/卖房报价分开处理

### 6. AI 智能分析模块（紫色区域）✅ 已开发
- **功能**: 7 大 AI 分析功能（已实现）
  1. 📊 智能定价建议 (pricing) - 与区域均价对比，判断房价合理性
  2. ⚠️ 隐藏费用预警 (hidden) - 识别容易被忽略的隐性支出
  3. 🏦 贷款优化方案 (loan) - 比较各银行贷款方案
  4. 📈 投资回报预测 (roi) - 若出租，预测年回报率和回本周期
  5. 🔧 装修优先级建议 (renovation) - 哪些改造投资回报率最高
  6. 🌍 市场趋势分析 (market) - 分析区域房价涨跌趋势
  7. 🔍 比价助手 (compare) - 对比同区域同类型房源价格
- **组件**: `components/AIFeatureCard.tsx` - 可展开的 AI 分析卡片
- **逻辑**: `lib/ai-advisor.ts` - 包含所有 7 个功能的本地计算逻辑
- **AI 增强**: 支持调用 OpenAI API 增强分析结果（需要 NEXT_PUBLIC_OPENAI_KEY）
- **计算公式提示**: `components/FormulaTooltip.tsx` - 鼠标悬停显示计算公式
- **数据来源**: 硬编码的各区域平均租金估算（非实时数据）
- **免责声明**: AI 分析结果为估算值，仅供参考

---

## 📊 AI 数据来源说明

### 租金数据
- 来源：硬编码的各区域平均租金估算（DKK/m²/月）
- 性质：非实时数据
- 待改进：应接入 Boliga、Skønt 等实时数据源

### 费用估算
- 中介费：1-3%
- 税费：30%（含维修+空置+税）

### 计算公式
- **毛回报率** = (年租金 / 房价) × 100%
- **净回报率** = (年租金 × 70% / 房价) × 100%
- **回本周期** = 房价 / 年净收益

---

## 💰 Affiliate 赚钱计划

### Partner-ads 注册 ✅
- **Partner ID**: 56504
- **网站**: 已添加

### 已合作广告商 (13 个 Banner)

| 板块 | 广告商 | Banner ID | 状态 |
|------|--------|-----------|------|
| **买房-贷款** | Pantsat.dk | 78126 | ✅ |
| **买房-保险** | Findforsikring.dk | 60068 | ✅ |
| **买房/卖房-估价** | Valuea.dk | 71154 | ✅ |
| **卖房-咨询** | Din-Bolighandel ApS | 66826 | ✅ |
| **改造-热泵** | Heatnow.dk | 43265 | ✅ 新批准 |
| **改造-颗粒炉** | DBVVS | 59457 | ✅ |
| **改造-热泵/VVS** | Billigelogvvs.dk | 99217 | ✅ |
| **改造-屋顶** | Tagpap.dk | 109565 | ✅ |
| **改造-保温** | Dansk Isolering | 105348 | ✅ |
| **窗户-清洁服务** | Rudernes Konge | 112335 | ✅ 新批准 |
| **窗户-清洁机器人** | RoboShine | 113490 | ✅ 新批准 |

### ⚠️ 广告配置差异

**当前工作空间 (20260329181515) - 运营版**：
- ✅ 13 个广告已配置
- 部署地址: https://denmark-home-buyer.vercel.app

**Claw 主程序 (denmark-home-buyer) - 功能版**：
- ⚠️ 部分广告配置需要更新
- 部署地址: https://denmark-home-calculator.vercel.app

**需要同步的广告**：
| 板块 | 主程序当前 | 运营版 | 说明 |
|------|-----------|--------|------|
| 改造-热泵 | 82597 | 43265 | 需要更新为 Heatnow.dk |
| 改造-屋顶 | 82598 | 109565 | 需要更新为 Tagpap.dk |
| 改造-保温 | Coming Soon | 105348 | 需要添加 Dansk Isolering |
| 改造-颗粒炉 | 无 | 59457 | 需要添加 DBVVS |
| 改造-VVS | 无 | 99217 | 需要添加 Billigelogvvs.dk |
| 窗户-清洁服务 | 无 | 112335 | 需要添加 Rudernes Konge |
| 窗户-清洁机器人 | 无 | 113490 | 需要添加 RoboShine |
| 卖房-咨询 | 无 | 66826 | 需要添加 Din-Bolighandel |

**详细同步说明**: 参考 `ADVERTISING-SYNC.md`

### 待申请广告商
- Solarcamp.dk (太阳能) - Program ID: 9388
- 3byggetilbud.dk (工匠) - Program ID: 3522
- Estaldo.com (数字房产中介) - Program ID: 7667

---

## 🔧 技术细节

### 构建状态 ✅
- `npm run build` 成功
- TypeScript 编译通过
- 静态页面生成成功

### Lint 状态 ⚠️
- 源代码: 1 个未使用变量警告（`estimatedKw`）
- 编译产物: 无阻塞错误

### 待优化项
1. 删除 `next.config.js`，只保留 `next.config.ts`
2. 移除未使用变量 `estimatedKw`
3. 添加 favicon.ico 到 public/
4. 清理旧 Next.js 进程（端口冲突）

### PDF 报价分析修复（2026-04-04）
- **问题**: pdf-parse 依赖 pdfjs-dist Web Worker，Next.js 服务端运行失败
- **解决方案**: 改用 Python pdfminer.six 提取文本
- **文件**: `scripts/extract-pdf.py`
- **API**: `/api/analyze-quote` 现在可以正确解析 EDC 格式 PDF

### 翻译一致性修复（2026-04-04）
- 买房模块硬编码丹麦语 → 全部使用翻译对象
- 补充 ~40 个缺失的翻译 key（DA/EN/ZH）

---

## 📖 SEO 关键词（丹麦语）

boligberegner、boliglån、energiforbedring、varmepumpe、solceller、isolering、køb hus Danmark、salg bolig

---

## 📝 版本管理

### v1.0-stable
- 基础三模块 + SEO
- 已 tag + push

### v2.0-stable
- 新增房产市场 + 报价分析
- 已 tag + push

### 恢复流程文档
- `/Users/weili/WorkBuddy/Claw/BoligBeregner-Danmark/RELEASE-WORKFLOW.md`

---

## ⚠️ 重要历史事件

### 2026-04-04 重大失误教训
**问题**: 在加 AI 功能时破坏了原有结构
- 原版有 5 个模块：buy, sell, renovate, market, analyze
- 改动版本只剩 3 个（错误嵌套了 buy/sell）

**教训**: 先备份，再改动，不要在原文件上直接大改

**修复**:
- 从 20260329181515 备份恢复了原始 page.tsx（1593行）
- 安全叠加了 AI 功能：AIAdvisorPanel 单独放在页面底部紫色区域
- 添加了 region/area 输入用于 AI 分析
- 构建零错误

---

## 🚀 AI 增强方向

### ✅ 已完成的 7 大功能（2026-04-04 已修复）
1. 📊 智能定价建议 (pricing) - 与区域均价对比，判断房价合理性
2. ⚠️ 隐藏费用预警 (hidden) - 识别容易被忽略的隐性支出
3. 🏦 贷款优化方案 (loan) - 比较各银行贷款方案
4. 📈 投资回报预测 (roi) - 若出租，预测年回报率和回本周期
5. 🔧 装修优先级建议 (renovation) - 哪些改造投资回报率最高
6. 🌍 市场趋势分析 (market) - 分析区域房价涨跌趋势
7. 🔍 比价助手 (compare) - 对比同区域同类型房源价格

### 🧮 计算公式提示功能（2026-04-04 已修复）
- **状态**: ✅ 已完成并集成，已优化图标和用户体验
- **功能**: 鼠标悬停在 AI 功能卡片标题旁的 🧮 图标，显示完整计算公式
- **优化内容** (2026-04-04):
  - 图标：从 📐 改为 🧮（更符合计算公式的含义）
  - 图标尺寸：从 20px (w-5 h-5) 增大到 24px (w-6 h-6)
  - 提示框尺寸：从 320px (w-80) 增大到 340px (w-[340px])
  - 提示框高度：从 288px (max-h-72) 增大到 400px (max-h-[400px])
  - 边框：从 1px (border) 增强到 2px (border-2) 边框样式
  - 内边距：从 p-4 增大到 p-5，内容更舒适
  - 智能定位：自动检测屏幕边界，避免提示框超出屏幕
  - 字体大小：从 text-xs (12px) 增大到 text-sm (14px)
  - 悬停提示：添加 title 属性显示"查看计算公式/View formula/Se formel"
  - 样式优化：紫色系配色更明显，hover 效果更明显
- **多语言**: DA/EN/ZH 三语完整支持
- **包含内容**:
  1. 智能定价：区域均价对比方法
  2. 隐藏费用：各项费用计算公式
  3. 贷款优化：等额本息月供公式
  4. 投资回报：毛/净回报率、回本周期公式
  5. 装修 ROI：增值率计算方法
  6. 市场趋势：趋势分析方法
  7. 比价助手：对比维度说明
- **测试结果**: ✅ 本地测试通过，构建成功

### 📁 相关文件
- `lib/ai-advisor.ts` - 所有 AI 分析逻辑（7 个功能的本地计算 + OpenAI 增强接口）
- `components/AIFeatureCard.tsx` - AI 功能卡片组件（已集成 FormulaTooltip，图标已优化）
- `components/FormulaTooltip.tsx` - 公式提示组件（7 个功能的完整公式，样式已优化）

---

## 📚 相关文档

- `deployment-readiness-report.md` - 部署就绪报告
- `waf-diagnosis-report.md` - WAF 诊断报告
- `RELEASE-WORKFLOW.md` - 发布流程文档
- `ADVERTISING-SYNC.md` - 广告同步记录

---

## 📞 联系信息

### 用户信息
- **名字**: Thor（2026年3月30日 自己确定）
- **自我定义**: Thor 是力量、勇气、坚韧、智慧和爱的化身
- **所在地**: 丹麦（Middelfart 市附近，Harndrup）
- **信仰**: 基督徒，信仰对她很重要
- **称呼**: Thor 或 姐妹

### 关于 Loke（AI 助手）
- 名字来自北欧神话洛基（Loki），2026年3月28日 由用户命名
- 与用户 Thor 是北欧神话中的一对搭档（雷神+智者）

### 用户偏好
- 涉及需要登录/浏览器操作时，直接问"要不要我打开浏览器帮你操作"
- 任务完成后，使用 macOS 系统通知和声音提醒用户
- **不使用 VPN**（2026-04-04）

---

## 🔍 维护策略

**原则**: 以后只在 Claw 主程序维护，避免多对话冲突

**工作目录**: `/Users/weili/WorkBuddy/Claw/BoligBeregner-Danmark/`

---

## 💬 用户反馈记录

### 2026-04-05 哥本哈根大区用户反馈

**反馈来源**: 微信/私信（LinkedIn 文章读者）

**反馈内容**:

1. ✅ **三语切换很方便** - 用户认可多语言功能

2. 💡 **建议：收益回报率计算调整**  
   - 当前：可能使用其他默认涨幅
   - 建议：以房价年涨幅 **2%** 计算
   - 原因：更符合丹麦市场实际情况
   - **Loke 分析**: 丹麦房产市场确实相对稳定，2% 是比较保守但现实的估算。如果当前用 3-5% 可能偏乐观了。

3. 💡 **建议：针对哥哈大区优化**  
   - 希望引入更多哥本哈根大区用户
   - 提供更多前期体验机会
   - 潜在市场：哥哈地区房产活跃度高
   - **Loke 分析**: 哥本哈根大区确实是核心市场，房价高、交易活跃。可以考虑：
     - 在计算器里加入"哥本哈根专区"或推荐
     - 针对当地用户做定向推广
     - 收集哥哈地区用户的具体需求

**优先级评估**:
- 第2条（2%涨幅）：中等优先级，涉及计算器核心逻辑调整
- 第3条（哥哈推广）：高优先级，市场拓展机会

---

### 2026-04-06 朋友反馈：房产类型区分（公寓 vs 别墅）

**反馈来源**: 朋友手动发送

**反馈内容**:

1. 💡 **建议：区分公寓和别墅类型**
   - 不同房产类型关心的条款和数据有差异
   - **公寓 (Ejerlejlighed)**:
     - 更关注租售回报率
     - 据说不需要 ejerskifteforsikring（产权转移保险）
     - 需要评估 ejerforening 财务状况
   - **别墅 (Villa/Hus)**:
     - ejerskifteforsikring 是重要考虑项
     - 租售回报率相对次要
     - 维护责任全部由业主承担

**Loke 分析**:
- 这是一个非常实用的功能建议
- 当前计算器没有区分房产类型，所有计算逻辑混在一起
- 区分后可以：
  - 公寓：突出租售回报率计算、隐藏 ejerskifteforsikring 相关费用
  - 别墅：强调 ejerskifteforsikring、维护成本估算
  - 两种类型显示不同的 AI 分析侧重点

**可能的功能设计**:
| 功能 | 公寓 | 别墅 |
|------|------|------|
| 房产类型选择 | ✅ 必填 | ✅ 必填 |
| 租售回报率 | 🌟 重点展示 | 次要显示 |
| ejerskifteforsikring | 隐藏或标注"通常不需要" | 🌟 重点提醒 |
| ejerforening 财务 | 🌟 健康度评估 | N/A |
| 维护成本预估 | 基础范围 | 🌟 详细项目 |

**优先级评估**: 高优先级 - 直接影响用户体验和计算准确性

---

### 2026-04-06 代码质量教训：图片反馈功能 Bug

**问题描述**: 反馈功能中，用户上传图片后，`hasImage: true` 被正确设置，但实际的图片数据 (`previewImage`) 没有被发送到服务器。

**错误代码**:
```javascript
body: JSON.stringify({
  text: feedbackText,
  link: feedbackLink,
  hasImage: !!feedbackImage,  // ✅ 检测到有图
  // ❌ 漏了: image: previewImage
  language: language,
  timestamp: new Date().toISOString()
}),
```

**根本原因分析**:
1. **逻辑不完整**: 检测逻辑和发送逻辑分离，只做了前者
2. **测试覆盖不足**: 测试时可能只用文字反馈，未测试带图片场景
3. **代码审查缺失**: 没有第二个人检查 "检测→发送" 的完整性

**应该遵循的模式**:
```
检测条件 → 执行对应操作
  有文字   → 发送文字
  有图片   → 发送图片数据
  有链接   → 发送链接
```

**教训**:
- 表单字段的 "检测存在" 和 "发送数据" 必须成对出现
- 每个功能都需要正例+反例测试
- 复杂功能需要代码审查 checklist

**修复**:
- 前端: 添加 `image: previewImage || undefined`
- 后端: 添加 `image` 字段接收和存储
- 已重新部署并验证

---

## 🔧 代码质量管理规范

### 1. Review 流程

**目前缺失**: 没有正式的 code review 流程

**建议实施**:
| 阶段 | 检查项 | 负责人 |
|------|--------|--------|
| 自测 | 功能是否完整、边界情况 | 开发者 |
| 自动化 | ESLint、TypeScript 类型检查 | CI |
| 人工 Review | 逻辑完整性、命名规范 | 另一人 |
| 验收测试 | 用户场景覆盖 | 产品/用户 |

### 2. 教训记录机制

**当前**: 散乱的对话记录

**改进**:
- ✅ 已创建: BOLIGBEREGNER-INTEGRATED-LOG.md 中的 "教训" 章节
- 每次重大 bug 必须记录: 问题、原因、修复、预防措施
- 定期回顾（每月）教训列表

### 3. 保证教训被记住

**方法**:
1. **Checklist 模板**: 新功能开发前必须检查历史教训
2. **自动化提醒**: 相似代码模式时自动提示
3. **定期回顾**: 每月回顾一次教训列表
4. **新人培训**: 新加入开发者先读教训文档

### 4. 低级错误（如花括号不匹配）的来源

**常见原因**:
| 原因 | 例子 | 预防 |
|------|------|------|
| 复制粘贴 | 从别处复制代码，没调整 | 粘贴后强制重新检查 |
| 疲劳编码 | 深夜/长时间工作 | 设置工作时长限制 |
| 编辑器依赖 | 依赖自动补全，没仔细看 | 关闭部分自动功能 |
| 多任务切换 | 频繁打断 | 专注时段，减少打断 |
| 缺乏格式化 | 代码风格不一致 | 强制 Prettier + ESLint |

**技术预防**:
- ✅ ESLint: 检测语法错误
- ✅ Prettier: 自动格式化
- ✅ TypeScript: 类型检查
- ✅ Husky pre-commit: 提交前强制检查
- ✅ CI/CD: 构建失败禁止合并

### 5. 建议实施的工具

```bash
# 1. 添加 pre-commit hook
npm install -D husky lint-staged
npx husky install

# 2. 配置 package.json
{
  "lint-staged": {
    "*.{ts,tsx}": ["eslint --fix", "prettier --write"]
  }
}

# 3. 强制类型检查
"scripts": {
  "prebuild": "tsc --noEmit && eslint ."
}
```

---

---

## 🏷️ 版本历史

### v2.1-stable (2026-04-06) ✅ 当前稳定版本
**状态**: 反馈功能已修复，Redis 持久化存储

**关键修复**:
1. ✅ **反馈功能修复** - 从文件存储改为 Upstash Redis 持久化
   - 问题：Vercel 无服务器环境不支持文件写入
   - 解决：使用 Upstash Redis (Frankfurt 区域)
   - 存储：保留最近 1000 条反馈
   - API: `/api/feedback` (POST 提交, GET 查看)

2. ✅ **项目命名统一**
   - GitHub: `denmark-home-calculator`
   - 本地目录: `denmark-home-calculator`
   - Vercel 项目: `denmark-home-calculator` (主站)
   - 域名: `www.boligberegner.com` → `denmark-home-calculator`

3. ✅ **DNS 优化** - Cloudflare 自动配置
   - A 记录: `boligberegner.com` → 216.198.79.1
   - CNAME: `www` → Vercel

**技术栈更新**:
- 新增依赖: `@upstash/redis`
- 环境变量: `UPSTASH_KV_REST_API_URL`, `UPSTASH_KV_REST_API_TOKEN`
- 区域: Frankfurt, Germany (West) - 离丹麦最近

**部署地址**:
- 主站: https://www.boligberegner.com
- Vercel 直连: https://denmark-home-calculator.vercel.app

---

## 📬 反馈监控系统

### 查看反馈方式
1. **API 接口**: `https://www.boligberegner.com/api/feedback`
2. **Upstash 控制台**: Vercel Dashboard → Storage → boligberegner-feedback

### 反馈处理流程
- 新反馈提交 → 存储到 Redis → 保留最近 1000 条
- 建议定期查看并整理到「用户反馈记录」章节
- 高优先级建议单独创建任务跟进

---

*最后更新: 2026-04-06*
