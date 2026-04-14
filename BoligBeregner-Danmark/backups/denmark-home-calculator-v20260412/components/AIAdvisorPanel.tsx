"use client";

import { useState, useCallback, useEffect } from "react";
import { AI_FEATURES, runLocalAnalysis, runAIAnalysis } from "../lib/ai-advisor";
import FormulaTooltip, { AI_FEATURE_FORMULAS } from "./FormulaTooltip";
import type { PropertyContext, AIFeatureResult, Lang } from "../lib/ai-types";

interface AIAdvisorPanelProps {
  ctx: PropertyContext;
  lang: Lang;
}

const TYPE_STYLES: Record<string, string> = {
  tip:      "bg-green-50  border-green-200  text-green-800",
  warning:  "bg-yellow-50 border-yellow-200 text-yellow-800",
  info:     "bg-blue-50   border-blue-200   text-blue-700",
  positive: "bg-emerald-50 border-emerald-200 text-emerald-800",
  negative: "bg-red-50    border-red-200    text-red-800",
};

const TYPE_ICONS: Record<string, string> = {
  tip: "💡", warning: "⚠️", info: "ℹ️", positive: "✅", negative: "❌",
};

const CONFIDENCE_BADGE: Record<string, { text: Record<Lang, string>; color: string }> = {
  high:   { text: { da: "Høj sikkerhed", en: "High confidence", zh: "高可信度" }, color: "bg-green-100 text-green-700" },
  medium: { text: { da: "Middel sikkerhed", en: "Moderate confidence", zh: "中等可信度" }, color: "bg-yellow-100 text-yellow-700" },
  low:    { text: { da: "Lav sikkerhed", en: "Low confidence", zh: "低可信度（需更多信息）" }, color: "bg-gray-100 text-gray-600" },
};

function FeatureCard({ featureId, ctx, lang }: { featureId: string; ctx: PropertyContext; lang: Lang }) {
  const [result, setResult] = useState<AIFeatureResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);

  // 上下文变化时自动重新分析
  useEffect(() => {
    if (result) {
      // 自动用新参数重新分析
      setLoading(true);
      setExpanded(true);
      const timeout = setTimeout(async () => {
        try {
          const res = await runAIAnalysis(featureId, ctx);
          setResult(res);
        } catch {
          setResult(runLocalAnalysis(featureId, ctx));
        } finally {
          setLoading(false);
        }
      }, 300); // 防抖 300ms
      return () => clearTimeout(timeout);
    }
  }, [ctx.region, ctx.size, ctx.price, ctx.transactionType, featureId, ctx]);

  const meta = AI_FEATURES[featureId];

  const handleAnalyze = useCallback(async () => {
    if (result) {
      setExpanded(!expanded);
      return;
    }
    setLoading(true);
    setExpanded(true);
    try {
      const res = await runAIAnalysis(featureId, ctx);
      setResult(res);
    } catch {
      setResult(runLocalAnalysis(featureId, ctx));
    } finally {
      setLoading(false);
    }
  }, [featureId, ctx, result, expanded]);

  const confidence = result?.confidence || "medium";
  const badge = CONFIDENCE_BADGE[confidence];

  return (
    <div className={`border rounded-xl overflow-hidden transition-all duration-200 ${expanded ? "border-purple-300 shadow-md" : "border-gray-200 hover:border-purple-200 hover:shadow-sm"}`}>
      {/* Card Header */}
      <button
        className="w-full flex items-center justify-between p-4 bg-white hover:bg-purple-50 transition text-left"
        onClick={handleAnalyze}
      >
        <div className="flex items-center gap-3">
          <span className="text-2xl">{meta.icon}</span>
          <div className="flex items-center gap-2">
            <p className="font-semibold text-gray-900 text-sm">{meta.title[lang]}</p>
            {AI_FEATURE_FORMULAS[featureId] && (
              <FormulaTooltip 
                formula={AI_FEATURE_FORMULAS[featureId]} 
                lang={lang}
                icon="💡"
              />
            )}
          </div>
        </div>
        <div className="flex items-center gap-2">
          {result && (
            <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${badge.color}`}>
              {badge.text[lang]}
            </span>
          )}
          <span className="text-gray-400 text-sm ml-1">
            {loading ? "⏳" : expanded ? "▲" : "▼"}
          </span>
        </div>
      </button>

      {/* Expanded Result */}
      {expanded && (
        <div className="border-t border-gray-100 bg-gradient-to-b from-purple-50 to-white p-4">
          {loading ? (
            <div className="flex items-center justify-center gap-2 py-6 text-gray-500">
              <div className="animate-spin w-5 h-5 border-2 border-purple-400 border-t-transparent rounded-full" />
              <span className="text-sm">
                {lang === "zh" ? "AI 分析中..." : lang === "en" ? "Analyzing..." : "Analyserer..."}
              </span>
            </div>
          ) : result ? (
            <>
              {/* Summary */}
              <p className="text-sm font-medium text-purple-900 mb-3 p-3 bg-purple-100 rounded-lg">
                {result.icon} {result.summary}
              </p>
              {/* Points */}
              <div className="space-y-2">
                {result.points.map((point, i) => (
                  <div
                    key={i}
                    className={`p-3 rounded-lg border text-sm flex items-start gap-2 ${TYPE_STYLES[point.type] || TYPE_STYLES.info}`}
                  >
                    <span className="flex-shrink-0 mt-0.5">{TYPE_ICONS[point.type]}</span>
                    <div className="flex-1">
                      <span>{point.text}</span>
                      {point.value && (
                        <span className="ml-2 font-bold text-xs px-1.5 py-0.5 bg-white/60 rounded">
                          {point.value}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </>
          ) : null}
        </div>
      )}
    </div>
  );
}

export default function AIAdvisorPanel({ ctx, lang }: AIAdvisorPanelProps) {
  const [showAll, setShowAll] = useState(false);

  const TITLE: Record<Lang, string> = {
    da: "🤖 AI Rådgiver",
    en: "🤖 AI Advisor",
    zh: "🤖 AI 智能顾问",
  };
  const SUBTITLE: Record<Lang, string> = {
    da: "7 intelligente analyser til at støtte din boligbeslutning",
    en: "7 smart analyses to support your property decision",
    zh: "7 项智能分析，辅助您的房产决策",
  };
  const SUBTITLE_RENOVATE: Record<Lang, string> = {
    da: "AI-analyse af renoveringsprioritet og investeringsafkast",
    en: "AI renovation priority and ROI analysis",
    zh: "AI 装修优先级和投资回报分析",
  };
  const SHOW_MORE: Record<Lang, string> = {
    da: "Vis alle analyser ▼",
    en: "Show all analyses ▼",
    zh: "展开全部分析 ▼",
  };
  const SHOW_LESS: Record<Lang, string> = {
    da: "Vis færre ▲",
    en: "Show fewer ▲",
    zh: "收起 ▲",
  };

  // 根据tab类型选择要显示的AI功能
  const getFeaturesForTab = () => {
    if (ctx.tabType === "renovate") {
      return ["renovation"]; // 房屋改造只显示装修优先级分析
    }
    return Object.keys(AI_FEATURES); // 其他tab显示所有功能
  };

  const FEATURES_ALL = getFeaturesForTab();
  const visibleFeatures = showAll ? FEATURES_ALL : FEATURES_ALL.slice(0, FEATURES_ALL.length);

  return (
    <div className="mt-8 bg-white rounded-2xl shadow-lg overflow-hidden">
      {/* Panel Header */}
      <div className="bg-gradient-to-r from-purple-700 to-indigo-700 px-6 py-4">
        <h2 className="text-white font-bold text-lg">{TITLE[lang]}</h2>
        <p className="text-purple-200 text-sm mt-0.5">
          {ctx.tabType === "renovate" ? SUBTITLE_RENOVATE[lang] : SUBTITLE[lang]}
        </p>
      </div>

      {/* No price warning */}
      {!ctx.price && ctx.tabType !== "renovate" ? (
        <div className="p-6 text-center text-gray-400">
          <p className="text-4xl mb-2">🏠</p>
          <p className="text-sm">
            {lang === "zh" ? "请先输入房产价格以启用 AI 分析"
              : lang === "en" ? "Enter a property price to enable AI analysis"
              : "Indtast en ejendomspris for at aktivere AI-analyse"}
          </p>
        </div>
      ) : ctx.tabType === "renovate" && !ctx.size ? (
        <div className="p-6 text-center text-gray-400">
          <p className="text-4xl mb-2">🏠</p>
          <p className="text-sm">
            {lang === "zh" ? "请先输入房屋面积以启用 AI 分析"
              : lang === "en" ? "Enter house size to enable AI analysis"
              : "Indtast husstørrelse for at aktivere AI-analyse"}
          </p>
        </div>
      ) : (
        <div className="p-4">
          <div className="grid gap-3">
            {visibleFeatures.map(fId => (
              <FeatureCard key={fId} featureId={fId} ctx={ctx} lang={lang} />
            ))}
          </div>

          {FEATURES_ALL.length > 4 && ctx.tabType !== "renovate" && (
            <button
              onClick={() => setShowAll(!showAll)}
              className="mt-3 w-full py-2 text-sm text-purple-600 hover:text-purple-800 font-medium transition"
            >
              {showAll ? SHOW_LESS[lang] : SHOW_MORE[lang]}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
