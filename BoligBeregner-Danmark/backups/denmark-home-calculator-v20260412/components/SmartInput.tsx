"use client";

import { useState, useCallback, useRef, useEffect } from "react";

interface SmartInputProps {
  type?: "text" | "number";
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  formatDisplay?: (value: string) => string;
  parseInput?: (display: string) => string;
  className?: string;
  inputClassName?: string;
  onFocusCustom?: () => void;
  onBlurCustom?: () => void;
  debounceMs?: number; // 防抖延迟（毫秒）
}

/**
 * SmartInput - 智能输入框组件
 * 
 * UX 设计原则：
 * - 当有默认值显示时，点击/focus 自动清空
 * - 用户输入时正常工作
 * - 如果用户清空并离开，保留空状态（不恢复默认值）
 * 
 * 这个设计让用户可以：
 * 1. 一眼看到示例值（placeholder/默认值）
 * 2. 点击时立即开始输入自己的值
 * 3. 不需要手动选中/删除默认值
 */
export default function SmartInput({
  type = "text",
  value,
  onChange,
  placeholder,
  formatDisplay,
  parseInput,
  className = "",
  inputClassName = "",
  onFocusCustom,
  onBlurCustom,
  debounceMs = 0, // 默认不防抖
}: SmartInputProps) {
  const [isFocused, setIsFocused] = useState(false);
  const [hasInteracted, setHasInteracted] = useState(false);
  const [inputValue, setInputValue] = useState(value); // 本地输入值
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null);

  // 同步外部 value 变化
  useEffect(() => {
    setInputValue(value);
  }, [value]);

  // 清理防抖定时器
  useEffect(() => {
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current);
      }
    };
  }, []);

  // 处理 focus - 清空方便用户输入
  const handleFocus = useCallback(() => {
    setIsFocused(true);
    if (!hasInteracted && placeholder) {
      onChange("");
    }
    onFocusCustom?.();
  }, [hasInteracted, placeholder, onChange, onFocusCustom]);

  // 处理 blur
  const handleBlur = useCallback(() => {
    setIsFocused(false);
    onBlurCustom?.();
  }, [onBlurCustom]);

  // 处理输入变化（带防抖）
  const handleChange = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    setHasInteracted(true);
    const rawValue = e.target.value;
    
    // 先更新本地显示值（立即响应）
    setInputValue(rawValue);
    
    // 清理之前的定时器
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current);
    }
    
    // 防抖处理 onChange
    if (debounceMs > 0) {
      debounceTimerRef.current = setTimeout(() => {
        if (parseInput) {
          const parsed = parseInput(rawValue);
          onChange(parsed);
        } else {
          onChange(rawValue);
        }
      }, debounceMs);
    } else {
      // 无防抖，立即触发
      if (parseInput) {
        const parsed = parseInput(rawValue);
        onChange(parsed);
      } else {
        onChange(rawValue);
      }
    }
  }, [parseInput, onChange, debounceMs]);

  // 显示值 - 使用本地 inputValue 保证即时响应
  const displayValue = (() => {
    if (formatDisplay && inputValue) {
      return formatDisplay(inputValue);
    }
    return inputValue;
  })();

  return (
    <div className={className}>
      <input
        type={type}
        value={displayValue}
        onChange={handleChange}
        onFocus={handleFocus}
        onBlur={handleBlur}
        placeholder={placeholder}
        className={inputClassName}
      />
    </div>
  );
}

// 数字输入专用版本 - 自动处理丹麦数字格式
interface SmartNumberInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
  inputClassName?: string;
  thousandSeparator?: string;
  debounceMs?: number; // 防抖延迟（毫秒）
}

export function SmartNumberInput({
  value,
  onChange,
  placeholder = "0",
  className = "",
  inputClassName = "",
  thousandSeparator = ".",
  debounceMs = 300, // 数字输入默认 300ms 防抖
}: SmartNumberInputProps) {
  const [isFocused, setIsFocused] = useState(false);

  // 格式化显示值（支持输入时实时格式化）
  const formatDisplay = (val: string, focused: boolean): string => {
    if (!val) return "";
    // 只格式化纯数字（不接受负号、小数点等）
    const digitsOnly = val.replace(/[^0-9]/g, "");
    if (!digitsOnly) return val;
    const num = parseInt(digitsOnly, 10);
    if (isNaN(num)) return val;
    // 输入时（focus）也格式化，不再区分 blur
    return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, thousandSeparator);
  };

  const parseInput = (display: string): string => {
    // 去掉所有千分位符号和非数字字符
    return display.replace(/\./g, "").replace(/[^0-9]/g, "");
  };

  return (
    <SmartInput
      type="text"
      value={value}
      onChange={onChange}
      placeholder={placeholder}
      formatDisplay={(val) => formatDisplay(val, isFocused)}
      parseInput={parseInput}
      className={className}
      inputClassName={inputClassName}
      onFocusCustom={() => setIsFocused(true)}
      onBlurCustom={() => setIsFocused(false)}
      debounceMs={debounceMs}
    />
  );
}
