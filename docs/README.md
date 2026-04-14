# Claw 工作区文档导航

> 所有跨项目通用文档存放在此目录。
> ⚠️ 重要：全局状态和知识库在 `.workbuddy/` 目录（见下方），非 `docs/` 目录。

---

## 🚀 新功能迭代标准流程

**必读：**[PRODUCT-DEPLOYMENT-WORKFLOW.md](./PRODUCT-DEPLOYMENT-WORKFLOW.md)

包含：
- 三环境原则（开发 / 预发布 / 生产）
- 6步标准迭代流程
- 分支命名规范
- CHANGELOG 记录规则
- 回退操作手册
- FEATURE 文档模板

---

## 🌍 全局状态与知识库（核心！）

| 文件 | 作用 | 路径 |
|------|------|------|
| **全局项目看板** | 所有项目当前状态一览 | `../.workbuddy/GLOBAL_STATUS.md` |
| **跨项目知识库** | 已验证技术方案记录 | `../.workbuddy/KNOWLEDGE_BASE.md` |

> 💡 在任意项目对话里，遇到技术问题时先查知识库，避免重复踩坑。

---

## 📁 项目级文档

| 项目 | 流程文档 | 环境配置 |
|------|---------|---------|
| JobMatchAI-Nordic | `JobMatchAI-Nordic/docs/RD-PROCESS.md` | 本地 `localhost:8000` / 生产 `jobmatchai-37ld.onrender.com` |
| BoligBeregner-Danmark | `BoligBeregner-Danmark/RELEASE-WORKFLOW.md` | 本地 `localhost:3000` / 生产 `denmark-home-calculator.vercel.app` |

---

## 📋 新项目启动清单（复制到项目 docs/ 目录）

参考 `PRODUCT-DEPLOYMENT-WORKFLOW.md` → 第七节：

1. [ ] 确认主力项目目录（其他设为只读）
2. [ ] 记录生产/测试/本地环境地址
3. [ ] 创建 `CHANGELOG.md`（根目录，v0.1 开始）
4. [ ] 创建 `docs/` 目录放功能文档
5. [ ] 配置 CI/CD 自动部署 main 分支
6. [ ] 打第一个 stable 标签

---

*导航制定日期：2026-04-07*
