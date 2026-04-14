import { Redis } from '@upstash/redis';

const redis = new Redis({
  url: process.env.UPSTASH_KV_REST_API_URL,
  token: process.env.UPSTASH_KV_REST_API_TOKEN,
});

async function check() {
  try {
    const feedbacks = await redis.lrange('boligberegner:feedbacks', 0, 49);
    console.log('Found', feedbacks.length, 'feedbacks:');
    feedbacks.forEach((f, i) => {
      console.log(`\n[${i + 1}]`, typeof f, f);
    });
  } catch (err) {
    console.error('Error:', err);
  }
}

check();
