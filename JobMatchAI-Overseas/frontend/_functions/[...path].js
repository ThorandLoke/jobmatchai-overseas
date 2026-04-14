/**
 * JobMatchAI - Cloudflare Pages API Proxy
 * 
 * 作用：将 /api/*, /jobs/*, /upload-* 等 API 请求代理到 Render 后端
 * 原理：Cloudflare Pages Functions 拦截匹配路径的请求，Forward 到后端
 */

const BACKEND = 'https://jobmatchai-overseas.onrender.com';

// 需要代理的路径（不含前导斜杠，函数中 request.path 也是无斜杠格式）
const PROXY_PATTERNS = [
  'api/', 'jobs/', 'job/', 'upload-', 'extract/', 'generate-',
  'analyze-', 'fetch-', 'user-profile', 'tracker', 'payment',
  'session', 'cover-letter', 'templates', 'letter-evolution',
  'salary', 'industries', 'ats', 'auth', 'beta', 'health',
  'learning/', 'resumes/',
];

function shouldProxy(path) {
  // path 是无斜杠格式，如 "jobs/search"
  return PROXY_PATTERNS.some(p => path.startsWith(p));
}

function shouldProxy(pathname) {
  return API_PATHS.some(prefix => pathname.startsWith(prefix));
}

export async function onRequest({ request, env, next }) {
  const url = new URL(request.url);
  const pathname = url.pathname;

  // path 是无斜杠格式，如 "jobs/search" 或 "api/resume/polish"
  const pathname = new URL(request.url).pathname.slice(1); // 去掉前导斜杠
  if (!shouldProxy(pathname)) {
    return next();
  }

  // 构建后端 URL（path 无前导斜杠）
  const backendUrl = BACKEND + '/' + request.path + (url.search || '');

  try {
    // 转发请求到 Render 后端
    const response = await fetch(backendUrl, {
      method: request.method,
      headers: {
        ...Object.fromEntries(
          [...request.headers.entries()].filter(([key]) =>
            !['host', 'connection'].includes(key.toLowerCase())
          )
        ),
        'X-Forwarded-Host': url.host,
        'X-Forwarded-Proto': url.protocol.replace(':', ''),
      },
      body: ['GET', 'HEAD'].includes(request.method) ? undefined : request.body,
      redirect: 'manual',
    });

    // 构建响应，添加 CORS 头
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Requested-With',
      'Access-Control-Max-Age': '86400',
    };

    // 处理 CORS 预检
    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers: corsHeaders });
    }

    // 转发响应
    const newHeaders = new Headers(response.headers);
    Object.entries(corsHeaders).forEach(([k, v]) => newHeaders.set(k, v));

    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers: newHeaders,
    });

  } catch (err) {
    return new Response(JSON.stringify({ error: 'Backend unavailable', detail: err.message }), {
      status: 502,
      headers: {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': '*',
      },
    });
  }
}
