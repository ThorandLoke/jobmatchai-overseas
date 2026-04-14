# 广告配置同步说明

## 当前状态对比

### 当前工作空间 (20260329181515) - 运营版
**13个广告已配置：**

| 板块 | 广告商 | Banner ID | 状态 |
|------|--------|-----------|------|
| 买房-贷款 | Pantsat.dk | 78126 | ✅ |
| 买房-保险 | Findforsikring.dk | 60068 | ✅ |
| 买房/卖房-估价 | Valuea.dk | 71154 | ✅ |
| 卖房-咨询 | Din-Bolighandel ApS | 66826 | ✅ |
| 改造-热泵 | Heatnow.dk | **43265** | ✅ 新批准 |
| 改造-颗粒炉 | DBVVS | 59457 | ✅ |
| 改造-热泵/VVS | Billigelogvvs.dk | 99217 | ✅ |
| 改造-屋顶 | Tagpap.dk | 109565 | ✅ |
| 改造-保温 | Dansk Isolering | 105348 | ✅ |
| 窗户-清洁服务 | Rudernes Konge | 112335 | ✅ 新批准 |
| 窗户-清洁机器人 | RoboShine | 113490 | ✅ 新批准 |

### Claw 主程序 - 功能版
**6个广告（需要更新）：**

| 板块 | 当前 Banner ID | 需要改为 | 说明 |
|------|---------------|----------|------|
| 买房-贷款 | 78126 | 78126 | ✅ 正确 |
| 买房-保险 | 60068 | 60068 | ✅ 正确 |
| 改造-热泵 | **82597** | **43265** | ⚠️ 需要更新为 Heatnow.dk |
| 改造-窗户 | **82598** | **109565** | ⚠️ 需要更新为 Tagpap.dk |
| 改造-保温 | Coming Soon | **105348** | ⚠️ 需要添加 Dansk Isolering |
| 改造-颗粒炉 | 无 | **59457** | ⚠️ 需要添加 DBVVS |
| 改造-VVS | 无 | **99217** | ⚠️ 需要添加 Billigelogvvs.dk |
| 窗户-清洁服务 | 无 | **112335** | ⚠️ 需要添加 Rudernes Konge |
| 窗户-清洁机器人 | 无 | **113490** | ⚠️ 需要添加 RoboShine |
| 卖房-咨询 | 无 | **66826** | ⚠️ 需要添加 Din-Bolighandel |

## 需要同步的代码变更

### 1. 改造板块 (renovate tab)

**热泵部分：**
```tsx
// 旧代码 (Claw)
<a href="https://www.partner-ads.com/dk/klikbanner.php?partnerid=56504&bannerid=82597" ...

// 新代码 (需要改为)
<a href="https://www.partner-ads.com/dk/klikbanner.php?partnerid=56504&bannerid=43265" ...
🔥 {t.compareLoan ? "Få tilbud på varmepumpe →" : "获取热泵报价 →"}
```

**窗户部分：**
```tsx
// 旧代码 (Claw)
<a href="https://www.partner-ads.com/dk/klikbanner.php?partnerid=56504&bannerid=82598" ...

// 新代码 (需要改为)
<a href="https://www.partner-ads.com/dk/klikbanner.php?partnerid=56504&bannerid=109565" ...
🏠 {t.getQuotes}

// 还需要添加以下两个广告：
<a href="https://www.partner-ads.com/dk/klikbanner.php?partnerid=56504&bannerid=112335" ...
🪟 {t.compareLoan ? "Bestil vinduespudsning →" : "预约窗户清洁 →"}

<a href="https://www.partner-ads.com/dk/klikbanner.php?partnerid=56504&bannerid=113490" ...
🤖 {t.compareLoan ? "Køb vinduespudser robot →" : "购买窗户清洁机器人 →"}
```

**保温部分：**
```tsx
// 旧代码 (Claw)
<span className="inline-block px-4 py-2 bg-gray-100 text-gray-500 text-sm rounded-lg">
  🏠 {language === 'zh' ? '保暖改造广告商 Coming Soon' ...}
</span>

// 新代码 (需要改为)
<a href="https://www.partner-ads.com/dk/klikbanner.php?partnerid=56504&bannerid=105348" ...
🏠 {t.getQuotes}
```

**需要新增 - 颗粒炉：**
```tsx
<a href="https://www.partner-ads.com/dk/klikbanner.php?partnerid=56504&bannerid=59457" ...
🔥 {t.compareLoan ? "Få tilbud på brændeovn/pillefyr →" : "获取壁炉/颗粒炉报价 →"}
```

**需要新增 - VVS：**
```tsx
<a href="https://www.partner-ads.com/dk/klikbanner.php?partnerid=56504&bannerid=99217" ...
🔧 {t.compareLoan ? "Få VVS tilbud →" : "获取VVS报价 →"}
```

### 2. 卖房板块 (sell tab)

**需要新增 - 房产咨询：**
```tsx
<a href="https://www.partner-ads.com/dk/klikbanner.php?partnerid=56504&bannerid=66826" ...
🏠 {t.compareLoan ? "Få rådgivning om boligsalg →" : "获取卖房咨询 →"}
```

## 建议操作

由于两边代码结构差异较大，建议：

1. **在 Claw 主程序那边打开新对话**
2. **参考当前工作空间的 `page.tsx` 第 954-1600 行左右的广告配置**
3. **或者直接把当前工作空间的广告部分代码复制过去**

## 两个网站

- **主站** (AI功能完整): https://denmark-home-calculator.vercel.app
- **运营站** (13个广告): https://denmark-home-buyer.vercel.app

当前运营站已经上线并可以赚钱，主站需要同步广告配置后才能替换。
