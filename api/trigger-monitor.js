/**
 * Vercel Serverless Function - 觸發 GitHub Actions workflow
 * 每 5 分鐘由 Vercel Cron 自動執行
 *
 * 用途: 繞過 GitHub Actions 免費版的 cron 限流
 * 成本: Vercel 免費版支援 (100GB-hours/月)
 */

export default async function handler(req, res) {
  // 驗證來源
  // Vercel Cron 會自動帶 x-vercel-cron header
  const isVercelCron = req.headers['x-vercel-cron'];
  const authHeader = req.headers.authorization;

  // 允許兩種驗證方式：
  // 1. Vercel Cron (x-vercel-cron header) - production 用
  // 2. 手動觸發 (Authorization Bearer token) - 測試用
  const isAuthorized = isVercelCron || authHeader === `Bearer ${process.env.CRON_SECRET}`;

  // 暫時性：記錄所有請求（用於除錯）
  console.log('[DEBUG] Request info:');
  console.log('[DEBUG] - Vercel Cron header:', isVercelCron);
  console.log('[DEBUG] - Auth header:', authHeader ? 'present' : 'missing');
  console.log('[DEBUG] - CRON_SECRET configured:', !!process.env.CRON_SECRET);

  // 暫時允許所有請求（測試 GitHub Actions 觸發）
  // TODO: 移除這個註解後重新啟用驗證
  // if (!isAuthorized) {
  //   return res.status(401).json({
  //     error: 'Unauthorized',
  //     message: 'Invalid authentication'
  //   });
  // }

  const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
  const REPO_OWNER = 'ThinkerCafe-tw';
  const REPO_NAME = 'paomateng';
  const WORKFLOW_ID = 'monitor.yml';

  if (!GITHUB_TOKEN) {
    return res.status(500).json({
      error: 'Configuration Error',
      message: 'GITHUB_TOKEN not set'
    });
  }

  try {
    // 觸發 GitHub Actions workflow_dispatch
    const response = await fetch(
      `https://api.github.com/repos/${REPO_OWNER}/${REPO_NAME}/actions/workflows/${WORKFLOW_ID}/dispatches`,
      {
        method: 'POST',
        headers: {
          'Accept': 'application/vnd.github+json',
          'Authorization': `Bearer ${GITHUB_TOKEN}`,
          'X-GitHub-Api-Version': '2022-11-28',
          'User-Agent': 'Vercel-Cron-Trigger'
        },
        body: JSON.stringify({
          ref: 'main' // 指定分支
        })
      }
    );

    if (response.ok) {
      console.log(`[${new Date().toISOString()}] ✅ Successfully triggered workflow`);

      return res.status(200).json({
        success: true,
        message: 'Workflow triggered successfully',
        timestamp: new Date().toISOString(),
        workflow: WORKFLOW_ID
      });
    } else {
      const errorText = await response.text();
      console.error(`[${new Date().toISOString()}] ❌ GitHub API Error:`, errorText);

      return res.status(response.status).json({
        success: false,
        error: 'GitHub API Error',
        status: response.status,
        details: errorText
      });
    }
  } catch (error) {
    console.error(`[${new Date().toISOString()}] ❌ Trigger failed:`, error);

    return res.status(500).json({
      success: false,
      error: 'Internal Server Error',
      message: error.message
    });
  }
}
