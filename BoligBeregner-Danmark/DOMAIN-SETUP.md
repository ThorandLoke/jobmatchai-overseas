# BoligBeregner 域名配置指南

> **创建时间**: 2026-04-06
> **目的**: 配置自定义域名，解决反馈功能无法使用的问题

---

## 当前部署状态

| 项目 | Vercel 项目名 | 当前域名 | 目标域名 |
|------|--------------|---------|---------|
| 主站 | denmark-home-calculator | denmark-home-calculator.vercel.app | www.boligberegner.com |
| 运营站 | denmark-home-buyer | denmark-home-buyer.vercel.app | boligberegner.com |

---

## 配置步骤

### 步骤 1: 在 Vercel 控制台添加域名

1. 登录 [Vercel Dashboard](https://vercel.com/dashboard)
2. 选择项目 `denmark-home-calculator`
3. 进入 **Settings** → **Domains**
4. 添加域名：`www.boligberegner.com`
5. Vercel 会提供 DNS 配置信息

### 步骤 2: 在域名服务商配置 DNS

**需要添加的记录：**

| 类型 | 主机记录 | 记录值 | 说明 |
|------|---------|--------|------|
| A | @ | 76.76.21.21 | 根域名指向 Vercel |
| CNAME | www | cname.vercel-dns.com | www 子域名指向 Vercel |

> 注：具体记录值以 Vercel 提供的为准

### 步骤 3: 验证配置

1. 等待 DNS 生效（通常 5-30 分钟）
2. 访问 `www.boligberegner.com`
3. 测试反馈功能是否正常工作

---

## 项目命名统一

### 已完成 ✅

| 位置 | 旧名称 | 新名称 |
|------|--------|--------|
| GitHub 仓库 | denmark-home-calculator | denmark-home-calculator ✅ 保持不变 |
| 本地目录 | denmark-home-buyer | denmark-home-calculator ✅ 已重命名 |

### 待确认

- Vercel 项目名是否需要调整？
- 是否需要将运营站合并到主站？

---

## 反馈功能问题

**问题原因**: `www.boligberegner.com` 未绑定到 Vercel 项目，API 路由无法访问

**解决方案**: 配置自定义域名后，反馈功能将自动正常工作

---

## 相关文件

- `app/api/feedback/route.ts` - 反馈 API 路由
- `app/page.tsx` - 反馈表单前端代码

---

*最后更新: 2026-04-06*
