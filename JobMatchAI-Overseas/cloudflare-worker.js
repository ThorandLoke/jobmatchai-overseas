/**
 * JobMatchAI API Proxy Worker
 * 
 * 用途：将前端 API 请求代理到 Render 后端
 * 部署：Cloudflare Workers
 * 路由：api.job-match-ai.com/*
 * 
 * 部署步骤：
 * 1. 打开 https://dash.cloudflare.com
 * 2. Workers & Pages → Create Application → Create Worker
 * 3. 名称：jobmatchai-api-proxy
 * 4. 粘贴本文件代码
 * 5. Save and Deploy
 * 6. 添加路由：api.job-match-ai.com/* → jobmatchai-api-proxy
 * 
 * 验证：
 * curl -X POST https://api.job-match-ai.com/upload-resume
 */

const BACKEND = 'https://jobmatchai-overseas.onrender.com';

const API_PATHS = [
  '/upload-resume', '/upload-job-document', '/upload-document',
  '/api/', '/jobs/', '/job/', '/generate/', '/extract/',
  '/user-profile', '/tracker', '/payment', '/session',
  '/cover-letter', '/fetch-job', '/resumes/',
  '/beta/', '/templates/', '/letter-evolution/', '/salary/',
  '/industries/', '/ats/', '/auth/', '/health'
];

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const pathname = url.pathname;

    // 检查是否需要代理
    const shouldProxy = API_PATHS.some(p => pathname.startsWith(p));
    
    if (!shouldProxy) {
      return fetch(request);
    }

    // CORS 预检请求
    if (request.method === 'OPTIONS') {
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

    // 构建代理请求
    const backendUrl = BACKEND + pathname + url.search;
    const headers = new Headers(request.headers);
    headers.set('Host', 'jobmatchai-overseas.onrender.com');
    
    const cfIp = request.headers.get('CF-Connecting-IP');
    if (cfIp) headers.set('X-Forwarded-For', cfIp);

    try {
      let body = null;
      if (['POST', 'PUT', 'PATCH'].includes(request.method)) {
        body = await request.arrayBuffer();
      }

      const response = await fetch(backendUrl, {
        method: request.method,
        headers: headers,
        body: body,
      });

      const responseBody = await response.arrayBuffer();

      // 直接使用后端的响应头（包括 CORS 头）
      const responseHeaders = Object.fromEntries(response.headers.entries());

      return new Response(responseBody, {
        status: response.status,
        headers: responseHeaders,
      });
    } catch (error) {
      return new Response(JSON.stringify({ 
        error: 'Backend unavailable', 
        details: error.message 
      }), {
        status: 503,
        headers: { 
          'Content-Type': 'application/json'
        }
      });
    }
  }
};
