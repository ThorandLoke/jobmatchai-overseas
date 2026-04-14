import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 在 Vercel 上使用标准部署以支持 API 路由
  // 本地开发使用静态导出
  ...(process.env.VERCEL ? {} : { output: 'export', distDir: 'dist' }),
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
