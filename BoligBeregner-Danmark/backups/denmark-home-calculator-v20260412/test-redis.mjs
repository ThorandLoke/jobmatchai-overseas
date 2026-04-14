import { Redis } from '@upstash/redis';

const redis = new Redis({
  url: process.env.UPSTASH_KV_REST_API_URL,
  token: process.env.UPSTASH_KV_REST_API_TOKEN,
});

async function test() {
  try {
    await redis.ping();
    console.log('✅ Redis connection successful');
    
    // Test write
    await redis.lpush('test:feedback', JSON.stringify({ test: true, time: Date.now() }));
    console.log('✅ Write successful');
    
    // Test read
    const data = await redis.lrange('test:feedback', 0, 0);
    console.log('✅ Read successful:', data);
    
    // Cleanup
    await redis.del('test:feedback');
    console.log('✅ Cleanup successful');
  } catch (err) {
    console.error('❌ Error:', err.message);
  }
}

test();
