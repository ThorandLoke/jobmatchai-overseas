"use client";

import { useState, useCallback } from "react";
import { SmartNumberInput } from "./SmartInput";

type Lang = "da" | "en" | "zh";
type TransactionType = "buy" | "sell";

interface FeeItem {
  name: string;
  nameEn: string;
  nameDa: string;
  quoted: number;
  marketMin: number;
  marketMax: number;
  negotiable: boolean;
  tip: string;
  tipEn: string;
  tipDa: string;
}

interface AnalysisResult {
  propertyPrice: number;
  items: FeeItem[];
  totalQuoted: number;
  totalMin: number;
  saving: number;
}

// 丹麦房产交易费用基准数据 (2026年真实数据)
const BUYING_FEE_BENCHMARKS: FeeItem[] = [
  {
    name: "中介费 (Kontorets salær)",
    nameEn: "Agent Fee",
    nameDa: "Mæglergebyr",
    quoted: 0,
    marketMin: 15000,
    marketMax: 45000,
    negotiable: true,
    tip: "中介费通常可以砍价 10-30%，多问几家比较",
    tipEn: "Agent fees are usually negotiable by 10-30%, compare multiple agents",
    tipDa: "Mæglergebyrer er normalt forhandlingsbare med 10-30%, sammenlign flere mæglere",
  },
  {
    name: "广告费 (Markedsføringsomkostninger)",
    nameEn: "Marketing Costs",
    nameDa: "Markedsføringsomkostninger",
    quoted: 0,
    marketMin: 5000,
    marketMax: 15000,
    negotiable: true,
    tip: "广告费包含在中介费中，或可单独议价",
    tipEn: "Marketing costs are often included in agent fee or negotiable separately",
    tipDa: "Markedsføringsomkostninger er ofte inkluderet i mæglergebyret eller forhandles separat",
  },
  {
    name: "照片/视频费",
    nameEn: "Photo/Video",
    nameDa: "Foto/Video",
    quoted: 0,
    marketMin: 0,
    marketMax: 5000,
    negotiable: true,
    tip: "部分中介已包含在广告费中，无需额外支付",
    tipEn: "Some agents include this in marketing fee, no extra charge needed",
    tipDa: "Nogle mæglere inkluderer dette i markedsføringsgebyret",
  },
  {
    name: "能耗报告 (Energimærke)",
    nameEn: "Energy Label",
    nameDa: "Energimærke",
    quoted: 0,
    marketMin: 3000,
    marketMax: 6000,
    negotiable: false,
    tip: "法律强制要求，无法免去",
    tipEn: "Legally required, cannot be waived",
    tipDa: "Lovpligtigt, kan ikke fraviges",
  },
  {
    name: "登记公告费",
    nameEn: "Registration Fee",
    nameDa: "Tinglysningsgebyr",
    quoted: 0,
    marketMin: 1500,
    marketMax: 2000,
    negotiable: false,
    tip: "政府固定收费，无法议价",
    tipEn: "Government fixed fee, non-negotiable",
    tipDa: "Offentligt fast gebyr, kan ikke forhandles",
  },
];

const SELLING_FEE_BENCHMARKS: FeeItem[] = [
  {
    name: "中介费 (Kontorets salær)",
    nameEn: "Agent Fee",
    nameDa: "Mæglergebyr",
    quoted: 0,
    marketMin: 15000,
    marketMax: 60000,
    negotiable: true,
    tip: "中介费通常可以砍价 15-40%，争取最低价或固定费用",
    tipEn: "Agent fees negotiable by 15-40%, negotiate for lowest or fixed fee",
    tipDa: "Mæglergebyrer forhandles med 15-40%, bed om laveste eller fast pris",
  },
  {
    name: "广告费 (Markedsføringsomkostninger)",
    nameEn: "Marketing Costs",
    nameDa: "Markedsføringsomkostninger",
    quoted: 0,
    marketMin: 8000,
    marketMax: 25000,
    negotiable: true,
    tip: "包含专业摄影、视频、3D 扫描等，可要求包含在总价内",
    tipEn: "Includes professional photos, video, 3D scan - negotiate to include in total",
    tipDa: "Inkluderer professionelle billeder, video, 3D scan - forhandl det inkluderet",
  },
  {
    name: "能耗报告 (Energimærke)",
    nameEn: "Energy Label",
    nameDa: "Energimærke",
    quoted: 0,
    marketMin: 3000,
    marketMax: 6000,
    negotiable: false,
    tip: "卖房必须提供，法律强制",
    tipEn: "Required by law when selling",
    tipDa: "Påkrævet ved salg, lovmæssigt krav",
  },
  {
    name: "律师费/公证费 (Advokat)",
    nameEn: "Lawyer Fee",
    nameDa: "Advokat",
    quoted: 0,
    marketMin: 8000,
    marketMax: 20000,
    negotiable: true,
    tip: "可以要求卖方支付或包含在中介费中",
    tipEn: "Can request seller to pay or include in agent fee",
    tipDa: "Kan bede sælger om at betale eller inkludere i mæglergebyr",
  },
  {
    name: "登记费 (Tinglysningsafgift)",
    nameEn: "Registration Fee",
    nameDa: "Tinglysningsafgift",
    quoted: 0,
    marketMin: 0,
    marketMax: 0,
    negotiable: false,
    tip: "卖房无需支付登记费（由买方支付）",
    tipEn: "Seller does not pay registration fee (paid by buyer)",
    tipDa: "Sælger betaler ikke tinglysningsafgift (køber betaler)",
  },
];

const LABELS = {
  zh: {
    title: "📋 报价单分析",
    titleBuy: "🏠 买房报价分析",
    titleSell: "🏷️ 卖房报价分析",
    subtitleBuy: "上传或粘贴中介的报价单，自动识别费用项并分析可议价项目",
    subtitleSell: "输入中介的卖房费用明细，计算实际到账金额",
    inputSection: "📝 输入报价单信息",
    propertyPrice: "房产售价 (kr)",
    enableCustomize: "✏️ 自定义各项费用",
    enableCustomizeHint: "勾选后可以手动输入各项费用，与市场对比",
    quotedAmount: "报价金额",
    totalQuoted: "总费用合计",
    totalMin: "按最低市场价计算",
    potentialSaving: "💰 潜在节省",
    analysisResult: "📊 分析结果",
    breakdown: "费用明细",
    negotiable: "可议价",
    fixed: "固定费用",
    vsMarket: "vs 市场",
    tip: "💡 建议",
    quoted: "报价",
    market: "市场价",
    saving: "可节省",
    netProceeds: "💵 实际到账",
    netProceedsHint: "扣除所有费用后您能拿到的金额",
    negotiationTips: "🎯 谈判建议",
    tip1Buy: "要求中介提供费用明细，逐项讨论",
    tip2Buy: "询问是否有固定费用套餐",
    tip3Buy: "多比较 2-3 家中介的报价",
    tip1Sell: "要求中介明确列出所有费用项",
    tip2Sell: "争取将广告费包含在总费用内",
    tip3Sell: "询问成功卖出后是否有额外费用",
    reset: "🔄 重新分析",
    formatHelp: "支持输入格式：\n• 中介费: xxx kr\n• 广告费: xxx kr\n• 或直接输入总价",
    placeholder: "例如：\n中介费 35000\n广告费 12000\n能耗报告 4500",
  },
  en: {
    title: "📋 Quote Analysis",
    titleBuy: "🏠 Buyer Quote Analysis",
    titleSell: "🏷️ Seller Quote Analysis",
    subtitleBuy: "Upload or paste agent's quote to identify fees and analyze negotiable items",
    subtitleSell: "Enter agent's fee breakdown to calculate your actual proceeds",
    inputSection: "📝 Enter Quote Information",
    propertyPrice: "Property Price (kr)",
    enableCustomize: "✏️ Customize Fees",
    enableCustomizeHint: "Check to manually input fees and compare with market",
    quotedAmount: "Quoted Amount",
    totalQuoted: "Total Quoted",
    totalMin: "At Market Minimum",
    potentialSaving: "💰 Potential Saving",
    analysisResult: "📊 Analysis Results",
    breakdown: "Fee Breakdown",
    negotiable: "Negotiable",
    fixed: "Fixed",
    vsMarket: "vs Market",
    tip: "💡 Suggestion",
    quoted: "Quoted",
    market: "Market",
    saving: "Can Save",
    netProceeds: "💵 Net Proceeds",
    netProceedsHint: "Amount you'll receive after all fees",
    negotiationTips: "🎯 Negotiation Tips",
    tip1Buy: "Request itemized fee breakdown and discuss each item",
    tip2Buy: "Ask about fixed-fee packages",
    tip3Buy: "Compare quotes from 2-3 agents",
    tip1Sell: "Request clear breakdown of all fees",
    tip2Sell: "Negotiate to include marketing in total fee",
    tip3Sell: "Ask about extra fees after successful sale",
    reset: "🔄 Reset",
    formatHelp: "Supported formats:\n• Agent fee: xxx kr\n• Marketing: xxx kr\n• Or just total amount",
    placeholder: "Example:\nAgent fee 35000\nMarketing 12000\nEnergy label 4500",
  },
  da: {
    title: "📋 Tilbudsanalyse",
    titleBuy: "🏠 Køber Tilbudsanalyse",
    titleSell: "🏷️ Sælger Tilbudsanalyse",
    subtitleBuy: "Upload eller indsæt mæglerens tilbud for at identificere gebyrer og analysere forhandlingsbare poster",
    subtitleSell: "Indtast mæglerens gebyroversigt for at beregne dine faktiske provenu",
    inputSection: "📝 Indtast Tilbudsoplysninger",
    propertyPrice: "Ejendomspris (kr)",
    enableCustomize: "✏️ Tilpas Gebyrer",
    enableCustomizeHint: "Aktiver for at indtaste gebyrer manuelt og sammenligne med marked",
    quotedAmount: "Tilbudt Beløb",
    totalQuoted: "Samlet Tilbudt",
    totalMin: "Markedsminimum",
    potentialSaving: "💰 Mulig Besparelse",
    analysisResult: "📊 Analyseresultater",
    breakdown: "Gebyrfordeling",
    negotiable: "Forhandlingsbar",
    fixed: "Fast",
    vsMarket: "vs Marked",
    tip: "💡 Forslag",
    quoted: "Tilbudt",
    market: "Marked",
    saving: "Kan Spare",
    netProceeds: "💵 Netto Provenu",
    netProceedsHint: "Beløb du modtager efter alle gebyrer",
    negotiationTips: "🎯 Forhandlingstips",
    tip1Buy: "Anmod om specifikation af gebyrer og diskuter hver post",
    tip2Buy: "Spørg om fast pris-pakker",
    tip3Buy: "Sammenlign tilbud fra 2-3 mæglere",
    tip1Sell: "Anmod om klar fordeling af alle gebyrer",
    tip2Sell: "Forhandl om at inkludere markedsføring i samlet gebyr",
    tip3Sell: "Spørg om ekstra gebyrer efter vellykket salg",
    reset: "🔄 Nulstil",
    formatHelp: "Understøttede formater:\n• Mæglergebyr: xxx kr\n• Markedsføring: xxx kr\n• Eller kun samlet beløb",
    placeholder: "Eksempel:\nMæglergebyr 35000\nMarkedsføring 12000\nEnergimærke 4500",
  },
};

function formatCurrency(amount: number, lang: Lang): string {
  return amount.toLocaleString("da-DK") + " kr";
}

function getLocalizedName(item: FeeItem, lang: Lang): string {
  if (lang === "zh") return item.name;
  if (lang === "en") return item.nameEn;
  return item.nameDa;
}

function getLocalizedTip(item: FeeItem, lang: Lang): string {
  if (lang === "zh") return item.tip;
  if (lang === "en") return item.tipEn;
  return item.tipDa;
}

interface QuoteAnalyzerProps {
  type: TransactionType;
  language: Lang;
  initialPrice?: string;
}

export default function QuoteAnalyzer({ type, language, initialPrice = "" }: QuoteAnalyzerProps) {
  const l = LABELS[language];
  const isBuy = type === "buy";
  
  const [propertyPrice, setPropertyPrice] = useState(initialPrice);
  const [enableCustomize, setEnableCustomize] = useState(false);
  const [customFees, setCustomFees] = useState<{ [key: string]: string }>({});
  const [showResult, setShowResult] = useState(false);

  const benchmarks = isBuy ? BUYING_FEE_BENCHMARKS : SELLING_FEE_BENCHMARKS;

  // 计算分析结果
  const analysis = useCallback((): AnalysisResult | null => {
    if (!propertyPrice || parseFloat(propertyPrice) <= 0) return null;

    const price = parseFloat(propertyPrice);
    
    // 根据房产价格计算基准费用
    const items: FeeItem[] = benchmarks.map(item => {
      let quoted = item.quoted;
      
      if (enableCustomize && customFees[item.name]) {
        quoted = parseFloat(customFees[item.name]) || 0;
      } else {
        // 默认报价 = 中间市场价（模拟中介报价）
        quoted = (item.marketMin + item.marketMax) / 2;
        if (item.quoted > 0) quoted = item.quoted;
      }
      
      return { ...item, quoted };
    });

    const totalQuoted = items.reduce((sum, item) => sum + item.quoted, 0);
    const totalMin = items.reduce((sum, item) => sum + item.marketMin, 0);
    const saving = items.reduce((sum, item) => {
      if (item.negotiable) {
        return sum + Math.max(0, item.quoted - item.marketMin);
      }
      return sum;
    }, 0);

    return {
      propertyPrice: price,
      items,
      totalQuoted,
      totalMin,
      saving,
    };
  }, [propertyPrice, enableCustomize, customFees, benchmarks]);

  const result = analysis();

  const handleCustomFeeChange = (name: string, value: string) => {
    setCustomFees(prev => ({ ...prev, [name]: value }));
  };

  const reset = () => {
    setPropertyPrice("");
    setCustomFees({});
    setShowResult(false);
    setEnableCustomize(false);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className={`rounded-2xl shadow-xl p-6 ${
        isBuy 
          ? "bg-gradient-to-br from-green-50 to-emerald-100 border border-green-200" 
          : "bg-gradient-to-br from-orange-50 to-amber-100 border border-orange-200"
      }`}>
        <div className="flex items-center gap-3 mb-2">
          <span className="text-3xl">{isBuy ? "🏠" : "🏷️"}</span>
          <div>
            <h2 className="text-xl font-bold text-gray-900">
              {isBuy ? l.titleBuy : l.titleSell}
            </h2>
          </div>
        </div>
        <p className="text-gray-600 text-sm">
          {isBuy ? l.subtitleBuy : l.subtitleSell}
        </p>
      </div>

      {/* Input Section */}
      <div className="bg-white rounded-2xl shadow-xl p-6">
        <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
          {l.inputSection}
        </h3>

        {/* Property Price */}
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            💰 {l.propertyPrice}
          </label>
          <SmartNumberInput
            value={propertyPrice}
            onChange={setPropertyPrice}
            placeholder="1.500.000"
            inputClassName="w-full px-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:outline-none text-lg font-semibold"
          />
          <p className="text-xs text-gray-400 mt-1">
            💡 {language === "zh" ? "点击后输入您的房产价格" : language === "en" ? "Click and enter your property price" : "Klik og indtast din ejendomspris"}
          </p>
        </div>

        {/* Customize Toggle */}
        <div className={`p-4 rounded-xl border-2 ${
          enableCustomize 
            ? "border-blue-300 bg-blue-50" 
            : "border-gray-200 bg-gray-50"
        }`}>
          <div className="flex items-center justify-between mb-2">
            <label className="flex items-center gap-2 cursor-pointer">
              <input
                type="checkbox"
                checked={enableCustomize}
                onChange={(e) => setEnableCustomize(e.target.checked)}
                className="w-5 h-5 rounded border-gray-300 text-blue-500 focus:ring-blue-500"
              />
              <span className="font-semibold text-gray-900">{l.enableCustomize}</span>
            </label>
          </div>
          <p className="text-xs text-gray-500">{l.enableCustomizeHint}</p>
        </div>

        {/* Custom Fee Inputs */}
        {enableCustomize && (
          <div className="mt-4 space-y-3">
            {benchmarks.map((item, idx) => (
              <div key={idx} className="flex items-center gap-3">
                <div className={`flex-1 px-3 py-2 rounded-lg text-sm ${
                  item.negotiable 
                    ? "bg-blue-50 text-blue-700" 
                    : "bg-gray-100 text-gray-600"
                }`}>
                  {getLocalizedName(item, language)}
                  {item.negotiable && (
                    <span className="ml-2 text-xs bg-blue-200 px-1 rounded">{l.negotiable}</span>
                  )}
                </div>
                <div className="flex items-center gap-1">
                  <input
                    type="text"
                    value={customFees[item.name] || ""}
                    onChange={(e) => handleCustomFeeChange(item.name, e.target.value)}
                    placeholder="0"
                    className="w-28 px-3 py-2 border rounded-lg text-right font-medium"
                  />
                  <span className="text-gray-500 text-sm">kr</span>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Analyze Button */}
        {propertyPrice && parseFloat(propertyPrice) > 0 && (
          <button
            onClick={() => setShowResult(true)}
            className={`w-full mt-6 px-6 py-4 rounded-xl font-bold text-white text-lg transition ${
              isBuy
                ? "bg-gradient-to-r from-green-500 to-emerald-600 hover:from-green-600 hover:to-emerald-700"
                : "bg-gradient-to-r from-orange-500 to-amber-600 hover:from-orange-600 hover:to-amber-700"
            }`}
          >
            {isBuy ? "🔍 分析买房费用" : "🔍 分析卖房收益"}
          </button>
        )}
      </div>

      {/* Analysis Results */}
      {showResult && result && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className={`rounded-xl shadow-lg p-6 ${
              isBuy ? "bg-white border-2 border-blue-100" : "bg-white border-2 border-orange-100"
            }`}>
              <p className="text-sm text-gray-500 mb-1">{l.totalQuoted}</p>
              <p className={`text-2xl font-bold ${isBuy ? "text-blue-600" : "text-orange-600"}`}>
                {formatCurrency(result.totalQuoted, language)}
              </p>
            </div>
            <div className="bg-white rounded-xl shadow-lg p-6 border-2 border-green-100">
              <p className="text-sm text-gray-500 mb-1">{l.potentialSaving}</p>
              <p className="text-2xl font-bold text-green-600">
                {formatCurrency(result.saving, language)}
              </p>
            </div>
            {isBuy && (
              <div className="bg-white rounded-xl shadow-lg p-6 border-2 border-gray-100">
                <p className="text-sm text-gray-500 mb-1">{l.totalMin}</p>
                <p className="text-2xl font-bold text-gray-600">
                  {formatCurrency(result.totalMin, language)}
                </p>
              </div>
            )}
            {!isBuy && (
              <div className="bg-white rounded-xl shadow-lg p-6 border-2 border-emerald-100">
                <p className="text-sm text-gray-500 mb-1">{l.netProceeds}</p>
                <p className="text-2xl font-bold text-emerald-600">
                  {formatCurrency(result.propertyPrice - result.totalQuoted, language)}
                </p>
                <p className="text-xs text-gray-400 mt-1">{l.netProceedsHint}</p>
              </div>
            )}
          </div>

          {/* Fee Breakdown */}
          <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
            <div className={`px-6 py-4 border-b ${
              isBuy ? "bg-blue-50" : "bg-orange-50"
            }`}>
              <h3 className="font-bold text-gray-900">{l.breakdown}</h3>
            </div>
            <div className="p-6">
              <div className="space-y-4">
                {result.items.map((item, idx) => {
                  const saving = item.negotiable ? Math.max(0, item.quoted - item.marketMin) : 0;
                  
                  return (
                    <div
                      key={idx}
                      className={`p-4 rounded-xl border-2 ${
                        item.negotiable
                          ? "bg-blue-50 border-blue-200"
                          : "bg-gray-50 border-gray-200"
                      }`}
                    >
                      <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                          <span className={`text-xs px-2 py-1 rounded-full font-medium ${
                            item.negotiable
                              ? "bg-blue-100 text-blue-700"
                              : "bg-gray-200 text-gray-600"
                          }`}>
                            {item.negotiable ? `✅ ${l.negotiable}` : `🔒 ${l.fixed}`}
                          </span>
                          <span className="font-semibold text-gray-900">
                            {getLocalizedName(item, language)}
                          </span>
                        </div>
                        <div className="text-right">
                          <p className="font-bold text-gray-900">
                            {formatCurrency(item.quoted, language)}
                          </p>
                          {item.negotiable && item.marketMin > 0 && (
                            <p className="text-xs text-gray-500">
                              {l.vsMarket}: {formatCurrency(item.marketMin, language)}
                            </p>
                          )}
                        </div>
                      </div>
                      
                      {/* Saving indicator */}
                      {item.negotiable && saving > 0 && (
                        <div className="mt-2 flex items-center gap-2">
                          <span className="text-xs bg-red-100 text-red-700 px-2 py-1 rounded-full">
                            {l.saving}: {formatCurrency(saving, language)}
                          </span>
                        </div>
                      )}
                      
                      {/* Tip */}
                      <div className={`mt-3 p-3 rounded-lg ${
                        item.negotiable && saving > 0
                          ? "bg-green-50 border border-green-200"
                          : "bg-white border border-gray-100"
                      }`}>
                        <p className="text-xs text-gray-600">
                          💡 {getLocalizedTip(item, language)}
                        </p>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Negotiation Tips */}
          <div className={`rounded-2xl shadow-xl p-6 ${
            isBuy ? "bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200" : "bg-gradient-to-br from-orange-50 to-amber-50 border border-orange-200"
          }`}>
            <h3 className="font-bold text-gray-900 mb-4 flex items-center gap-2">
              🎯 {l.negotiationTips}
            </h3>
            <div className="space-y-3">
              <div className="flex items-start gap-3 p-3 bg-white rounded-xl">
                <span className="text-xl">1️⃣</span>
                <p className="text-sm text-gray-700">
                  {isBuy ? l.tip1Buy : l.tip1Sell}
                </p>
              </div>
              <div className="flex items-start gap-3 p-3 bg-white rounded-xl">
                <span className="text-xl">2️⃣</span>
                <p className="text-sm text-gray-700">
                  {isBuy ? l.tip2Buy : l.tip2Sell}
                </p>
              </div>
              <div className="flex items-start gap-3 p-3 bg-white rounded-xl">
                <span className="text-xl">3️⃣</span>
                <p className="text-sm text-gray-700">
                  {isBuy ? l.tip3Buy : l.tip3Sell}
                </p>
              </div>
            </div>
          </div>

          {/* Reset Button */}
          <div className="text-center">
            <button
              onClick={reset}
              className="px-6 py-3 bg-gray-100 text-gray-700 font-medium rounded-xl hover:bg-gray-200 transition"
            >
              {l.reset}
            </button>
          </div>
        </div>
      )}

      {/* Ad Banner */}
      <div className="text-center pt-4">
        {isBuy ? (
          <a
            href="https://www.partner-ads.com/dk/klikbanner.php?partnerid=56504&bannerid=60068"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block px-6 py-3 bg-blue-500 text-white font-semibold rounded-xl hover:bg-blue-600 transition"
          >
            🏠 {language === "zh" ? "比较房产保险 →" : language === "en" ? "Compare Home Insurance →" : "Sammenlign Boligforsikring →"}
          </a>
        ) : (
          <a
            href="https://www.partner-ads.com/dk/klikbanner.php?partnerid=56504&bannerid=71154"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-block px-6 py-3 bg-orange-500 text-white font-semibold rounded-xl hover:bg-orange-600 transition"
          >
            🏠 {language === "zh" ? "获取免费房产估价 →" : language === "en" ? "Get Free Valuation →" : "Få Gratis Vurdering →"}
          </a>
        )}
      </div>
    </div>
  );
}
