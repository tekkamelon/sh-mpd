// @ts-check
const { test, expect } = require('@playwright/test');
const { execFileSync } = require('node:child_process');
const path = require('node:path');

const DIRECTORY_URL = '/cgi-bin/directory/directory.cgi';
const QUEUED_URL = '/cgi-bin/queued/queued.cgi';
const REMOVE_URL = '/cgi-bin/queued/remove.cgi';
const REFERER = 'http://127.0.0.1/cgi-bin/index.cgi';
const TRICKY = 'Album A/01 tricky & tag.mp3';

// MPD の操作には mpc を使用 (MPD_HOST, MPD_PORT は実行環境より継承)
function mpc(args) {
  return execFileSync('mpc', args, { encoding: 'utf8', env: process.env })
    .replace(/\n$/, '');
}

function queueFiles() {
  const out = mpc(['-f', '%file%', 'playlist']);
  return out === '' ? [] : out.split('\n');
}

function resetQueue() {
  mpc(['clear']);
  mpc(['add', '/']);
}

// ブラウザのフォーム送信と同じ application/x-www-form-urlencoded を組み立てる
function formBody(fields) {
  return fields
    .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(value)}`)
    .join('&');
}

function post(request, url, fields) {
  return request.post(url, {
    data: formBody(fields),
    headers: {
      Referer: REFERER,
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
}

test.describe('行番号ではなく楽曲パスで指定する', () => {

  test.beforeEach(() => {
    resetQueue();
  });

  test('directory: ボタン値は行番号ではなくパス', async ({ page }) => {
    await page.goto(DIRECTORY_URL);
    await page.evaluate(() => {
      document.querySelectorAll('form.directory-list details.dir-tree').forEach((el) => {
        el.setAttribute('open', '');
      });
    });

    const values = await page.locator('form.directory-list button[name="add"]')
      .evaluateAll((els) => els.map((el) => el.getAttribute('value')));

    expect(values.length).toBeGreaterThan(0);
    for (const value of values) {
      expect(value).not.toMatch(/^\d+$/);
      expect(value).toContain('/');
    }
    // '&' は HTML 属性内で脱出される
    await expect(page.locator('form.directory-list')).toContainText('01 tricky & tag.mp3');
    const html = await page.locator('form.directory-list').innerHTML();
    expect(html).toContain('tricky &amp; tag.mp3');
  });

  test('directory: 単曲追加はパスで行い "&" や日本語を含んでも一致する', async ({ request }) => {
    mpc(['clear']);

    const res = await post(request, DIRECTORY_URL, [['add', TRICKY]]);

    expect(res.status()).toBe(200);
    expect(await res.text()).toContain('Added: Album A/01 tricky &amp; tag.mp3');
    expect(queueFiles()).toEqual([TRICKY]);
    expect(mpc(['current', '-f', '%file%'])).toBe(TRICKY);
  });

  test('directory: 検索結果から選んだ曲をパスで追加する', async ({ request }) => {
    mpc(['clear']);

    // 旧方式では検索後の value=1 が listall の先頭(別の曲)を指していた
    const res = await post(request, `${DIRECTORY_URL}?search_word=Biosphere`, [
      ['add', 'Biosphere/Substrata/01.mp3'],
    ]);

    expect(res.status()).toBe(200);
    expect(queueFiles()).toEqual(['Biosphere/Substrata/01.mp3']);
  });

  test('queued: 描画後にキューが動いてもパスで正しい曲を再生する', async ({ page, request }) => {
    await page.goto(QUEUED_URL);
    const button = page.locator('form[name="music"] button[name="play"]')
      .filter({ hasText: 'Chill - Loose' }).first();
    const songPath = await button.getAttribute('value');
    expect(songPath).toBe('chill/loose.mp3');

    // 描画後に先頭を削除し,位置を 1 つずらす
    mpc(['del', '1']);

    const res = await post(request, QUEUED_URL, [['play', songPath]]);

    expect(res.status()).toBe(200);
    expect(mpc(['current', '-f', '%file%'])).toBe('chill/loose.mp3');
  });

  test('queued: キューに無いパスでも 200 を返しキューを壊さない', async ({ request }) => {
    const before = queueFiles();

    const res = await post(request, QUEUED_URL, [['play', 'does/not/exist.mp3']]);

    expect(res.status()).toBe(200);
    expect(queueFiles()).toEqual(before);
  });

  test('remove: 複数選択をパスで削除し,キュー変動後も別曲を消さない', async ({ page, request }) => {
    await page.goto(REMOVE_URL);
    const values = await page.locator('form[name="music"] input[name="del"]')
      .evaluateAll((els) => els.map((el) => el.getAttribute('value')));
    const selected = values.filter(
      (value) => value && ['Album A/02 second.mp3', '汐海ワカ/01.mp3'].includes(value),
    );
    expect(selected).toHaveLength(2);

    // 描画後に先頭を削除し,位置を 1 つずらす
    mpc(['del', '1']);

    const res = await post(request, REMOVE_URL, selected.map((value) => ['del', value]));

    expect(res.status()).toBe(200);
    expect(queueFiles()).toEqual(['Biosphere/Substrata/01.mp3', 'chill/loose.mp3']);
  });

  test('remove: 同じ曲が重複していても選択した数だけ消す', async ({ request }) => {
    mpc(['clear']);
    mpc(['add', 'chill/loose.mp3']);
    mpc(['add', 'chill/loose.mp3']);
    mpc(['add', 'Biosphere/Substrata/01.mp3']);

    // 1つだけ選択 -> 1つだけ消える
    const first = await post(request, REMOVE_URL, [['del', 'chill/loose.mp3']]);
    expect(first.status()).toBe(200);
    expect(queueFiles()).toEqual(['chill/loose.mp3', 'Biosphere/Substrata/01.mp3']);

    // 2つ選択 -> 残っている1つが消える(位置の二重取りをしない)
    const second = await post(request, REMOVE_URL, [
      ['del', 'chill/loose.mp3'],
      ['del', 'chill/loose.mp3'],
    ]);
    expect(second.status()).toBe(200);
    expect(queueFiles()).toEqual(['Biosphere/Substrata/01.mp3']);
  });

  test('remove: "&" 入りパスを含む複数削除', async ({ request }) => {
    const res = await post(request, REMOVE_URL, [
      ['del', TRICKY],
      ['del', 'chill/loose.mp3'],
    ]);

    expect(res.status()).toBe(200);
    expect(queueFiles()).toEqual([
      'Album A/02 second.mp3',
      'Biosphere/Substrata/01.mp3',
      '汐海ワカ/01.mp3',
    ]);
  });

});

// 再生中表示の一致判定は、bin/directory_tree と同じく楽曲パス同士で行う
// (表示名と mpc current の既定フォーマット出力は、composer のみの曲や
//  名前だけのストリームのように一致しないタグ構成があるため)
test.describe('再生中の表示も楽曲パスで一致させる', () => {

  /**
   * @param {string[]} lines
   * @param {string} mpcCurrentFile
   * @param {string} postName
   */
  function renderQueuedSong(lines, mpcCurrentFile, postName) {
    const script = path.join(__dirname, '..', 'bin', 'queued_song');
    const input = lines.map((line) => line.replace('<US>', '\u001f')).join('\n');

    return execFileSync(
      script,
      ['-v', `mpc_current=${mpcCurrentFile}`, '-v', `post_name=${postName}`],
      { input, encoding: 'utf8' },
    );
  }

  test('queued_song: 表示名が無い曲(名前だけのストリーム相当)もパス一致で再生中表示を出す', () => {
    const html = renderQueuedSong(['radio/live.m3u<US>'], 'radio/live.m3u', 'play');

    expect(html).toContain('<span id=current><button class=now_playing name="play" value="radio/live.m3u">');
    expect(html).toContain('>radio/live.m3u</button>');
  });

  test('queued_song: composer のみの曲(表示名が再生中の既定表示と異なる)もパス一致で出す', () => {
    const html = renderQueuedSong(
      ['comp/01.mp3<US>Comp Title', 'plain/02.mp3<US>Normal Artist - Normal Song'],
      'comp/01.mp3',
      'play',
    );

    expect(html).toContain('<span id=current><button class=now_playing name="play" value="comp/01.mp3">');
    // 非再生の行は span で囲まれない通常のボタン
    expect(html).toContain('<p><button name="play" value="plain/02.mp3">');
  });

  test('queued_song: 違うパスを渡した曲には再生中表示を出さない', () => {
    const html = renderQueuedSong(
      ['plain/02.mp3<US>Normal Artist - Normal Song'],
      'comp/01.mp3',
      'play',
    );

    expect(html).not.toContain('id=current');
  });

  test('queued_song: 削除用チェックボックスでもパス一致で再生中表示を出す', () => {
    const html = renderQueuedSong(['comp/01.mp3<US>Comp Title'], 'comp/01.mp3', 'del');

    expect(html).toContain('<span id=current><input type=checkbox name="del" value="comp/01.mp3">');
    expect(html).toContain('[Now Playing]');
  });

});
