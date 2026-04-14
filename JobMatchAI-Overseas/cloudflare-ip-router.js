/**
 * JobMatchAI IP Routing Worker
 * 
 * 功能：根据用户IP自动分流
 * - 中国IP → 中文版
 * - 其他IP → 英文版
 * 
 * 部署步骤：
 * 1. 打开 https://dash.cloudflare.com
 * 2. Workers & Pages → Create Application → Create Worker
 * 3. 名称：jobmatchai-ip-router
 * 4. 粘贴本文件代码，Save and Deploy
 * 
 * 路由设置（可选，用于测试）：
 * - 测试域名：test.job-match-ai.com/* → jobmatchai-ip-router
 * - 或者直接用 Workers 提供的 *.workers.dev 域名测试
 */

const ZH_HTML = 'index-zh.html';
const EN_HTML = 'index-en.html';

// 中国IP段前缀（主要覆盖）
const CHINA_IP_PREFIXES = [
  '36.', '42.', '58.', '59.', '60.', '61.',
  '101.', '103.', '106.', '110.', '111.', '112.',
  '113.', '114.', '115.', '116.', '117.', '118.',
  '119.', '120.', '121.', '122.', '123.', '124.',
  '125.', '140.', '175.', '180.', '182.', '183.',
  '202.', '203.', '210.', '211.', '218.', '220.',
  '221.', '222.', '223.', '116.', '117.', '118.',
  '119.', '120.', '121.', '122.', '123.', '124.',
  '125.', '175.', '180.', '182.', '183.', '202.'
];

function isChinaIP(ip) {
  if (!ip) return false;
  
  // 跳过本地IP
  if (ip === '127.0.0.1' || ip === 'localhost' || ip === '::1' || ip === '0.0.0.0') {
    return false;
  }
  
  // 检查IP前缀
  for (const prefix of CHINA_IP_PREFIXES) {
    if (ip.startsWith(prefix)) {
      return true;
    }
  }
  
  return false;
}

function getClientIP(request) {
  // 尝试从各种header获取真实IP
  const cfConnectingIP = request.headers.get('CF-Connecting-IP');
  if (cfConnectingIP) return cfConnectingIP;
  
  const xForwardedFor = request.headers.get('X-Forwarded-For');
  if (xForwardedFor) {
    return xForwardedFor.split(',')[0].trim();
  }
  
  const xRealIP = request.headers.get('X-Real-IP');
  if (xRealIP) return xRealIP;
  
  return null;
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    
    // 只处理根路径的GET请求
    if (url.pathname !== '/' || request.method !== 'GET') {
      // 其他请求直接返回404或原始响应
      return new Response('Not Found', { status: 404 });
    }
    
    // 获取客户端IP
    const clientIP = getClientIP(request);
    const isChina = isChinaIP(clientIP);
    const targetHTML = isChina ? ZH_HTML : EN_HTML;
    
    console.log(`IP: ${clientIP}, Region: ${isChina ? 'CN' : 'OTHER'}, Serving: ${targetHTML}`);
    
    // 获取对应的HTML内容
    // 这里需要返回对应的HTML内容
    // 由于Workers不能直接读取Cloudflare Pages的文件，我们需要把HTML内容内嵌或者fetch到正确的版本
    
    // 方案A：使用Stale Content（如果有缓存）
    // 方案B：内嵌HTML内容（文件会很大）
    // 方案C：重定向到对应版本
    
    // 推荐方案：重定向到对应版本
    const baseUrl = isChina 
      ? 'https://job-match-ai.com/index-zh.html'
      : 'https://job-match-ai.com/index-en.html';
    
    // 返回301重定向
    return Response.redirect(baseUrl, 301);
  }
};
