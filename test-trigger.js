// 測試 Vercel Cron 觸發 endpoint
const CRON_SECRET = 'bb849a1b4f3403174e0bf5aed95364b8f5fb82941cbb5ff17fc5c53e87754e09';
const URL = 'https://paomateng.vercel.app/api/trigger-monitor';

async function test() {
  console.log('Testing trigger-monitor endpoint...\n');
  console.log('URL:', URL);

  try {
    const response = await fetch(URL, {
      method: 'GET',
      headers: {
        'Authorization': `Bearer ${CRON_SECRET}`,
        'User-Agent': 'Test-Script'
      }
    });

    console.log('Status:', response.status, response.statusText);
    console.log('Content-Type:', response.headers.get('content-type'));

    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      const data = await response.json();
      console.log('\nResponse:');
      console.log(JSON.stringify(data, null, 2));

      if (data.success) {
        console.log('\n✅ Success! GitHub Actions workflow has been triggered.');
        console.log('Check: https://github.com/ThinkerCafe-tw/paomateng/actions');
      } else {
        console.log('\n❌ Failed to trigger workflow');
      }
    } else {
      const text = await response.text();
      console.log('\nResponse (first 500 chars):');
      console.log(text.substring(0, 500));
    }
  } catch (error) {
    console.error('❌ Error:', error.message);
  }
}

test();
