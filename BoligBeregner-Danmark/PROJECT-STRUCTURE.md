# BoligBeregner 项目结构整理

**整理日期**: 2026-04-12
**负责人**: Thor & Loke

---

## 🏠 当前实际项目结构

```
/Users/weili/WorkBuddy/Claw/BoligBeregner-Danmark/
│
├── 📦 主要代码目录
│   ├── denmark-home-calculator/          ⭐ 生产环境（当前运行的版本）
│   └── denmark-home-calculator-dev-shade/ ⭐ 开发分支（遮阳棚功能）
│
├── 📁 backups/                            备份文件
│   ├── denmark-home-calculator-v20260412/ ✅ 最新生产备份（3.8MB）
│   └── page-ai-restore-20260404-1003.tsx
│
├── 🌐 Vercel 部署
│   ├── denmark-home-calculator (项目)    → boligberegner.com
│   └── denmark-home-calculator-dev-shade  → dev 预览
│
├── 🌐 域名配置
│   ├── www.boligberegner.com              → 主站（计算器）
│   └── boligberegner.com                  → 运营站（待确认）
│
├── 📱 social-media/                       社媒自动化脚本
│   └── V4/
│
└── 📄 配置文档
    ├── DOMAIN-SETUP.md                    域名配置
    ├── MODIFICATIONS-LOG.md               改动日志
    ├── RELEASE-WORKFLOW.md                发布流程
    └── ...
```

---

## ❌ 发现的问题

### 1. 目录命名混乱
| 目录 | 问题 | 建议 |
|------|------|------|
| `denmark-home-buyer/` | 旧目录，已空 | 删除 |
| `backups/denmark-home-buyer-v20260412/` | 刚做的备份用了旧名 | 重命名为 `denmark-home-calculator-v20260412` |
| `denmark-home-buyer-backup-20260404/` | 旧备份 | 删除或归档 |

### 2. package.json 内部名称错误
```json
// denmark-home-calculator/package.json
"name": "denmark-home-buyer"  ❌ 应该是 "denmark-home-calculator"
```

### 3. GitHub 仓库
- 需要确认 GitHub 仓库名称是否正确

---

## ✅ 建议的清理操作

### 立即执行
1. [ ] 重命名 `backups/denmark-home-buyer-v20260412` → `backups/denmark-home-calculator-v20260412`
2. [ ] 修复 `denmark-home-calculator/package.json` 中的 name 字段
3. [ ] 删除空目录 `denmark-home-buyer`
4. [ ] 评估 `denmark-home-buyer-backup-20260404` 是否需要保留

### 后续确认
5. [ ] 确认 GitHub 仓库名称
6. [ ] 确认 `boligberegner.com` 的用途

---

## 🔗 相关链接

- **生产环境**: https://www.boligberegner.com
- **Vercel Dashboard**: https://vercel.com/dashboard
- **GitHub 仓库**: （待确认）

---

*最后更新: 2026-04-12*
