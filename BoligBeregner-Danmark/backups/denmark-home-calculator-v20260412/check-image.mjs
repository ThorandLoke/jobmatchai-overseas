import { Redis } from '@upstash/redis';

const redis = new Redis({
  url: process.env.UPSTASH_KV_REST_API_URL,
  token: process.env.UPSTASH_KV_REST_API_TOKEN,
});

async function check() {
  try {
    const feedbacks = await redis.lrange('boligberegner:feedbacks', 0, 49);
    console.log('Found', feedbacks.length, 'feedbacks:\n');
    
    feedbacks.forEach((f, i) => {
      const feedback = typeof f === 'string' ? JSON.parse(f) : f;
      console.log(`[${i + 1}] ID: ${feedback.id}`);
      console.log(`    时间: ${feedback.timestamp}`);
      console.log(`    内容: ${feedback.text}`);
      console.log(`    有图片: ${feedback.hasImage}`);
      console.log(`    图片数据: ${feedback.image ? '有' : '无'}`);
      if (feedback.image) {
        console.log(`    图片长度: ${feedback.image.length} 字符`);
        console.log(`    图片前100字符: ${feedback.image.substring(0, 100)}...`);
      }
      console.log('');
    });
  } catch (err) {
    console.error('Error:', err);
  }
}

check();
