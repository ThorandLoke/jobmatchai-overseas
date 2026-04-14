#!/bin/bash
# JobMatchAI Frontend 部署脚本
# 用法: ./deploy-frontend.sh

PROJECT_DIR="/Users/weili/WorkBuddy/Claw/JobMatchAI-Overseas"
DEPLOY_DIR="/tmp/jobmatchai-deploy-$(date +%Y%m%d-%H%M%S)"
BACKEND_URL="https://jobmatchai-overseas.onrender.com"

echo "📦 正在准备部署包..."

# 创建临时目录
mkdir -p "$DEPLOY_DIR/frontend"
mkdir -p "$DEPLOY_DIR/functions"

# 1. 根目录语言跳转页
cat > "$DEPLOY_DIR/index.html" << 'HTML'
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="JobMatchAI - AI智能求职助手">
    <title>JobMatchAI - 智能求职助手</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1e3a5f 0%, #2d5a87 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            color: #fff;
            margin: 0;
        }
        .loading { text-align: center; }
        .spinner {
            width: 50px; height: 50px;
            border: 4px solid rgba(255,255,255,0.3);
            border-top-color: #fff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin { to { transform: rotate(360deg); } }
        .loading h2 { font-weight: 400; opacity: 0.9; }
        .loading p { opacity: 0.6; font-size: 14px; margin-top: 10px; }
    </style>
</head>
<body>
    <div class="loading">
        <div class="spinner"></div>
        <h2>正在加载 JobMatchAI...</h2>
        <p id="status">检测语言环境</p>
    </div>
    <script>
        (function() {
            const browserLang = navigator.language || navigator.userLanguage || 'en';
            const lang = browserLang.toLowerCase();
            const isChinese = lang.startsWith('zh');
            const targetPage = isChinese ? 'frontend/index-zh.html' : 'frontend/index-en-final.html';
            document.getElementById('status').textContent = 'Detected: ' + browserLang + ' → Loading...';
            console.log('Language:', browserLang, '->', targetPage);
            setTimeout(function() { window.location.href = targetPage; }, 300);
        })();
    </script>
</body>
</html>
HTML

# 2. 创建 Cloudflare Pages Function（API 代理）
cat > "$DEPLOY_DIR/functions/[path].js" << 'FUNCJS'
export async function onRequest(context) {
  const url = new URL(context.request.url);
  const pathname = url.pathname;
  
  // 处理 CORS 预检请求
  if (context.request.method === 'OPTIONS') {
    return new Response(null, {
      status: 204,
      headers: {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization',
        'Access-Control-Max-Age': '86400',
      }
    });
  }
  
  // 需要代理的 API 路径
  const apiPaths = [
    '/api/', '/upload', '/upload-resume', '/upload-job-document',
    '/analyze', '/jobs/', '/job/', '/generate', '/generate-cover-letter',
    '/user-profile', '/extract', '/tracker', '/payment',
    '/session', '/cover-letter', '/fetch-job', '/resumes/',
    '/beta/', '/templates/', '/letter-evolution/', '/salary/',
    '/industries/', '/ats/', '/auth/', '/health'
  ];
  
  const shouldProxy = apiPaths.some(p => pathname.startsWith(p));
  
  if (shouldProxy) {
    const backendUrl = 'https://jobmatchai-overseas.onrender.com' + pathname + url.search;
    const headers = new Headers(context.request.headers);
    headers.set('Host', 'jobmatchai-overseas.onrender.com');
    
    const cfIp = context.request.headers.get('CF-Connecting-IP');
    if (cfIp) headers.set('X-Forwarded-For', cfIp);
    
    try {
      let body = undefined;
      if (['POST', 'PUT', 'PATCH'].includes(context.request.method)) {
        body = await context.request.arrayBuffer();
      }
      
      const response = await fetch(backendUrl, {
        method: context.request.method,
        headers: headers,
        body: body,
      });
      
      const responseBody = await response.arrayBuffer();
      
      return new Response(responseBody, {
        status: response.status,
        headers: {
          ...Object.fromEntries(response.headers.entries()),
          'Access-Control-Allow-Origin': '*',
        }
      });
    } catch (error) {
      return new Response(JSON.stringify({ error: 'Backend unavailable', details: error.message }), {
        status: 503,
        headers: { 'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*' }
      });
    }
  }
  
  return context.next();
}
FUNCJS

echo "✅ API 代理函数已创建"

# 3. 复制最新前端文件
cp "$PROJECT_DIR/frontend/index-zh.html" "$DEPLOY_DIR/frontend/"
cp "$PROJECT_DIR/frontend/index-en-final.html" "$DEPLOY_DIR/frontend/"

# 3. 打包
ZIP_FILE="/tmp/jobmatchai-deploy.zip"
cd "$DEPLOY_DIR" && zip -r "$ZIP_FILE" . -x "*.DS_Store"

echo ""
echo "✅ 部署包已准备好: $ZIP_FILE"
echo ""
echo "📁 文件结构:"
find "$DEPLOY_DIR" -type f | sed "s|$DEPLOY_DIR|  |"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "下一步："
echo "1. 打开 Cloudflare Dashboard → Pages → jobmatchai-4y1"
echo "2. 点击 Create deployment → Upload assets"
echo "3. 上传文件: $ZIP_FILE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
