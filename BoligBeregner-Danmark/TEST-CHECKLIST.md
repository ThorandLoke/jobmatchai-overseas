# 本地测试清单 - BoligBeregner 广告验证

## 📋 测试目标
确认所有 13 个广告在本地显示正常，然后再部署到生产环境。

## 🔍 测试步骤

### 1. 买房模块 (Køb / I Want to Buy)
访问：http://localhost:3001，点击 "Køb" 或 "I Want to Buy" 标签

**检查项：**
- [ ] 买房后出现的贷款比较广告（Pantsat.dk）
  - Banner ID: 78126
  - 位置：在计算结果下方
  - 链接：https://www.partner-ads.com/dk/klikbanner.php?partnerid=56504&bannerid=78126

### 2. 卖房模块 (Sælg / I Want to Sell)
点击 "Sælg" 或 "I Want to Sell" 标签

**检查项：**
- [ ] 房产估值广告（Valuea.dk）
  - Banner ID: 71154
  - 位置：在净收益结果下方，橙色背景
  - 链接：https://www.partner-ads.com/dk/klikbanner.php?partnerid=56504&bannerid=71154

- [ ] 卖房咨询广告（Din-Bolighandel）**新增**
  - Banner ID: 66826
  - 位置：在房产估值广告下方，紫色背景
  - 链接：https://www.partner-ads.com/dk/klikbanner.php?partnerid=56504&bannerid=66826

### 3. 装修模块 (Renovering / Renovation)
点击 "Renovering" 或 "Renovation" 标签

**检查项：**
- [ ] 热泵广告（Heatnow.dk）**已更新**
  - Banner ID: 43265（原 82597）
  - 位置：在热泵计算器结果下方，红色按钮
  - 链接：https://www.partner-ads.com/dk/klikbanner.php?partnerid=56504&bannerid=43265

- [ ] 窗户广告（Tagpap.dk）**已更新**
  - Banner ID: 109565（原 82598）
  - 位置：在窗户计算器结果下方，蓝色按钮
  - 链接：https://www.partner-ads.com/dk/klikbanner.php?partnerid=56504&bannerid=109565

- [ ] 保温广告（Dansk Isolering）**已更新**
  - Banner ID: 105348（原 Coming Soon）
  - 位置：在保温计算器结果下方，绿色按钮
  - 链接：https://www.partner-ads.com/dk/klikbanner.php?partnerid=56504&bannerid=105348

- [ ] 颗粒炉广告（DBVVS）**新增**
  - Banner ID: 59457
  - 位置：保温广告下方，独立的颗粒炉模块，橙色按钮
  - 链接：https://www.partner-ads.com/dk/klikbanner.php?partnerid=56504&bannerid=59457

- [ ] VVS 广告（Billigelogvvs.dk）**新增**
  - Banner ID: 99217
  - 位置：颗粒炉广告下方，独立的 VVS 模块，青色按钮
  - 链接：https://www.partner-ads.com/dk/klikbanner.php?partnerid=56504&bannerid=99217

- [ ] 窗户清洁服务广告（Rudernes Konge）**新增**
  - Banner ID: 112335
  - 位置：VVS 广告下方，天空色按钮
  - 链接：https://www.partner-ads.com/dk/klikbanner.php?partnerid=56504&bannerid=112335

- [ ] 窗户清洁机器人广告（RoboShine）**新增**
  - Banner ID: 113490
  - 位置：窗户清洁服务旁边，靛蓝色按钮
  - 链接：https://www.partner-ads.com/dk/klikbanner.php?partnerid=56504&bannerid=113490

- [ ] 通用装修广告（General）
  - Banner ID: 82599
  - 位置：装修模块底部，紫粉渐变背景
  - 链接：https://www.partner-ads.com/dk/klikbanner.php?partnerid=56504&bannerid=82599

### 4. 房产市场模块 (Boligmarked / Housing Market)
点击 "Boligmarked" 或 "Housing Market" 标签

**检查项：**
- [ ] 房屋保险广告（Findforsikring）
  - Banner ID: 60068
  - 位置：页面底部绿色卡片
  - 链接：https://www.partner-ads.com/dk/klikbanner.php?partnerid=56504&bannerid=60068

- [ ] 工匠/装修广告（Håndværker）
  - Banner ID: 92764
  - 位置：页面底部琥珀色卡片
  - 链接：https://www.partner-ads.com/dk/landingpage.php?id=56504&prg=9363&bannerid=92764&desturl=https://velkommen.tilmeld-haandvaerker.dk/3maaned_gratis

- [ ] 房贷比较广告（Pantsat.dk）
  - Banner ID: 78126
  - 位置：页面底部蓝色卡片
  - 链接：https://www.partner-ads.com/dk/klikbanner.php?partnerid=56504&bannerid=78126

### 5. AI 功能模块
查看页面底部的紫色 AI 分析区域

**检查项：**
- [ ] AI 功能卡片的公式提示（🧮 图标）是否正常显示
- [ ] 鼠标悬停是否显示计算公式
- [ ] AI 分析功能是否正常工作

## ✅ 测试结果

**通过的广告：** ___ / 13

**发现的问题：**
- 

**备注：**

---

## 🚀 部署前确认

- [ ] 所有 13 个广告都显示正常
- [ ] 所有链接都正确（检查 `bannerid` 是否匹配）
- [ ] 三语界面（DA/EN/ZH）都正常
- [ ] AI 功能正常工作
- [ ] 无控制台错误

**全部确认后，执行：`vercel --prod`**
