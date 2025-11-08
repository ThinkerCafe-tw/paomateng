// 驗證假設：Vercel Cron 只執行內部邏輯，不發外部 request
export const dynamic = 'force-dynamic';

export default async function handler(req, res) {
  const timestamp = new Date().toISOString();

  console.log('='.repeat(80));
  console.log('[TEST CRON] Executed at:', timestamp);
  console.log('[TEST CRON] x-vercel-cron header:', req.headers['x-vercel-cron']);
  console.log('='.repeat(80));

  // 不要發任何外部 request，只做內部邏輯
  return res.status(200).json({
    success: true,
    timestamp,
    message: 'Cron executed successfully (no external requests)',
    isVercelCron: !!req.headers['x-vercel-cron']
  });
}
