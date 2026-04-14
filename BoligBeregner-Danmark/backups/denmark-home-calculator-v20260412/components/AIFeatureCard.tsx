"use client";

import { useState, useEffect } from "react";
import { AI_FEATURES, runLocalAnalysis, runAIAnalysis } from "../lib/ai-advisor";
import FormulaTooltip, { AI_FEATURE_FORMULAS } from "./FormulaTooltip";
import type { PropertyContext, AIFeatureResult, Lang } from "../lib/ai-types";

interface AIFeatureCardProps {
  featureId: string;
  ctx: PropertyContext;
  lang: Lang;
  className?: string;
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

const FEATURE_COLORS: Record<string, { bg: string; border: string; hover: string; icon: string }> = {
  pricing:    { bg: "bg-blue-50", border: "border-blue-200", hover: "hover:border-blue-400", icon: "📊" },
  hidden:     { bg: "bg-amber-50", border: "border-amber-200", hover: "hover:border-amber-400", icon: "⚠️" },
  loan:       { bg: "bg-indigo-50", border: "border-indigo-200", hover: "hover:border-indigo-400", icon: "🏦" },
  roi:        { bg: "bg-green-50", border: "border-green-200", hover: "hover:border-green-400", icon: "📈" },
  renovation: { bg: "bg-purple-50", border: "border-purple-200", hover: "hover:border-purple-400", icon: "🔧" },
  market:     { bg: "bg-cyan-50", border: "border-cyan-200", hover: "hover:border-cyan-400", icon: "🌍" },
  compare:    { bg: "bg-pink-50", border: "border-pink-200", hover: "hover:border-pink-400", icon: "🔍" },
};

export default function AIFeatureCard({ featureId, ctx, lang, className = "" }: AIFeatureCardProps) {
  const [result, setResult] = useState<AIFeatureResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const meta = AI_FEATURES[featureId];
  const colors = FEATURE_COLORS[featureId] || FEATURE_COLORS.info;

  // 上下文变化时自动重新分析
  useEffect(() => {
    if (result) {
      setLoading(true);
      const timeout = setTimeout(async () => {
        try {
          const res = await runAIAnalysis(featureId, ctx);
          setResult(res);
        } catch {
          setResult(runLocalAnalysis(featureId, ctx));
        } finally {
          setLoading(false);
        }
      }, 300);
      return () => clearTimeout(timeout);
    }
  }, [ctx.region, ctx.size, ctx.price, ctx.transactionType, featureId, ctx, result]);

  const handleAnalyze = async () => {
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
  };

  return (
    <div className={`border-2 ${colors.border} ${colors.hover} rounded-2xl transition-all duration-300 ${className} ${expanded ? "shadow-lg" : "shadow-sm"}`}>
      {/* Card Header - 点击触发分析 */}
      <button
        className={`w-full p-5 ${result ? "bg-gradient-to-r from-white to-gray-50" : colors.bg} hover:shadow-md transition-all text-left`}
        onClick={handleAnalyze}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className={`text-3xl ${result ? "opacity-100" : "opacity-70"}`}>{result ? result.icon : meta.icon}</span>
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <p className="font-bold text-gray-900">{meta.title[lang]}</p>
                <FormulaTooltip formula={AI_FEATURE_FORMULAS[featureId]} lang={lang} icon="💡" />
              </div>
              <p className="text-sm text-gray-500 mt-0.5 line-clamp-2">{meta.desc[lang]}</p>
            </div>
          </div>
          <div className="flex-shrink-0">
            {loading ? (
              <div className="animate-spin w-6 h-6 border-2 border-purple-400 border-t-transparent rounded-full" />
            ) : result ? (
              <span className={`text-2xl ${expanded ? "rotate-180" : ""} transition-transform`}>▼</span>
            ) : (
              <span className="text-purple-600 font-medium text-sm">→</span>
            )}
          </div>
        </div>
        
        {/* 快速结果预览 */}
        {result && !expanded && (
          <div className={`mt-3 p-3 ${colors.bg} rounded-lg border ${colors.border}`}>
            <p className="text-sm font-medium text-gray-700 line-clamp-2">
              {result.icon} {result.summary}
            </p>
          </div>
        )}
      </button>

      {/* Expanded Result - 分析详情 */}
      {expanded && (
        <div className={`border-t ${colors.border} ${colors.bg} p-5 space-y-4`}>
          {loading ? (
            <div className="flex items-center justify-center gap-3 py-8">
              <div className="animate-spin w-8 h-8 border-3 border-purple-400 border-t-transparent rounded-full" />
              <span className="text-gray-600">
                {lang === "zh" ? "AI 分析中..." : lang === "en" ? "Analyzing..." : "Analyserer..."}
              </span>
            </div>
          ) : result ? (
            <>
              {/* Summary */}
              <div className={`p-4 rounded-xl border ${colors.border} bg-white/80`}>
                <p className="text-base font-semibold text-gray-900">
                  {result.icon} {result.summary}
                </p>
              </div>

              {/* Points */}
              <div className="space-y-2">
                {result.points.map((point, i) => (
                  <div
                    key={i}
                    className={`p-3 rounded-lg border text-sm flex items-start gap-3 ${TYPE_STYLES[point.type] || TYPE_STYLES.info}`}
                  >
                    <span className="flex-shrink-0 mt-0.5 text-base">{TYPE_ICONS[point.type]}</span>
                    <div className="flex-1 min-w-0">
                      <span className="text-gray-800">{point.text}</span>
                      {point.value && (
                        <span className="ml-2 font-bold text-xs px-2 py-0.5 bg-white/60 rounded">
                          {point.value}
                        </span>
                      )}
                    </div>
                  </div>
                ))}
              </div>

              {/* Confidence Badge */}
              <div className="text-center">
                <span className={`inline-block px-3 py-1 rounded-full text-xs font-medium ${
                  result.confidence === "high" ? "bg-green-100 text-green-700"
                    : result.confidence === "medium" ? "bg-yellow-100 text-yellow-700"
                    : "bg-gray-100 text-gray-600"
                }`}>
                  {result.confidence === "high"
                    ? (lang === "zh" ? "✅ 高可信度" : lang === "en" ? "✅ High confidence" : "✅ Høj sikkerhed")
                    : result.confidence === "medium"
                    ? (lang === "zh" ? "⚡ 中等可信度" : lang === "en" ? "⚡ Moderate confidence" : "⚡ Middel sikkerhed")
                    : (lang === "zh" ? "📝 低可信度" : lang === "en" ? "📝 Low confidence" : "📝 Lav sikkerhed")
                  }
                </span>
              </div>

              {/* Disclaimer */}
              {result.disclaimer && (
                <div className="mt-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
                  <p className="text-xs text-gray-600 leading-relaxed">
                    {result.disclaimer}
                  </p>
                </div>
              )}
            </>
          ) : null}
        </div>
      )}
    </div>
  );
}
