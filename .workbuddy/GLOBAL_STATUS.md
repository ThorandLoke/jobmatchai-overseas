# Claw 全局项目看板

> 维护规则：每个项目有进展时，更新对应项目行。所有对话都读写此文件。
> 制定日期：2026-04-07

---

## 活跃项目总览

| 项目 | 状态 | 产品地址 | 本地端口 | 最后更新 | 本周重点 |
|------|------|---------|---------|---------|---------|
| JobMatchAI-Nordic | 🟡 Beta测试 | https://jobmatchai-37ld.onrender.com | 8000 | 2026-04-07 | Beta数据收集 + 三语界面测试 |
| BoligBeregner-Danmark | 🟢 运营中 | https://denmark-home-calculator.vercel.app | 3000 | 2026-04-07 | 推广优化 + GA4集成 |

---

## 项目详情

### JobMatchAI-Nordic

**定位**：AI智能求职平台（北欧华人市场，中英丹三语）

**当前阶段**：Beta 公开测试

**技术栈**：Python FastAPI + HTML单文件前端 + SQLite

**环境配置**：
- 开发：`http://localhost:8000`
- 生产：`https://jobmatchai-37ld.onrender.com`
- GitHub：`https://github.com/ThorandLoke/jobmatchai`（main分支自动部署）

**待办**：
- [ ] Thor 测试三语界面，反馈修改意见
- [ ] Beta 数据收集优化（early_bird.py）
- [ ] 下一功能：简历精修 / 职位智能匹配

**发布记录**：
| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-04-01 | v0.9 | Beta 上线 |
| 2026-04-07 | v1.0 | 三语界面 + 多项目流程文档 |

---

### BoligBeregner-Danmark

**定位**：丹麦房产计算工具（买/卖/改造三模块，三语）

**当前阶段**：运营中（无活跃开发）

**技术栈**：Next.js + TypeScript + Tailwind CSS + Vercel

**环境配置**：
- 开发：`http://localhost:3000`
- 生产：`https://denmark-home-calculator.vercel.app`
- GitHub：`ThorandLoke/denmark-home-calculator`（私有）

**待办**：
- [ ] GA4 集成
- [ ] 卖房模块重测（上次修改后未确认）

**发布记录**：
| 日期 | 版本 | 说明 |
|------|------|------|
| 2026-04-03 | v1.0-stable | 三模块 + SEO + 广告配置 |
| 2026-04-04 | v1.1 | 免责声明 + 标签修改 + 广告13个 |

---

## 新项目模板

新项目创建时，在此添加一行，并参考 `docs/PRODUCT-DEPLOYMENT-WORKFLOW.md` 建立项目文档。

---

*最后更新：2026-04-07 by Loke*
