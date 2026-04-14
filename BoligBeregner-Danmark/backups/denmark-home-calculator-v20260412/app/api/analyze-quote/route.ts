import { NextRequest, NextResponse } from "next/server";
import { spawn } from "child_process";
import path from "path";
import fs from "fs";

// 丹麦中介常见费用关键词映射
const FEE_KEYWORDS: Record<string, { patterns: string[]; category: string; negotiable: boolean; benchmark: number }> = {
  mæglerhonorar: {
    patterns: ["mæglerhonorar", "mægler", "kommission", "provisions"],
    category: "中介费",
    negotiable: true,
    benchmark: 35000,
  },
  markedsføring: {
    patterns: ["markedsføringsomkostninger", "marketing", "annonce", "foto", "fotopakke"],
    category: "营销费",
    negotiable: true,
    benchmark: 15000,
  },
  salgsmateriale: {
    patterns: ["salgsmateriale", "opmåling", "teknisk rap"],
    category: "销售材料",
    negotiable: true,
    benchmark: 5000,
  },
  tinglysning: {
    patterns: ["tinglysning", "tinglysningsafgift"],
    category: "登记费",
    negotiable: false,
    benchmark: 18000,
  },
  ejendomsdatarapport: {
    patterns: ["ejendomsdatarapport", "e-dokument"],
    category: "房产数据报告",
    negotiable: false,
    benchmark: 1500,
  },
};

interface ExtractedFee {
  name: string;
  amount: number;
  category: string;
  negotiable: boolean;
  benchmark: number;
  savings: number;
}

interface AnalysisResult {
  success: boolean;
  fees: ExtractedFee[];
  total: number;
  negotiableTotal: number;
  potentialSavings: number;
  propertyPrice: number | null;
  netProceeds: number | null;
  suggestions: Array<{ type: "tip" | "warning"; text: string }>;
  rawText?: string;
  error?: string;
}

// 解析丹麦数字格式
function parseDanishNumber(text: string): number {
  // 丹麦格式：1.234.567,50 → 1234567
  const cleaned = text
    .replace(/\s/g, "")
    .replace(/\./g, "")
    .replace(",", ".");
  return parseFloat(cleaned) || 0;
}

// 提取 PDF 中的费用项
function extractFees(text: string): ExtractedFee[] {
  const fees: ExtractedFee[] = [];
  const lines = text.split("\n");
  
  // EDC Salgsbudget 格式：查找 "Udgifter i alt" 和后面的金额
  let inUdgifterSection = false;
  let lastLabel = "";
  
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].toLowerCase();
    const originalLine = lines[i];
    
    // 标记进入费用区域
    if (line.includes("udgifter i alt") || line.includes("øvrige salgsomkostninger")) {
      inUdgifterSection = true;
    }
    
    // 检测费用标签
    if (inUdgifterSection) {
      // EDC 格式中的费用项（不带 kr.）
      const feePatterns: Record<string, { category: string; negotiable: boolean; benchmark: number }> = {
        "ejerskifteforsikring": { category: "产权保险", negotiable: false, benchmark: 7500 },
        "tilstandsrapport": { category: "房屋状况报告", negotiable: false, benchmark: 12000 },
        "sælgeransvarsforsikring": { category: "卖家责任险", negotiable: false, benchmark: 2000 },
        "digitalt skøde": { category: "数字产权登记", negotiable: false, benchmark: 6000 },
        "refusionsopgørelse": { category: "结算调整", negotiable: false, benchmark: 2000 },
        "deponering": { category: "托管费", negotiable: false, benchmark: 5000 },
        "indfrielse": { category: "贷款清偿", negotiable: false, benchmark: 0 },
        "mæglerhonorar": { category: "中介费", negotiable: true, benchmark: 35000 },
        "salær": { category: "中介费", negotiable: true, benchmark: 35000 },
        "markedsføring": { category: "营销费", negotiable: true, benchmark: 15000 },
      };
      
      for (const [pattern, config] of Object.entries(feePatterns)) {
        if (line.includes(pattern)) {
          lastLabel = config.category;
          // 在接下来的行中找金额
          for (let j = i + 1; j < Math.min(i + 3, lines.length); j++) {
            const numMatch = lines[j].match(/(\d{1,3}\.\d{3},\d{2})/);
            if (numMatch) {
              const amount = parseDanishNumber(numMatch[1]);
              if (amount > 100 && amount < 500000) {
                const existing = fees.find((f) => f.category === config.category);
                if (!existing) {
                  fees.push({
                    name: config.category,
                    amount,
                    category: config.category,
                    negotiable: config.negotiable,
                    benchmark: config.benchmark,
                    savings: config.benchmark > 0 ? Math.max(0, amount - config.benchmark) : 0,
                  });
                }
              }
              break;
            }
          }
          break;
        }
      }
    }
  }
  
  // 如果没找到详细费用，尝试提取总费用
  if (fees.length === 0) {
    // 查找 "Øvrige salgsomkostninger i alt" 后面的总额
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].toLowerCase().includes("øvrige salgsomkostninger i alt")) {
        for (let j = i; j < Math.min(i + 5, lines.length); j++) {
          const numMatch = lines[j].match(/(\d{1,3}\.\d{3},\d{2})/);
          if (numMatch) {
            const amount = parseDanishNumber(numMatch[1]);
            if (amount > 10000) {
              fees.push({
                name: "其他销售费用",
                amount,
                category: "其他销售费用",
                negotiable: false,
                benchmark: 0,
                savings: 0,
              });
              break;
            }
          }
        }
        break;
      }
    }
  }

  return fees;
}

// 估算房产总价（从报价中推断）
function estimatePropertyPrice(text: string): number | null {
  // 寻找总价相关关键词
  // Salgsbudget 格式：Kontant betales + Indtægter i alt
  const lines = text.split("\n");
  
  // 匹配 "Indtægter i alt" 或 "Kontant betales" 后面的金额
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].toLowerCase();
    if (line.includes("indtægter i alt") || line.includes("kontant betales")) {
      // 在接下来的几行中找金额 (丹麦格式: 295.000,00)
      for (let j = i + 1; j < Math.min(i + 5, lines.length); j++) {
        const numMatch = lines[j].match(/(\d{1,3}\.\d{3},\d{2})/);
        if (numMatch) {
          const amount = parseDanishNumber(numMatch[1]);
          // 金额应该在 50000 - 10000000 之间才合理
          if (amount > 50000 && amount < 10000000) {
            return amount;
          }
        }
      }
    }
  }
  
  // 备选：在 "1.1. Indtægter" 部分直接找大额数字
  const bigAmountMatch = text.match(/Indtægter[\s\S]{0,500}?(\d{1,3}\.\d{3},\d{2})/);
  if (bigAmountMatch) {
    const amount = parseDanishNumber(bigAmountMatch[1]);
    if (amount > 50000 && amount < 10000000) {
      return amount;
    }
  }

  return null;
}

// 提取净额（Salgsprovenu / Rådighedsbeløb）
function extractNetProceeds(text: string): number | null {
  const lines = text.split("\n");
  
  // Salgsbudget 格式：查找 "Budgetteret rådighedsbeløb" 后面的金额
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].toLowerCase();
    if (line.includes("rådighedsbeløb") || line.includes("salgsprovenu")) {
      // 在接下来的几行中找金额
      for (let j = i + 1; j < Math.min(i + 5, lines.length); j++) {
        const numMatch = lines[j].match(/(\d{1,3}\.\d{3},\d{2})/);
        if (numMatch) {
          const amount = parseDanishNumber(numMatch[1]);
          // 净额通常是正数且小于房价
          if (amount > 0 && amount < 5000000) {
            return amount;
          }
        }
      }
    }
  }
  
  // 备选：匹配明确标注的净额
  const patterns = [
    /salgs?pro?venu?[:\s]*(\d{1,3}[.,]\d{3}[.,]\d{3})/i,
    /netto prov?enu?[:\s]*(\d{1,3}[.,]\d{3}[.,]\d{3})/i,
  ];

  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) {
      return parseDanishNumber(match[1]);
    }
  }

  return null;
}

// 生成建议
function generateSuggestions(fees: ExtractedFee[], lang: string): Array<{ type: "tip" | "warning"; text: string }> {
  const suggestions: Array<{ type: "tip" | "warning"; text: string }> = [];

  // 丹麦语建议
  if (lang === "da" || lang === "zh") {
    const highMægler = fees.find((f) => f.category === "中介费" && f.savings > 5000);
    if (highMægler) {
      suggestions.push({
        type: "warning",
        text: lang === "da"
          ? `Mæglerhonoraret på ${highMægler.amount.toLocaleString("da-DK")} kr virker højt. Forhandl om 10-15% rabat.`
          : `中介费 ${highMægler.amount.toLocaleString()} kr 偏高，可以尝试谈判 10-15% 的折扣。`,
      });
    }

    const highMarketing = fees.find((f) => f.category === "营销费" && f.savings > 3000);
    if (highMarketing) {
      suggestions.push({
        type: "tip",
        text: lang === "da"
          ? `Markedsføringsomkostninger på ${highMarketing.amount.toLocaleString("da-DK")} kr kan ofte reduceres.`
          : `营销费用 ${highMarketing.amount.toLocaleString()} kr 通常可以协商降低。`,
      });
    }
  } else {
    // 英语建议
    const highMægler = fees.find((f) => f.category === "中介费" && f.savings > 5000);
    if (highMægler) {
      suggestions.push({
        type: "warning",
        text: `Agent fee of DKK ${highMægler.amount.toLocaleString()} seems high. Negotiate for 10-15% discount.`,
      });
    }
  }

  return suggestions;
}

export async function POST(request: NextRequest) {
  try {
    const formData = await request.formData();
    const file = formData.get("file") as File | null;
    const lang = (formData.get("lang") as string) || "en";

    if (!file) {
      return NextResponse.json(
        { success: false, error: "No file uploaded" },
        { status: 400 }
      );
    }

    // 验证文件类型
    if (!file.name.toLowerCase().endsWith(".pdf")) {
      return NextResponse.json(
        { success: false, error: "Only PDF files are supported" },
        { status: 400 }
      );
    }

    // 读取文件
    const bytes = await file.arrayBuffer();
    const buffer = Buffer.from(bytes);

    // 提取文本
    let text = "";
    let isScanned = false;

    try {
      // 使用 Python pdfminer 提取文本（更可靠）
      const scriptPath = path.join(process.cwd(), "scripts", "extract-pdf.py");
      
      // 临时写入 PDF 文件供 Python 脚本读取
      const tmpPath = `/tmp/pdf-analyze-${Date.now()}.pdf`;
      fs.writeFileSync(tmpPath, buffer);
      
      text = await new Promise<string>((resolve, reject) => {
        const proc = spawn("python3", [scriptPath, tmpPath], {
          cwd: process.cwd(),
        });
        
        let stdout = "";
        let stderr = "";
        
        proc.stdout.on("data", (data) => { stdout += data.toString(); });
        proc.stderr.on("data", (data) => { stderr += data.toString(); });
        
        proc.on("close", (code) => {
          // 清理临时文件
          try { fs.unlinkSync(tmpPath); } catch {}
          
          if (code === 0) {
            try {
              const result = JSON.parse(stdout);
              if (result.success) {
                resolve(result.text);
              } else {
                reject(new Error(result.error || "PDF extraction failed"));
              }
            } catch {
              reject(new Error("Invalid Python output"));
            }
          } else {
            reject(new Error(stderr || "Python script failed"));
          }
        });
      });
    } catch (e: any) {
      console.error("PDF parse error:", e?.message || e);
      return NextResponse.json({
        success: false,
        error: lang === "da"
          ? "Kunne ikke udtrække tekst fra PDF. Prøv et andet format."
          : lang === "zh"
          ? "无法从 PDF 提取文字，请尝试其他 PDF 文件。"
          : "Could not extract text from PDF. Try a different file.",
      });
    }

    // 提取费用
    const fees = extractFees(text);
    const total = fees.reduce((sum, f) => sum + f.amount, 0);
    const negotiableTotal = fees.filter((f) => f.negotiable).reduce((sum, f) => sum + f.amount, 0);
    const potentialSavings = fees.reduce((sum, f) => sum + f.savings, 0);
    const propertyPrice = estimatePropertyPrice(text);
    const netProceeds = extractNetProceeds(text);
    const suggestions = generateSuggestions(fees, lang);

    const result: AnalysisResult = {
      success: true,
      fees,
      total,
      negotiableTotal,
      potentialSavings,
      propertyPrice,
      netProceeds,
      suggestions,
      rawText: text.substring(0, 1000), // 只返回前1000字符用于调试
    };

    return NextResponse.json(result);
  } catch (error) {
    console.error("Quote analysis error:", error);
    return NextResponse.json({
      success: false,
      error: "Analysis failed",
    }, { status: 500 });
  }
}
