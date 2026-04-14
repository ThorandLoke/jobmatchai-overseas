# BoligBeregner Danmark - 版本发布与恢复流程

> 每次跑通一个产品版本，必须执行本流程保存快照。
> 主模板：见 `/Users/weili/WorkBuddy/Claw/docs/PRODUCT-DEPLOYMENT-WORKFLOW.md`

---

## 快速入口

| 内容 | 链接 |
|-----|------|
| 通用迭代工作流 | `docs/PRODUCT-DEPLOYMENT-WORKFLOW.md` |
| 通用功能文档模板 | `docs/PRODUCT-DEPLOYMENT-WORKFLOW.md` → 第六节 |
| 本项目发布记录 | 下方第四节 |
| 本项目回退操作 | 下方第三节 |

---

## 一、打版本快照（每次迭代上线后必做）

```bash
cd /Users/weili/WorkBuddy/20260329181515/denmark-home-buyer

# 1. 确认当前代码已提交
git status
git add -A && git commit -m "feat: 描述本次改动"

# 2. 打 tag（版本号命名规则：v主版本.次版本-说明）
git tag -a "v1.x-stable" -m "版本说明：功能描述，测试状态"

# 3. 推送到 GitHub（含 tag）
git push origin main
git push origin --tags
```

### 版本命名规范
| 版本 | 说明 |
|------|------|
| v1.0-stable | 基础三模块（买/卖/改造）+ SEO |
| v1.1-stable | 下一个稳定迭代 |
| v2.0-stable | 新增房产市场模块 |

---

## 二、查看所有历史版本

```bash
git tag -l
git log --oneline --decorate
```

---

## 三、恢复到任意历史版本

```bash
# 查看某个版本的内容（不修改当前代码）
git show v1.0-stable

# 切换到某个版本（只读模式）
git checkout v1.0-stable

# 回到最新版本
git checkout main

# ⚠️ 危险：强制回退到某版本（会覆盖当前代码，谨慎！）
# git reset --hard v1.0-stable
```

---

## 四、当前版本记录

| Tag | 日期 | 功能描述 | 部署状态 |
|-----|------|---------|---------|
| v1.0-stable | 2026-04-03 | 买/卖/改造三模块 + SEO（sitemap、robots、OG）| ✅ Vercel 已验证 |

---

## 五、注意事项（知识产权保护）

- ✅ 代码在私有仓库 `ThorandLoke/denmark-home-calculator`
- ✅ 每次提交包含版权声明 `© 2026 BoligBeregner Danmark`
- ❌ 不要把 `.env` 文件提交到 Git
- ❌ 核心算法不要发布到公开渠道
