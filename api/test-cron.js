// 驗證假設：Vercel Cron 需要 Next.js App Router 格式
export const dynamic = 'force-dynamic';

export async function GET(request) {
  const timestamp = new Date().toISOString();

  console.log('='.repeat(80));
  console.log('[TEST CRON - App Router] Executed at:', timestamp);
  console.log('[TEST CRON] x-vercel-cron header:', request.headers.get('x-vercel-cron'));
  console.log('='.repeat(80));

  // 使用 Response 而不是 res.json()
  return new Response(JSON.stringify({
    success: true,
    timestamp,
    message: 'Cron executed with App Router format',
    isVercelCron: !!request.headers.get('x-vercel-cron')
  }), {
    status: 200,
    headers: {
      'Content-Type': 'application/json'
    }
  });
}
