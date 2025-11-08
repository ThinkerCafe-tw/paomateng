// 超級簡單的測試 cron - 只記錄時間
export const dynamic = 'force-dynamic';

export default async function handler(req, res) {
  const timestamp = new Date().toISOString();

  console.log('='.repeat(50));
  console.log(`[TEST CRON] Executed at: ${timestamp}`);
  console.log(`[TEST CRON] Headers:`, JSON.stringify(req.headers, null, 2));
  console.log(`[TEST CRON] Method:`, req.method);
  console.log('='.repeat(50));

  return res.status(200).json({
    success: true,
    message: 'Test cron executed successfully',
    timestamp,
    headers: {
      'x-vercel-cron': req.headers['x-vercel-cron'],
      'user-agent': req.headers['user-agent']
    }
  });
}
