/**
 * Vercel Serverless Function - 觸發 GitHub Actions workflow
 * 每 5 分鐘由 Vercel Cron 自動執行
 *
 * 用途: 繞過 GitHub Actions 免費版的 cron 限流
 * 成本: Vercel 免費版支援 (100GB-hours/月)
 *
 * 格式: App Router (Vercel Cron 需要此格式)
 */

// 強制 dynamic routing（防止 caching）
export const dynamic = 'force-dynamic';

export async function GET(request) {
  const timestamp = new Date().toISOString();

  // 驗證來源 - Vercel Cron 會自動帶 x-vercel-cron header
  const isVercelCron = request.headers.get('x-vercel-cron');
  const authHeader = request.headers.get('authorization');

  console.log(`[${timestamp}] Trigger monitor request received`);
  console.log(`[${timestamp}] - Vercel Cron header: ${isVercelCron}`);
  console.log(`[${timestamp}] - Auth header: ${authHeader ? 'present' : 'missing'}`);

  const GITHUB_TOKEN = process.env.GITHUB_TOKEN;
  const REPO_OWNER = 'ThinkerCafe-tw';
  const REPO_NAME = 'paomateng';
  const WORKFLOW_ID = 'monitor.yml';

  if (!GITHUB_TOKEN) {
    console.error(`[${timestamp}] ❌ GITHUB_TOKEN not configured`);
    return new Response(JSON.stringify({
      error: 'Configuration Error',
      message: 'GITHUB_TOKEN not set',
      timestamp
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
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
          ref: 'main'
        })
      }
    );

    if (response.ok || response.status === 204) {
      console.log(`[${timestamp}] ✅ Successfully triggered workflow (HTTP ${response.status})`);

      return new Response(JSON.stringify({
        success: true,
        message: 'Workflow triggered successfully',
        timestamp,
        workflow: WORKFLOW_ID,
        isVercelCron: !!isVercelCron
      }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      });
    } else {
      const errorText = await response.text();
      console.error(`[${timestamp}] ❌ GitHub API Error (${response.status}):`, errorText);

      return new Response(JSON.stringify({
        success: false,
        error: 'GitHub API Error',
        status: response.status,
        details: errorText,
        timestamp
      }), {
        status: response.status,
        headers: { 'Content-Type': 'application/json' }
      });
    }
  } catch (error) {
    console.error(`[${timestamp}] ❌ Trigger failed:`, error.message);

    return new Response(JSON.stringify({
      success: false,
      error: 'Internal Server Error',
      message: error.message,
      timestamp
    }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}
