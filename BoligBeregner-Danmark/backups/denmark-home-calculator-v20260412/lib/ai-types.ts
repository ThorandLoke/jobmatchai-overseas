// ==================== AI 智能分析 类型定义 ====================

export type Lang = "da" | "en" | "zh";

export interface PropertyContext {
  price: number;
  region?: string;
  size?: number;                // 面积 m²
  yearBuilt?: number;           // 建造年份
  energyLabel?: string;         // 能源等级 A-G
  transactionType: "buy" | "sell";
  downPaymentPercent?: number;
  loanRate?: number;
  loanYears?: number;
  renovations?: string[];       // 已选改造项目
  lang: Lang;
  tabType?: "buy" | "sell" | "renovate" | "market" | "pdf"; // 当前tab类型
}

export interface AIFeatureResult {
  title: string;
  icon: string;
  summary: string;              // 1-2 句核心结论
  points: AIPoint[];
  confidence?: "high" | "medium" | "low";
  loading?: boolean;
  error?: string;
  disclaimer?: string;          // 数据来源免责声明
}

export interface AIPoint {
  type: "tip" | "warning" | "info" | "positive" | "negative";
  text: string;
  value?: string;               // 可选的量化值，例如 "DKK 45.000"
}

export type AIFeatureType =
  | "pricing"       // 智能定价建议
  | "hidden_costs"  // 隐藏费用预警
  | "loan_opt"      // 贷款优化方案
  | "roi"           // 投资回报预测
  | "renovation"    // 装修优先级建议
  | "market"        // 市场趋势分析
  | "compare";      // 比价助手
