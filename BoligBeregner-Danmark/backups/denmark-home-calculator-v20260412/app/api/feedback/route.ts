import { NextRequest, NextResponse } from 'next/server';
import { Redis } from '@upstash/redis';

// 初始化 Upstash Redis 客户端
// Vercel 自动注入的环境变量：UPSTASH_KV_REST_API_URL 和 UPSTASH_KV_REST_API_TOKEN
const redis = new Redis({
  url: process.env.UPSTASH_KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL || '',
  token: process.env.UPSTASH_KV_REST_API_TOKEN || process.env.UPSTASH_REDIS_REST_TOKEN || '',
});

const FEEDBACK_KEY = 'boligberegner:feedbacks';

export async function POST(request: NextRequest) {
  try {
    // 检查 Redis 配置
    const redisUrl = process.env.UPSTASH_KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL;
    const redisToken = process.env.UPSTASH_KV_REST_API_TOKEN || process.env.UPSTASH_REDIS_REST_TOKEN;
    if (!redisUrl || !redisToken) {
      console.error('Redis configuration missing');
      return NextResponse.json(
        { error: 'Server configuration error' },
        { status: 500 }
      );
    }

    const body = await request.json();
    const { text, link, hasImage, image, language, timestamp } = body;

    // 验证必填字段
    if (!text || text.trim() === '') {
      return NextResponse.json(
        { error: 'Feedback text is required' },
        { status: 400 }
      );
    }

    // 创建反馈数据
    const feedback: Record<string, unknown> = {
      id: `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
      timestamp: timestamp || new Date().toISOString(),
      text: text.trim(),
      link: link || '',
      hasImage: hasImage || false,
      language: language || 'da'
    };
    
    // 如果有图片数据，存储图片（限制大小为500KB）
    if (image && typeof image === 'string' && image.startsWith('data:image')) {
      // Base64图片数据可能很大，限制存储大小
      const maxImageSize = 500 * 1024; // 500KB
      if (image.length <= maxImageSize) {
        feedback.image = image;
      } else {
        feedback.image = image.substring(0, maxImageSize); // 截断过大的图片
        feedback.imageTruncated = true;
      }
    }

    // 存储到 Redis（使用 list，保留最近 1000 条）
    await redis.lpush(FEEDBACK_KEY, JSON.stringify(feedback));
    await redis.ltrim(FEEDBACK_KEY, 0, 999); // 只保留最近 1000 条

    // 同时输出到控制台
    console.log('New feedback saved:', feedback.id);

    return NextResponse.json({
      success: true,
      message: 'Feedback received successfully',
      feedbackId: feedback.id
    });

  } catch (error) {
    console.error('Error processing feedback:', error);
    return NextResponse.json(
      { error: 'Failed to process feedback' },
      { status: 500 }
    );
  }
}

// GET 接口用于查看反馈（临时管理用）
export async function GET() {
  try {
    const redisUrl = process.env.UPSTASH_KV_REST_API_URL || process.env.UPSTASH_REDIS_REST_URL;
    const redisToken = process.env.UPSTASH_KV_REST_API_TOKEN || process.env.UPSTASH_REDIS_REST_TOKEN;
    if (!redisUrl || !redisToken) {
      return NextResponse.json(
        { error: 'Redis not configured' },
        { status: 500 }
      );
    }

    // 获取最近 50 条反馈
    const feedbacks = await redis.lrange(FEEDBACK_KEY, 0, 49);
    // Upstash Redis 客户端会自动解析 JSON，所以不需要再 JSON.parse
    const parsed = feedbacks.map(f => typeof f === 'string' ? JSON.parse(f) : f);

    return NextResponse.json({
      count: parsed.length,
      feedbacks: parsed
    });
  } catch (error) {
    console.error('Error fetching feedbacks:', error);
    return NextResponse.json(
      { error: 'Failed to fetch feedbacks' },
      { status: 500 }
    );
  }
}
