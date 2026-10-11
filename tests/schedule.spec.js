// @ts-check
const { test, expect } = require('@playwright/test');
const { execFileSync } = require('node:child_process');

// 前提(ハーネス):
// - Apache+mpc コンテナ (既定 shmpd-web) の docroot へ cgi-bin/ + bin/ を配置済み
// - 同 docroot の bin/ へ tests/fixtures/fake-at/{at,atq,atrm,pgrep} を複写済み
//   (コンテナに本物の at が無いため末尾追加の PATH でも偽物が見つかる)
// - コンテナの settings/shmpd.conf の MPD_HOST/MPD_PORT と
//   本テストへ渡す MPD_HOST/MPD_PORT が一致していること
// 実行例:
//   MPD_HOST=192.168.1.145 MPD_PORT=6600 BASE_URL=http://127.0.0.1:8081 \
//     SCHEDULE_CONTAINER=shmpd-sched-web npx playwright test tests/schedule.spec.js

const SCHEDULE_URL = '/cgi-bin/schedule/schedule.cgi';
const CONTAINER = process.env.SCHEDULE_CONTAINER || 'shmpd-web';
const SPOOL = '/tmp/fake-at-spool';
const REFERER = `${process.env.BASE_URL || 'http://localhost'}/cgi-bin/index.cgi`;

// MPDの操作にはmpcを使用 (MPD_HOST, MPD_PORTは実行環境より継承)
function mpc(args) {
  return execFileSync('mpc', args, { encoding: 'utf8', env: process.env })
    .replace(/\n$/, '');
}

// ハーネスコンテナ内でコマンドを実行する
function dockerExec(args) {
  return execFileSync('docker', ['exec', CONTAINER, ...args], { encoding: 'utf8' });
}

// 偽スプールの読み取り(無い場合はnull)
function spoolFile(name) {
  try {
    return dockerExec(['cat', `${SPOOL}/${name}`]).replace(/\n$/, '');
  } catch {
    return null;
  }
}

// 偽スプールの初期化
function resetSpool() {
  dockerExec(['rm', '-rf', SPOOL]);
}

// POSTで予約CGIを叩く
async function postSchedule(request, form) {
  const response = await request.post(SCHEDULE_URL, {
    form,
    headers: { Referer: REFERER },
  });
  expect(response.ok()).toBeTruthy();
  return response.text();
}

// 成功文よりジョブ番号を抜き出す
function jobIdOf(body) {
  const match = body.match(/job (\d+)/);
  expect(match).not.toBeNull();
  return match ? match[1] : '';
}

test.describe('Schedule (reserve play/pause/stop)', () => {

  test.beforeEach(() => {
    resetSpool();
  });

  test('schedule page renders POST-only forms without JS', async ({ page }) => {
    await page.goto(SCHEDULE_URL);

    await expect(page.getByRole('heading', { name: 'Reserve' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Reservations' })).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Result' })).toBeVisible();

    await expect(page.locator('form[name="after_form"]')).toHaveAttribute('method', 'POST');
    await expect(page.locator('form[name="at_form"]')).toHaveAttribute('method', 'POST');
    await expect(page.locator('form[name="after_form"] input[name="minutes"]')).toBeVisible();
    await expect(page.locator('form[name="at_form"] input[name="clock"]')).toBeVisible();

    // 予約が無い旨の表示
    await expect(page.getByText('(予約はありません)')).toBeVisible();

    // JavaScript非依存を崩さない
    await expect(page.locator('script')).toHaveCount(0);
    const content = await page.content();
    expect(content).not.toMatch(/javascript:/i);
  });

  test('index links to schedule and keeps existing controls', async ({ page }) => {
    await page.goto('/cgi-bin/index.cgi');

    await expect(page.getByRole('link', { name: 'Schedule' })).toBeVisible();
    await expect(page.locator('form[name="control_form"] button')).toHaveCount(16);
    await expect(page.locator('form[name="control_form"] button[value="toggle"]')).toHaveCount(1);
  });

  test('invalid minutes fails without calling at', async ({ request }) => {
    for (const minutes of ['0', '10081', 'abc', '5; reboot']) {
      const body = await postSchedule(request, { mode: 'after', minutes, action: 'play' });
      expect(body).toContain('minutes が不正');
    }
    expect(spoolFile('calls.log')).toBeNull();
  });

  test('invalid clock fails without calling at', async ({ request }) => {
    for (const clock of ['25:00', '9:00', 'ab:cd', '21:30\nmpc clear']) {
      const body = await postSchedule(request, { mode: 'at', clock, action: 'stop' });
      expect(body).toContain('clock が不正');
    }
    expect(spoolFile('calls.log')).toBeNull();
  });

  test('invalid action fails without calling at', async ({ request }) => {
    const body = await postSchedule(request, { mode: 'after', minutes: '5', action: 'dance' });
    expect(body).toContain('action が不正');
    expect(spoolFile('calls.log')).toBeNull();
  });

  test('invalid jobid fails without calling atrm', async ({ request }) => {
    const body = await postSchedule(request, { jobid: '1; reboot' });
    expect(body).toContain('JOBID が不正');
    expect(spoolFile('calls.log')).toBeNull();
  });

  test('reserve after-minutes, listed, then canceled', async ({ request, page }) => {
    const addBody = await postSchedule(request, { mode: 'after', minutes: '5', action: 'play' });
    expect(addBody).toContain('予約を登録');
    const jobId = jobIdOf(addBody);

    // at への引き渡しは now + N minutes 形式
    const calls = spoolFile('calls.log');
    expect(calls).toContain(`now + 5 minutes`);

    // 生成脚本は環境変数の代入と mpc 1行のみ(ユーザ入力の混入なし)
    const jobScript = spoolFile(`${jobId}.sh`);
    expect(jobScript).toContain('# sh-mpd schedule action=play');
    expect(jobScript).toContain('mpc play');
    expect(jobScript).toContain(`MPD_HOST="${process.env.MPD_HOST || '127.0.0.1'}"`);
    expect(jobScript).not.toContain('reboot');

    // 一覧に載り、他用途ジョブ(99)は濾過される
    await page.goto(SCHEDULE_URL);
    await expect(page.getByText('action=play')).toBeVisible();
    await expect(page.getByText('(予約はありません)')).toHaveCount(0);
    const reservations = await page.locator('section:has(h2:text("Reservations"))').textContent();
    // 他用途ジョブ(日付 2026-01-02 の行)は濾過される
    expect(reservations).not.toContain('2026-01-02');

    // 取消後は一覧が空に戻る
    const cancelBody = await postSchedule(request, { jobid: jobId });
    expect(cancelBody).toContain('予約を取消');
    await page.goto(SCHEDULE_URL);
    await expect(page.getByText('(予約はありません)')).toBeVisible();
  });

  test('reserve clock time', async ({ request }) => {
    const addBody = await postSchedule(request, { mode: 'at', clock: '23:59', action: 'stop' });
    expect(addBody).toContain('予約を登録');
    const jobId = jobIdOf(addBody);

    const jobScript = spoolFile(`${jobId}.sh`);
    expect(jobScript).toContain('# sh-mpd schedule action=stop');
    expect(jobScript).toContain('mpc stop');

    // 後片付け(キューや再生状態には触れない)
    const cancelBody = await postSchedule(request, { jobid: jobId });
    expect(cancelBody).toContain('予約を取消');
  });

  test('disabled mode hides forms', async ({ page, request }) => {
    const confPath = '/usr/local/apache2/htdocs/cgi-bin/settings/shmpd.conf';
    const original = dockerExec(['cat', confPath]);

    try {
      dockerExec(['sh', '-c', `printf '%s\\nschedule_enabled="no"\\n' '${original}' > '${confPath}'`]);

      await page.goto(SCHEDULE_URL);
      await expect(page.getByText('予約機能は無効です')).toBeVisible();
      await expect(page.locator('form[name="after_form"]')).toHaveCount(0);
      await expect(page.locator('form[name="at_form"]')).toHaveCount(0);

      // 無効時はPOSTを受け付けない
      const body = await postSchedule(request, { mode: 'after', minutes: '5', action: 'play' });
      expect(body).toContain('予約機能は無効です');
      expect(spoolFile('calls.log')).toBeNull();
    } finally {
      dockerExec(['sh', '-c', `printf '%s' '${original}' > '${confPath}'`]);
    }
  });

  test('mpc control path is untouched by schedule posts', async ({ request }) => {
    // 予約の登録・取消がMPDの再生状態を変えない
    const before = mpc(['status']).split('\n')[0];
    const addBody = await postSchedule(request, { mode: 'after', minutes: '60', action: 'pause' });
    const jobId = jobIdOf(addBody);
    await postSchedule(request, { jobid: jobId });
    const after = mpc(['status']).split('\n')[0];
    expect(after).toBe(before);
  });

});
