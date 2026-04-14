"use client";

import { useState } from "react";
import type { Lang } from "../lib/ai-types";

export interface FormulaTooltipProps {
  formula: {
    title: Record<Lang, string>;
    content: Record<Lang, string>;
  };
  lang: Lang;
  icon?: string;
}

// 计算公式数据 - 每个 AI 功能对应的计算方法
export const AI_FEATURE_FORMULAS: Record<string, {
  title: Record<Lang, string>;
  content: Record<Lang, string>;
}> = {
  // 1. 智能定价
  pricing: {
    title: {
      zh: "📊 智能定价计算公式",
      en: "📊 Smart Pricing Formula",
      da: "📊 Prisanalyse formel",
    },
    content: {
      zh: `计算方法：
与区域均价对比

区域均价 = 该区域最近6个月成交房产的平均单价（DKK/m²）

评估逻辑：
· 如果您的预算 > 区域均价：可能买贵了
· 如果您的预算 ≈ 区域均价：价格合理
· 如果您的预算 < 区域均价：有议价空间

数据来源：
丹麦房产成交数据（估算值）`,
      en: `Calculation Method:
Compare with area average price

Area Average = Average price per m² of recent sales in the area (last 6 months)

Assessment Logic:
· If your budget > area average: May be overpriced
· If your budget ≈ area average: Fair price
· If your budget < area average: Room for negotiation

Data Source:
Danish property sales data (estimated)`,
      da: `Beregningsmetode:
Sammenlign med områdegennemsnit

Områdegennemsnit = Gennemsnitlig pris per m² for nylige salg i området (sidste 6 måneder)

Vurderingslogik:
· Hvis din budget > områdegennemsnit: Kan være overpris
· Hvis din budget ≈ områdegennemsnit: Retfærdig pris
· Hvis din budget < områdegennemsnit: Forhandlingsrum

Datakilde:
Danske ejendomssalg (estimeret)`,
    },
  },

  // 2. 隐藏费用
  hidden: {
    title: {
      zh: "⚠️ 隐藏费用计算公式",
      en: "⚠️ Hidden Costs Formula",
      da: "⚠️ Skjulte udgifter formel",
    },
    content: {
      zh: `计算方法：
基于丹麦房产交易标准费用估算

主要隐藏费用项：
1. 登记费 = 房价 × 0.6%
2. 律师费 = 房价 × 0.15% (最低10,000 DKK)
3. 产权保险 = 房价 × 0.05% (或固定2,500 DKK)
4. 房屋状况报告 ≈ 4,000-8,000 DKK
5. 电力检查报告 ≈ 1,500-3,500 DKK
6. 能源标识 ≈ 1,500-3,000 DKK

总计估算：
约为房价的 1-2%（不含中介费）`,
      en: `Calculation Method:
Based on standard Danish property transaction fees

Main Hidden Costs:
1. Land Registry Fee = Price × 0.6%
2. Legal Fees = Price × 0.15% (min 10,000 DKK)
3. Property Insurance = Price × 0.05% (or fixed 2,500 DKK)
4. Condition Report ≈ 4,000-8,000 DKK
5. Electrical Report ≈ 1,500-3,500 DKK
6. Energy Label ≈ 1,500-3,000 DKK

Total Estimate:
Approximately 1-2% of property price (excl. agent fees)`,
      da: `Beregningsmetode:
Baseret på standard danske ejendomshandelsgebyrer

Vigtige skjulte omkostninger:
1. Tinglysningsafgift = Pris × 0,6%
2. Advokathonorar = Pris × 0,15% (min 10.000 DKK)
3. Ejendomsforsikring = Pris × 0,05% (eller fast 2.500 DKK)
4. Tilstandsrapport ≈ 4.000-8.000 DKK
5. Elinstallationsrapport ≈ 1.500-3.500 DKK
6. Energimærkning ≈ 1.500-3.000 DKK

Samlet estimat:
Ca. 1-2% af ejendomsprisen (ekskl. mæglergebyrer)`,
    },
  },

  // 3. 贷款优化
  loan: {
    title: {
      zh: "🏦 贷款计算公式",
      en: "🏦 Loan Calculation Formula",
      da: "🏦 Låneberegning formel",
    },
    content: {
      zh: `计算方法：
等额本息还款法

月供计算：
M = P × [r(1+r)^n] / [(1+r)^n - 1]

其中：
M = 每月还款额
P = 贷款本金
r = 月利率 (年利率 ÷ 12)
n = 还款月数

丹麦常见参数：
· 首付比例：通常 20%
· 利率：约 3-4% (2024年)
· 贷款期限：通常 20-30 年

注意事项：
实际利率因银行而异，建议比较多家银行方案`,
      en: `Calculation Method:
Equal monthly payment (annuity)

Monthly Payment Formula:
M = P × [r(1+r)^n] / [(1+r)^n - 1]

Where:
M = Monthly payment
P = Principal
r = Monthly rate (annual rate ÷ 12)
n = Number of payments

Common Danish Parameters:
· Down payment: Typically 20%
· Interest rate: ~3-4% (2024)
· Loan term: Usually 20-30 years

Note:
Actual rates vary by bank. Compare multiple options.`,
      da: `Beregningsmetode:
Lige månedlige betalinger (annuitet)

Månedlig betalingsformel:
M = P × [r(1+r)^n] / [(1+r)^n - 1]

Hvor:
M = Månedlig betaling
P = Hovedstol
r = Månedlig rente (årlig rente ÷ 12)
n = Antal betalinger

Almindelige danske parametre:
· Udbetaling: Typisk 20%
· Rente: Ca. 3-4% (2024)
· Låneperiode: Normalt 20-30 år

Bemærk:
Faktiske satser varierer efter bank. Sammenlign flere muligheder.`,
    },
  },

  // 4. 投资回报
  roi: {
    title: {
      zh: "📈 投资回报计算公式",
      en: "📈 ROI Calculation Formula",
      da: "📈 Investeringsafkast formel",
    },
    content: {
      zh: `计算方法：
租金回报率分析

毛租金回报率：
毛回报率 = (年租金 ÷ 房价) × 100%

净租金回报率：
净回报率 = (年租金 × 70%) ÷ 房价 × 100%
（扣除30%：税费约15% + 维修约10% + 空置约5%）

回本周期：
回本年限 = 房价 ÷ 年净收益

示例（200万房产，100m²）：
· 月租金：180 × 100 = 18,000 DKK
· 年租金：216,000 DKK
· 毛回报率：216,000 ÷ 2,000,000 = 10.8%
· 净回报率：216,000 × 0.7 ÷ 2,000,000 = 7.5%`,
      en: `Calculation Method:
Rental yield analysis

Gross Rental Yield:
Gross Yield = (Annual Rent ÷ Price) × 100%

Net Rental Yield:
Net Yield = (Annual Rent × 70%) ÷ Price × 100%
(Deducting 30%: tax ~15% + maintenance ~10% + vacancy ~5%)

Break-even Period:
Years to Break-even = Price ÷ Annual Net Income

Example (2M property, 100m²):
· Monthly rent: 180 × 100 = 18,000 DKK
· Annual rent: 216,000 DKK
· Gross yield: 216,000 ÷ 2,000,000 = 10.8%
· Net yield: 216,000 × 0.7 ÷ 2,000,000 = 7.5%`,
      da: `Beregningsmetode:
Lejeafkast analyse

Bruttolejeafkast:
Bruttoafkast = (Årlig leje ÷ Pris) × 100%

Nettolejeafkast:
Nettoafkast = (Årlig leje × 70%) ÷ Pris × 100%
(Fratrækker 30%: skat ~15% + vedligeholdelse ~10% + tomgang ~5%)

Break-even periode:
År til break-even = Pris ÷ Årlig nettoindkomst

Eksempel (2M ejendom, 100m²):
· Månedlig leje: 180 × 100 = 18.000 DKK
· Årlig leje: 216.000 DKK
· Bruttoafkast: 216.000 ÷ 2.000.000 = 10,8%
· Nettoafkast: 216.000 × 0,7 ÷ 2.000.000 = 7,5%`,
    },
  },

  // 5. 装修优先级
  renovation: {
    title: {
      zh: "🔧 装修 ROI 计算公式",
      en: "🔧 Renovation ROI Formula",
      da: "🔧 Renovering ROI formel",
    },
    content: {
      zh: `计算方法：
装修投资回报率分析

单次装修 ROI：
装修 ROI = (增值额 - 成本) ÷ 成本 × 100%

考虑增值率：
· 能源改造（热泵、保温）：增值率高（约1.5-2x投资）
· 厨房/卫生间翻新：中等增值（约1.2-1.5x投资）
· 美观改造（油漆、地板）：增值率较低（约1.1x投资）

丹麦常见装修成本估算：
· 热泵安装：80,000-150,000 DKK
· 窗户更换：3,000-6,000 DKK/扇
· 外墙保温：800-1,500 DKK/m²
· 厨房翻新：100,000-300,000 DKK`,
      en: `Calculation Method:
Renovation ROI analysis

Single Renovation ROI:
Renovation ROI = (Value Added - Cost) ÷ Cost × 100%

Value-Add Rates:
· Energy improvements (heat pump, insulation): High (~1.5-2x)
· Kitchen/bathroom renovation: Medium (~1.2-1.5x)
· Cosmetic improvements (paint, flooring): Lower (~1.1x)

Common Danish Renovation Costs:
· Heat pump installation: 80,000-150,000 DKK
· Window replacement: 3,000-6,000 DKK/window
· Wall insulation: 800-1,500 DKK/m²
· Kitchen renovation: 100,000-300,000 DKK`,
      da: `Beregningsmetode:
Renovering ROI analyse

Enkelt renovering ROI:
Renovering ROI = (Værditilvækst - Omkostning) ÷ Omkostning × 100%

Værditilvækst satser:
· Energieffektivisering (varmepumpe, isolering): Høj (~1,5-2x)
· Køkken/badeværelse renovering: Mellem (~1,2-1,5x)
· Kosmetiske forbedringer (maling, gulve): Lavere (~1,1x)

Almindelige danske renoveringsomkostninger:
· Varmepumpe installation: 80.000-150.000 DKK
· Vinduesudskiftning: 3.000-6.000 DKK/vindue
· Vægisolering: 800-1.500 DKK/m²
· Køkkenrenovering: 100.000-300.000 DKK`,
    },
  },

  // 6. 市场趋势
  market: {
    title: {
      zh: "🌍 市场趋势分析说明",
      en: "🌍 Market Trend Analysis",
      da: "🌍 Markedstendens analyse",
    },
    content: {
      zh: `分析方法：
基于区域历史价格数据

趋势判断依据：
· 过去12个月价格变化
· 与全国平均涨幅对比
· 供需关系分析

趋势类型：
📈 上升：价格持续上涨，适合买入
📉 下降：价格下跌，考虑等待或议价
➡️ 稳定：价格波动小，按需购买

数据来源：
丹麦房产历史成交数据（估算）`,
      en: `Analysis Method:
Based on regional historical price data

Trend Indicators:
· Price changes over past 12 months
· Comparison with national average growth
· Supply and demand analysis

Trend Types:
📈 Rising: Prices steadily increasing, good time to buy
📉 Falling: Prices declining, consider waiting or negotiating
➡️ Stable: Minimal price fluctuation, buy as needed

Data Source:
Danish property historical sales data (estimated)`,
      da: `Analysemetode:
Baseret på regionale historiske prisdatas

Tendensindikatorer:
· Prisændringer over de seneste 12 måneder
· Sammenligning med national gennemsnitlig vækst
· Udbud og efterspørgselsanalyse

Tendens typer:
📈 Stigende: Priserne stiger støt, god tid at købe
📉 Faldende: Priserne falder, overvej at vente eller forhandle
➡️ Stabil: Minimal prissvingning, køb efter behov

Datakilde:
Danske ejendoms historiske salgsdata (estimeret)`,
    },
  },

  // 7. 比价助手
  compare: {
    title: {
      zh: "🔍 比价助手说明",
      en: "🔍 Price Comparison Guide",
      da: "🔍 Prissammenligning vejledning",
    },
    content: {
      zh: `对比方法：
同区域同类型房源价格比较

比较维度：
1. 单价对比（DKK/m²）
   - 您的房产 vs 区域平均
2. 房型对比
   - 相同卧室数量的价格
3. 房龄对比
   - 同年代房子的价格区间
4. 配套对比
   - 能源标识、装修状况

评估标准：
• 低于均价10%以内：合理
• 低于均价10-20%：有竞争力
• 高于均价10%+：需谨慎`,
      en: `Comparison Method:
Compare similar properties in the same area

Comparison Dimensions:
1. Price per m²
   - Your property vs area average
2. Property Type
   - Prices for similar bedroom count
3. Age
   - Price range for similar age properties
4. Condition
   - Energy label, renovation status

Assessment Standards:
· Within 10% of average: Reasonable
· 10-20% below average: Competitive
· 10%+ above average: Proceed with caution`,
      da: `Sammenligningsmetode:
Sammenlign lignende ejendomme i samme område

Sammenligningsdimensioner:
1. Pris per m²
   - Din ejendom vs områdegennemsnit
2. Ejendomstype
   - Priser for lignende værelsetal
3. Alder
   - Prisinterval for ejendomme af lignende alder
4. Stand
   - Energimærke, renoveringsstatus

Vurderingsstandarder:
· Inden for 10% af gennemsnit: Rimelig
· 10-20% under gennemsnit: Konkurrencedygtig
· 10%+ over gennemsnit: Udvis forsigtighed`,
    },
  },
};

export default function FormulaTooltip({ formula, lang, icon = "💡" }: FormulaTooltipProps) {
  const [expanded, setExpanded] = useState(false);

  return (
    <div className="relative inline-block ml-1">
      <span
        role="button"
        tabIndex={0}
        className="inline-flex items-center justify-center w-5 h-5 text-xs text-purple-500 bg-purple-100 rounded-full cursor-pointer hover:bg-purple-200 transition-colors"
        title={lang === "zh" ? "查看计算公式" : lang === "en" ? "View formula" : "Se formel"}
        onMouseEnter={() => setExpanded(true)}
        onMouseLeave={() => setExpanded(false)}
        onFocus={() => setExpanded(true)}
        onBlur={() => setExpanded(false)}
      >
        {icon}
      </span>

      {expanded && (
        <div
          className="fixed left-4 bottom-4 w-80 p-4 bg-white border-2 border-purple-300 rounded-xl shadow-2xl text-xs z-[100]"
          style={{ maxHeight: '400px', overflowY: 'auto', minHeight: '200px' }}
        >
          <div className="flex items-center justify-between mb-2 shrink-0">
            <h4 className="font-bold text-purple-900">
              {formula.title[lang]}
            </h4>
            <span
              role="button"
              tabIndex={0}
              onClick={() => setExpanded(false)}
              onKeyDown={(e) => {
                if (e.key === "Enter" || e.key === " ") {
                  setExpanded(false);
                }
              }}
              className="text-gray-400 hover:text-gray-600 text-lg leading-none cursor-pointer"
            >
              ×
            </span>
          </div>
          <div className="text-gray-700 whitespace-pre-wrap leading-relaxed text-sm">
            {formula.content[lang]
              .replace(/\n{3,}/g, '\n\n')
              .replace(/\*\*/g, '')
              .replace(/•/g, '·')
              .trim()}
          </div>
        </div>
      )}
    </div>
  );
}
