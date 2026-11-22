// @ts-check
// X投稿機能(bin/x_share_text, bin/x_oauth2, bin/x_post, index.cgi, x_post.cgi)の検証
//
// 実行方法: 他のspecと同様に単体で実行する(MPDを操作するため並走を避ける):
//   MPD_HOST=192.168.1.145 MPD_PORT=6600 BASE_URL=http://127.0.0.1 \
//     npx playwright test tests/x-post.spec.js --reporter=list
//
// 構成:
//   - bin/x_share_text は stub mpc で5分岐を独立検算する
//   - bin/x_oauth2, bin/x_post, x_post.cgi は stub curl と一時トークンファイルで検証する
//     (実APIへの接続は行わない)
//   - index.cgi, x_post.cgi のページ検証はCGIを直接実行する(実MPDが必要)

const { test, expect } = require('@playwright/test');
const { execFileSync, spawnSync } = require('node:child_process');
const crypto = require('node:crypto');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const REPO = path.join(__dirname, '..');
const BIN = path.join(REPO, 'bin');
const CGI_BIN = path.join(REPO, 'cgi-bin');
const X_SHARE_TEXT = path.join(BIN, 'x_share_text');
const X_OAUTH2 = path.join(BIN, 'x_oauth2');
const X_POST = path.join(BIN, 'x_post');
const INDEX_CGI = path.join(CGI_BIN, 'index.cgi');
const X_POST_CGI = path.join(CGI_BIN, 'x_post.cgi');

const DEFAULT_TEMPLATE = '%artist% - %title% (%album%)';
const US = '\u001f';

const TWEET_OK_RESPONSE = '{"data":{"id":"1760000000000000000","text":"ok"}}';

// ====== 共通のへルパ ======

// stubスクリプト置き場とトークン類の一時ディレクトリ
let workDir = '';

function makeDir(name) {
  const dir = fs.mkdtempSync(path.join(workDir, `${name}-`));
  return dir;
}

// stub mpc: current -f <format> のみサポート
// 環境変数 MPC_FILE, MPC_ARTIST, MPC_TITLE, MPC_ALBUM, MPC_NAME をタグ値として使う
// MPC_STOPPED=1 で停止中(mpc current が何も出力しない状態)を表す
function writeStubMpc(dir) {
  const script = `#!/bin/sh
case "\${1:-}:\${2:-}" in
  current:-f)
    if [ -n "\${MPC_STOPPED:-}" ] ; then
      exit 0
    fi
    exec node "\${MPC_STUB_JS}" "\${3}"
    ;;
esac
exit 1
`;
  fs.writeFileSync(path.join(dir, 'mpc'), script, { mode: 0o755 });

  const tags = ['file', 'artist', 'title', 'album', 'name'];
  const render = `
const env = process.env;
let out = process.argv[2];
${tags.map((tag) => `
  out = out.split('%${tag}%').join(env['MPC_${tag.toUpperCase()}'] || '');`).join('')}
process.stdout.write(out + '\\n');
`;
  fs.writeFileSync(path.join(dir, 'mpc-stub.js'), render, { mode: 0o755 });
  return path.join(dir, 'mpc-stub.js');
}

// stub curl: 引数をCURL_LOGへ記録し,URLに応じたcanned応答を返す
//   api.x.com/2/oauth2/token   -> TOKEN_RESPONSE (既定は有効なトークン応答)
//   api.x.com/2/media/upload   -> UPLOAD_RESPONSE (既定は data.id を含む応答)
//   api.x.com/2/tweets         -> TWEET_RESPONSE (既定は data.id を含む応答)
//   それ以外(カバー画像の取得)  -> COVER_RESPONSE を -o 先へ書く(COVER_FAIL=1 なら失敗)
function writeStubCurl(dir) {
  const script = `#!/bin/sh
printf '%s\\n' "\${*}" >> "\${CURL_LOG:-/dev/null}"

# -o <file> の処理(最後の-oを優先)
out_file=""
prev=""
for arg in "\${@}" ; do
  if [ "\${prev}" = "-o" ] ; then
    out_file="\${arg}"
  fi
  prev="\${arg}"
done

emit () {
  if [ -n "\${out_file}" ] ; then
    printf '%s' "\${1}" > "\${out_file}"
  else
    printf '%s' "\${1}"
  fi
}

for arg in "\${@}" ; do
  case "\${arg}" in
    https://api.x.com/2/oauth2/token)
      emit "\${TOKEN_RESPONSE:-{\\"token_type\\":\\"bearer\\",\\"expires_in\\":7200,\\"access_token\\":\\"ROT_ACCESS\\",\\"refresh_token\\":\\"ROT_REFRESH\\"}}"
      exit 0
      ;;
    https://api.x.com/2/media/upload)
      if [ -n "\${UPLOAD_FAIL:-}" ] ; then
        emit "{\\"errors\\":[{\\"message\\":\\"upload failed\\"}]}"
        exit 1
      fi
      emit "\${UPLOAD_RESPONSE:-{\\"data\\":{\\"id\\":\\"MEDIA123\\",\\"media_key\\":\\"3_123\\"}}}"
      exit 0
      ;;
    https://api.x.com/2/tweets)
      if [ -n "\${TWEET_FAIL:-}" ] ; then
        emit "{\\"errors\\":[{\\"message\\":\\"tweet failed\\"}]}"
        exit 1
      fi
      emit "\${TWEET_RESPONSE:-{\\"data\\":{\\"id\\":\\"1760000000000000000\\",\\"text\\":\\"ok\\"}}}"
      exit 0
      ;;
  esac
done

# それ以外はカバー画像の取得
if [ -n "\${COVER_FAIL:-}" ] ; then
  exit 22
fi
emit "\${COVER_RESPONSE:-FAKEJPEGBYTES}"
exit 0
`;
  fs.writeFileSync(path.join(dir, 'curl'), script, { mode: 0o755 });
}

// bin/x_share_text をstub mpc環境で実行し本文を得る
function shareText(dir, tags, env = {}) {
  const stubJs = writeStubMpc(dir);
  const out = spawnSync(X_SHARE_TEXT, {
    encoding: 'utf8',
    env: {
      ...process.env,
      PATH: `${dir}:${process.env.PATH}`,
      MPC_STUB_JS: stubJs,
      MPC_FILE: tags.file || '',
      MPC_ARTIST: tags.artist || '',
      MPC_TITLE: tags.title || '',
      MPC_ALBUM: tags.album || '',
      MPC_NAME: tags.name || '',
      ...(tags.stopped ? { MPC_STOPPED: '1' } : {}),
      ...env,
    },
  });
  expect(out.status, `x_share_text failed: ${out.stderr}`).toBe(0);
  return out.stdout;
}

// 独立検算: タグとテンプレートから期待される本文をJS側で組み立てる
function renderTemplate(template, tags) {
  return template
    .split('%artist%').join(tags.artist || '')
    .split('%title%').join(tags.title || '')
    .split('%album%').join(tags.album || '');
}

// ====== bin/x_share_text: 5分岐の独立検算 ======

test.describe('bin/x_share_text: タグの状態ごとの本文生成', () => {

  test.beforeAll(() => {
    workDir = fs.mkdtempSync(path.join(os.tmpdir(), 'xpost-'));
  });

  test.afterAll(() => {
    fs.rmSync(workDir, { recursive: true, force: true });
  });

  test('全タグ揃いはテンプレート本文(既定)になる', () => {
    const dir = makeDir('share');
    const tags = { file: 'dir/song.flac', artist: 'Artist', title: 'Title', album: 'Album', name: '' };
    expect(shareText(dir, tags)).toBe(renderTemplate(DEFAULT_TEMPLATE, tags));
    expect(shareText(dir, tags)).toBe('Artist - Title (Album)');
  });

  test('全タグ揃いは設定テンプレートを優先する', () => {
    const dir = makeDir('share');
    const tags = { file: 'dir/song.flac', artist: 'A', title: 'T', album: 'AL', name: '' };
    const template = '#nowplaying %artist% / %title%';
    expect(shareText(dir, tags, { x_share_template: template })).toBe(renderTemplate(template, tags));
  });

  test('アルバム欠落はアーティスト名とタイトルのみ', () => {
    const dir = makeDir('share');
    const tags = { file: 'dir/song.mp3', artist: 'A', title: 'T', album: '', name: '' };
    expect(shareText(dir, tags)).toBe('Now Playing: A - T');
  });

  test('タイトル欠落はアーティスト名のみ', () => {
    const dir = makeDir('share');
    const tags = { file: 'dir/song.mp3', artist: 'A', title: '', album: 'AL', name: '' };
    expect(shareText(dir, tags)).toBe('Now Playing: A');
  });

  test('アーティスト欠落(ラジオ等)はタイトルのみ', () => {
    const dir = makeDir('share');
    const tags = { file: 'http://stream.example/', artist: '', title: 'T', album: '', name: '' };
    expect(shareText(dir, tags)).toBe('Now Playing: T');
  });

  test('全タグ欠落はストリーム名,次いでURIで代替する', () => {
    const dir = makeDir('share');
    expect(shareText(dir, { file: 'http://stream.example/', name: 'RadioName' }))
      .toBe('Now Playing: RadioName');
    expect(shareText(dir, { file: 'http://stream.example/', name: '' }))
      .toBe('Now Playing: http://stream.example/');
  });

  test('停止中は空を出力する', () => {
    const dir = makeDir('share');
    expect(shareText(dir, { stopped: true, file: 'dir/song.mp3', artist: 'A', title: 'T' })).toBe('');
  });

});

// ====== bin/x_oauth2: PKCEとトークン交換 ======

test.describe('bin/x_oauth2: 認可URL生成とコード交換', () => {

  test.beforeAll(() => {
    workDir = fs.mkdtempSync(path.join(os.tmpdir(), 'xoauth-'));
  });

  test.afterAll(() => {
    fs.rmSync(workDir, { recursive: true, force: true });
  });

  // x_oauth2実行用の環境(資格はダミー,API接続はstub curlが受ける)
  function oauthEnv(dir, extra = {}) {
    return {
      ...process.env,
      x_api_conf: path.join(dir, 'nonexistent.conf'),
      x_oauth2_client_id: 'dummy_client_id',
      x_oauth2_client_secret: 'dummy_client_secret',
      x_redirect_uri: 'http://127.0.0.1:18937/callback',
      x_token_file: path.join(dir, 'x_token.conf'),
      PATH: `${path.join(dir, 'stubbin')}:${process.env.PATH}`,
      CURL_LOG: path.join(dir, 'curl.log'),
      ...extra,
    };
  }

  test('setup: S256のcode_challengeがBASE64URL(SHA256(verifier))と一致する', () => {
    const dir = makeDir('oauth');
    fs.mkdirSync(path.join(dir, 'stubbin'));

    const out = execFileSync(X_OAUTH2, ['setup'], { encoding: 'utf8', env: oauthEnv(dir) });
    const url = out.match(/https:\/\/x\.com\/i\/oauth2\/authorize\?(\S+)/);
    expect(url).not.toBeNull();

    const params = new URLSearchParams(url[1]);
    expect(params.get('response_type')).toBe('code');
    expect(params.get('client_id')).toBe('dummy_client_id');
    expect(params.get('redirect_uri')).toBe('http://127.0.0.1:18937/callback');
    expect(params.get('code_challenge_method')).toBe('S256');
    expect(params.get('scope')).toBe('tweet.read users.read tweet.write media.write offline.access');

    // 状態ファイルよりverifierとstateを取り出し独立検算する
    const stateFile = fs.readFileSync(path.join(dir, 'x_token.conf.state'), 'utf8');
    const verifier = stateFile.match(/x_oauth2_code_verifier="([^"]+)"/)[1];
    const state = stateFile.match(/x_oauth2_state="([^"]+)"/)[1];

    const expected = crypto.createHash('sha256').update(verifier).digest('base64url');
    expect(params.get('code_challenge')).toBe(expected);
    expect(params.get('state')).toBe(state);

    // verifierはRFC 7636の許容文字かつ43文字以上
    expect(verifier).toMatch(/^[A-Za-z0-9\-._~]{43,128}$/);
  });

  test('exchange: stateを検証しトークンを保存する(状態ファイルは削除)', () => {
    const dir = makeDir('oauth');
    const stubDir = path.join(dir, 'stubbin');
    fs.mkdirSync(stubDir);
    writeStubCurl(stubDir);

    execFileSync(X_OAUTH2, ['setup'], { encoding: 'utf8', env: oauthEnv(dir) });
    const stateFile = fs.readFileSync(path.join(dir, 'x_token.conf.state'), 'utf8');
    const state = stateFile.match(/x_oauth2_state="([^"]+)"/)[1];

    const callback = `http://127.0.0.1:18937/callback?code=CODE123&state=${state}`;
    const out = execFileSync(X_OAUTH2, ['exchange', callback], { encoding: 'utf8', env: oauthEnv(dir) });
    expect(out).toContain('トークンを保存しました');

    // 交換要求の内容
    const log = fs.readFileSync(path.join(dir, 'curl.log'), 'utf8');
    expect(log).toContain('-d grant_type=authorization_code');
    expect(log).toContain('-d code=CODE123');
    expect(log).toContain('-d redirect_uri=http://127.0.0.1:18937/callback');
    expect(log).toContain('-d client_id=dummy_client_id');
    expect(log).toContain('-d client_secret=dummy_client_secret');
    expect(log).toContain(`-d code_verifier=${stateFile.match(/x_oauth2_code_verifier="([^"]+)"/)[1]}`);

    // トークンファイルと期限(expires_in=7200)
    const tokenFile = fs.readFileSync(path.join(dir, 'x_token.conf'), 'utf8');
    expect(tokenFile).toContain('x_oauth2_access_token="ROT_ACCESS"');
    expect(tokenFile).toContain('x_oauth2_refresh_token="ROT_REFRESH"');
    const expiresAt = Number(tokenFile.match(/x_oauth2_expires_at="(\d+)"/)[1]);
    const now = Math.floor(Date.now() / 1000);
    expect(expiresAt).toBeGreaterThan(now + 7000);
    expect(expiresAt).toBeLessThanOrEqual(now + 7200 + 5);

    // 認可コードは1回限り: 状態ファイルは削除される
    expect(fs.existsSync(path.join(dir, 'x_token.conf.state'))).toBe(false);
  });

  test('exchange: stateが一致しなければトークンを保存しない', () => {
    const dir = makeDir('oauth');
    fs.mkdirSync(path.join(dir, 'stubbin'));

    execFileSync(X_OAUTH2, ['setup'], { encoding: 'utf8', env: oauthEnv(dir) });

    const res = spawnSync(X_OAUTH2,
      ['exchange', 'http://127.0.0.1:18937/callback?code=CODE999&state=WRONGSTATE'],
      { encoding: 'utf8', env: oauthEnv(dir) });

    expect(res.status).not.toBe(0);
    expect(res.stderr).toContain('state');
    expect(fs.existsSync(path.join(dir, 'x_token.conf'))).toBe(false);
  });

  test('資格情報が未設定ならsetupは失敗する', () => {
    const dir = makeDir('oauth');
    fs.mkdirSync(path.join(dir, 'stubbin'));

    const res = spawnSync(X_OAUTH2, ['setup'], {
      encoding: 'utf8',
      env: {
        ...oauthEnv(dir),
        x_oauth2_client_id: '',
        x_oauth2_client_secret: '',
      },
    });

    expect(res.status).not.toBe(0);
    expect(res.stderr).toContain('未設定');
  });

  test('refresh: 現行refresh_tokenで更新し,ローテーション後のトークンを保存する', () => {
    const dir = makeDir('oauth');
    const stubDir = path.join(dir, 'stubbin');
    fs.mkdirSync(stubDir);
    writeStubCurl(stubDir);

    const tokenFile = path.join(dir, 'x_token.conf');
    const now = Math.floor(Date.now() / 1000);
    fs.writeFileSync(tokenFile,
      `x_oauth2_access_token="OLD_ACCESS"\n` +
      `x_oauth2_refresh_token="OLD_REFRESH"\n` +
      `x_oauth2_expires_at="${now - 10}"\n`);

    execFileSync(X_OAUTH2, ['refresh'], { encoding: 'utf8', env: oauthEnv(dir) });

    const log = fs.readFileSync(path.join(dir, 'curl.log'), 'utf8');
    expect(log).toContain('-d grant_type=refresh_token');
    expect(log).toContain('-d refresh_token=OLD_REFRESH');
    expect(log).toContain('-d client_id=dummy_client_id');

    const saved = fs.readFileSync(tokenFile, 'utf8');
    expect(saved).toContain('x_oauth2_access_token="ROT_ACCESS"');
    expect(saved).toContain('x_oauth2_refresh_token="ROT_REFRESH"');
  });

});

// ====== bin/x_post: トークン更新とAPI投稿(stub curl) ======

test.describe('bin/x_post: トークン更新とAPI投稿', () => {

  test.beforeAll(() => {
    workDir = fs.mkdtempSync(path.join(os.tmpdir(), 'xpost-cli-'));
  });

  test.afterAll(() => {
    fs.rmSync(workDir, { recursive: true, force: true });
  });

  /**
   * x_post 実行用の環境(資格はダミー,API接続はstub curlが受ける)
   * @param {string} dir
   * @param {Record<string, string>} extra
   */
  function postEnv(dir, extra = {}) {
    return {
      ...process.env,
      x_oauth2_client_id: 'dummy_client_id',
      x_oauth2_client_secret: 'dummy_client_secret',
      x_token_file: path.join(dir, 'x_token.conf'),
      PATH: `${path.join(dir, 'stubbin')}:${process.env.PATH}`,
      CURL_LOG: path.join(dir, 'curl.log'),
      ...extra,
    };
  }

  /**
   * トークンファイルを書く(expiresAt 既定は1時間後 = 期限内)
   * @param {string} dir
   * @param {{access?: string, refresh?: string, expiresAt?: number}} opts
   */
  function writeToken(dir, opts = {}) {
    const { access = 'VALID_ACCESS', refresh = 'VALID_REFRESH', expiresAt } = opts;
    fs.writeFileSync(path.join(dir, 'x_token.conf'),
      `x_oauth2_access_token="${access}"\n` +
      `x_oauth2_refresh_token="${refresh}"\n` +
      `x_oauth2_expires_at="${expiresAt ?? Math.floor(Date.now() / 1000) + 3600}"\n`);
  }

  /**
   * @param {string} dir
   * @param {string[]} args
   * @param {Record<string, string>} extraEnv
   */
  function runPost(dir, args, extraEnv = {}) {
    return spawnSync(X_POST, args, { encoding: 'utf8', env: postEnv(dir, extraEnv) });
  }

  /**
   * @param {string} dir
   */
  function curlLog(dir) {
    return fs.readFileSync(path.join(dir, 'curl.log'), 'utf8');
  }

  test('期限切れトークンは更新してから投稿し,ローテーションをファイルへ反映する', () => {
    const dir = makeDir('xpost');
    fs.mkdirSync(path.join(dir, 'stubbin'));
    writeStubCurl(path.join(dir, 'stubbin'));

    writeToken(dir, { expiresAt: Math.floor(Date.now() / 1000) - 100 });

    const res = runPost(dir, ['-t', 'Now Playing: A - T', '-i', 'http://127.0.0.1:8080/dir/Folder.jpg'],
      { COVER_RESPONSE: 'IMAGEBYTES' });
    expect(res.status, res.stderr).toBe(0);

    const log = curlLog(dir);

    // まず更新が呼ばれる
    expect(log).toContain('https://api.x.com/2/oauth2/token');
    expect(log).toContain('-d grant_type=refresh_token');
    expect(log).toContain('-d refresh_token=VALID_REFRESH');

    // 更新後のトークンでmedia uploadと投稿が行われる
    expect((log.match(/Bearer ROT_ACCESS/g) || []).length).toBe(2);
    expect(log).not.toContain('Bearer VALID_ACCESS');

    // 新トークンが一時ファイル+mvで保存されている
    const saved = fs.readFileSync(path.join(dir, 'x_token.conf'), 'utf8');
    expect(saved).toContain('x_oauth2_access_token="ROT_ACCESS"');
    expect(saved).toContain('x_oauth2_refresh_token="ROT_REFRESH"');
    const expiresMatch = saved.match(/x_oauth2_expires_at="(\d+)"/);
    expect(expiresMatch).not.toBeNull();
    const expiresAt = Number(expiresMatch && expiresMatch[1]);
    expect(expiresAt).toBeGreaterThan(Math.floor(Date.now() / 1000) + 7000);

    // 成功時は投稿応答本文を標準出力へ
    expect(res.stdout).toBe(TWEET_OK_RESPONSE);
  });

  test('有効期限内なら更新せずBearerヘッダで本文のみ投稿する', () => {
    const dir = makeDir('xpost');
    fs.mkdirSync(path.join(dir, 'stubbin'));
    writeStubCurl(path.join(dir, 'stubbin'));

    writeToken(dir);

    const res = runPost(dir, ['-t', 'plain text']);
    expect(res.status, res.stderr).toBe(0);

    const log = curlLog(dir);
    expect(log).not.toContain('/2/oauth2/token');
    expect(log).not.toContain('/2/media/upload');
    expect(log).toContain('-H Authorization: Bearer VALID_ACCESS');
    expect(log).toContain('-H Content-type: application/json');
    expect(log).toContain('-d {"text":"plain text"}');
  });

  test('カバー画像を添付して投稿する(-F引数とmedia_ids)', () => {
    const dir = makeDir('xpost');
    fs.mkdirSync(path.join(dir, 'stubbin'));
    writeStubCurl(path.join(dir, 'stubbin'));

    writeToken(dir);

    const coverUrl = 'http://127.0.0.1:8080/dir/Folder.jpg';
    const res = runPost(dir, ['-t', 'with cover', '-i', coverUrl], { COVER_RESPONSE: 'IMAGEBYTES' });
    expect(res.status, res.stderr).toBe(0);

    const log = curlLog(dir);

    // カバー画像の取得(-f, -o, URL)
    expect(log).toContain(`-sS -f -m 10 -o `);
    expect(log).toContain(` ${coverUrl}`);

    // media upload の引数
    expect(log).toContain('https://api.x.com/2/media/upload');
    expect(log).toContain('-F media_category=tweet_image');
    expect(log).toContain('-F media=@');
    expect(log).toContain(';type=image/jpeg');

    // 投稿本文にmedia uploadの応答idが入る
    expect(log).toContain('-d {"text":"with cover","media":{"media_ids":["MEDIA123"]}}');
  });

  test('カバー取得に失敗したら本文のみで投稿する', () => {
    const dir = makeDir('xpost');
    fs.mkdirSync(path.join(dir, 'stubbin'));
    writeStubCurl(path.join(dir, 'stubbin'));

    writeToken(dir);

    const res = runPost(dir, ['-t', 'no cover', '-i', 'http://127.0.0.1:8080/dir/Folder.jpg'],
      { COVER_FAIL: '1' });

    // 投稿自体は成功する
    expect(res.status, res.stderr).toBe(0);
    expect(res.stderr).toContain('本文のみで投稿します');

    const log = curlLog(dir);
    expect(log).not.toContain('/2/media/upload');
    expect(log).toContain('-d {"text":"no cover"}');
  });

  test('media upload に失敗したら投稿を行わない', () => {
    const dir = makeDir('xpost');
    fs.mkdirSync(path.join(dir, 'stubbin'));
    writeStubCurl(path.join(dir, 'stubbin'));

    writeToken(dir);

    const res = runPost(dir, ['-t', 'upload fails', '-i', 'http://127.0.0.1:8080/dir/Folder.jpg'],
      { UPLOAD_FAIL: '1' });

    expect(res.status).not.toBe(0);
    expect(res.stderr).toContain('media upload に失敗しました');
    expect(res.stderr).toContain('"upload failed"');

    const log = curlLog(dir);
    expect(log).not.toContain('https://api.x.com/2/tweets');
  });

  test('client_id が未設定ならAPIを一切呼ばず失敗する', () => {
    const dir = makeDir('xpost');
    fs.mkdirSync(path.join(dir, 'stubbin'));
    writeStubCurl(path.join(dir, 'stubbin'));

    writeToken(dir);

    const res = runPost(dir, ['-t', 'no credentials'],
      { x_oauth2_client_id: '', x_oauth2_client_secret: '' });

    expect(res.status).not.toBe(0);
    expect(res.stderr).toContain('未設定');
    expect(fs.existsSync(path.join(dir, 'curl.log'))).toBe(false);
  });

  test('投稿に失敗したらAPI応答を標準エラーへ出す', () => {
    const dir = makeDir('xpost');
    fs.mkdirSync(path.join(dir, 'stubbin'));
    writeStubCurl(path.join(dir, 'stubbin'));

    writeToken(dir);

    const res = runPost(dir, ['-t', 'will fail'], { TWEET_FAIL: '1' });

    expect(res.status).not.toBe(0);
    expect(res.stderr).toContain('投稿に失敗しました');
    // 原因(401/403/429等)を隠さないため応答本文を生で出す
    expect(res.stderr).toContain('"tweet failed"');
  });

  test('本文中の引用符とバックスラッシュをエスケープし,制御文字を除去する', () => {
    const dir = makeDir('xpost');
    fs.mkdirSync(path.join(dir, 'stubbin'));
    writeStubCurl(path.join(dir, 'stubbin'));

    writeToken(dir);

    // " と \ と多バイト文字を含み,タブと改行を混ぜる
    const text = 'A "q" \\b 途\t中\nend';
    const res = runPost(dir, ['-t', text]);
    expect(res.status, res.stderr).toBe(0);

    // タブと改行は除去され,引用符とバックスラッシュのみエスケープされる
    expect(curlLog(dir)).toContain('-d {"text":"A \\"q\\" \\\\b 途中end"}');
  });

});

// RFC 3986 の非予約文字以外を%HHへエンコードする(独立検算用)
/**
 * @param {string} s
 */
function rfc3986(s) {
  return [...Buffer.from(s, 'utf8')].map((b) => {
    const c = String.fromCharCode(b);
    return /[A-Za-z0-9\-._~]/.test(c) ? c : `%${b.toString(16).toUpperCase().padStart(2, '0')}`;
  }).join('');
}

// ====== bin/coverart_url: パスセグメントのエンコード(stub mpc) ======

test.describe('bin/coverart_url: パス区切りを保ったままセグメントをエンコードする', () => {

  test.beforeAll(() => {
    workDir = fs.mkdtempSync(path.join(os.tmpdir(), 'cover-'));
  });

  test.afterAll(() => {
    fs.rmSync(workDir, { recursive: true, force: true });
  });

  /**
   * stub mpc 環境で coverart_url を実行する
   * @param {string} dir
   * @param {string} file
   * @param {Record<string, string>} extra
   */
  function coverUrl(dir, file, extra = {}) {
    const stubJs = writeStubMpc(dir);
    const out = spawnSync(path.join(BIN, 'coverart_url'), {
      encoding: 'utf8',
      env: {
        ...process.env,
        PATH: `${dir}:${process.env.PATH}`,
        MPC_STUB_JS: stubJs,
        MPC_FILE: file,
        img_server_host: '127.0.0.1',
        img_server_port: '8080',
        ...extra,
      },
    });
    expect(out.status, out.stderr).toBe(0);
    return out.stdout;
  }

  test('空白と# ?を含むパスはセグメント単位でエンコードされ,区切りは保たれる', () => {
    const dir = makeDir('cover');

    expect(coverUrl(dir, 'Album A/02 second.flac'))
      .toBe(`http://127.0.0.1:8080/${rfc3986('Album A')}/Folder.jpg`);

    const tricky = 'Tag #1/Sub?dir/曲 ディレクトリ/song.flac';
    expect(coverUrl(dir, tricky))
      .toBe(`http://127.0.0.1:8080/${['Tag #1', 'Sub?dir', '曲 ディレクトリ'].map(rfc3986).join('/')}/Folder.jpg`);
  });

  test('予約文字を含まないパスは従来どおり素通しする', () => {
    const dir = makeDir('cover');

    expect(coverUrl(dir, 'Artist/Album_2026/song.flac'))
      .toBe('http://127.0.0.1:8080/Artist/Album_2026/Folder.jpg');
  });

  test('img_server が未設定なら空を出力する', () => {
    const dir = makeDir('cover');
    const stubJs = writeStubMpc(dir);
    const out = spawnSync(path.join(BIN, 'coverart_url'), {
      encoding: 'utf8',
      env: {
        ...process.env,
        PATH: `${dir}:${process.env.PATH}`,
        MPC_STUB_JS: stubJs,
        MPC_FILE: 'Album A/song.flac',
      },
    });
    expect(out.status, out.stderr).toBe(0);
    expect(out.stdout).toBe('');
  });

  test('停止中は空を出力する', () => {
    const dir = makeDir('cover');

    expect(coverUrl(dir, 'Album A/song.flac', { MPC_STOPPED: '1' })).toBe('');
  });

});

// ====== bin/x_post: 空白入りカバーURLの取得(stub curl) ======

test.describe('bin/x_post: エンコード済みカバーURLはそのまま取得できる', () => {

  test.beforeAll(() => {
    workDir = fs.mkdtempSync(path.join(os.tmpdir(), 'xpost-enc-'));
  });

  test.afterAll(() => {
    fs.rmSync(workDir, { recursive: true, force: true });
  });

  test('空白と#のパーセントエンコード済みURLは拒否されず添付される', () => {
    const dir = makeDir('enc');
    fs.mkdirSync(path.join(dir, 'stubbin'));
    writeStubCurl(path.join(dir, 'stubbin'));
    fs.writeFileSync(path.join(dir, 'x_token.conf'),
      `x_oauth2_access_token="VALID_ACCESS"\n` +
      `x_oauth2_refresh_token="VALID_REFRESH"\n` +
      `x_oauth2_expires_at="${Math.floor(Date.now() / 1000) + 3600}"\n`);

    // coverart_url が生成する形式(セグメント単位エンコード済み)のURL
    const coverUrl = `http://127.0.0.1:18080/${rfc3986('Album A')}/Folder.jpg`;

    const out = spawnSync(X_POST, ['-t', 'cover with space', '-i', coverUrl], {
      encoding: 'utf8',
      env: {
        ...process.env,
        x_oauth2_client_id: 'dummy_client_id',
        x_oauth2_client_secret: 'dummy_client_secret',
        x_token_file: path.join(dir, 'x_token.conf'),
        PATH: `${path.join(dir, 'stubbin')}:${process.env.PATH}`,
        CURL_LOG: path.join(dir, 'curl.log'),
        COVER_RESPONSE: 'IMAGEBYTES',
      },
    });
    expect(out.status, out.stderr).toBe(0);

    const log = fs.readFileSync(path.join(dir, 'curl.log'), 'utf8');
    expect(log).toContain(` ${coverUrl}`);
    expect(log).toContain('/2/media/upload');
    expect(log).toContain('media_ids');
  });

});

// ====== index.cgi / x_post.cgi: CGI直実行によるページ検証(実MPDを使用) ======

// cgi-bin/settings/shmpd.conf の接続先(CGIはこの設定を読むため,操作側も同じ接続先を使う)
const SHMPD_CONF = fs.existsSync(path.join(CGI_BIN, 'settings', 'shmpd.conf'))
  ? fs.readFileSync(path.join(CGI_BIN, 'settings', 'shmpd.conf'), 'utf8')
  : '';
const MPD_HOST = (SHMPD_CONF.match(/^\s*export\s+MPD_HOST="([^"]*)"/m) || [])[1] || '127.0.0.1';
const MPD_PORT = (SHMPD_CONF.match(/^\s*export\s+MPD_PORT="([^"]*)"/m) || [])[1] || '6600';

/**
 * @param {string[]} args
 */
function mpc(args) {
  return execFileSync('mpc', args, {
    encoding: 'utf8',
    env: { ...process.env, MPD_HOST, MPD_PORT },
  }).replace(/\n$/, '');
}

function ensurePlaying() {
  if (mpc(['current', '-f', '%file%']) === '') {
    if (mpc(['playlist']).trim() === '') {
      mpc(['add', '/']);
    }
    mpc(['play']);
  }
}

/**
 * CGIを直接実行し,本文(ヘッダ以降)を返す
 * 呼び出し側の環境にX関連の変数が残っていても結果が変わらないよう掃除する
 * @param {string} script
 * @param {Record<string, string>} extraEnv
 */
function runCgi(script, extraEnv = {}) {
  const out = spawnSync('sh', [script], {
    cwd: CGI_BIN,
    input: 'button=post',
    encoding: 'utf8',
    env: {
      ...process.env,
      MPD_HOST,
      MPD_PORT,
      REQUEST_METHOD: 'POST',
      QUERY_STRING: '',
      HTTP_REFERER: 'http://127.0.0.1/cgi-bin/index.cgi',
      x_oauth2_client_id: '',
      x_oauth2_client_secret: '',
      x_redirect_uri: '',
      ...extraEnv,
    },
  });
  expect(out.status, out.stderr).toBe(0);
  return out.stdout.slice(out.stdout.indexOf('\n\n') + 2);
}

test.describe('index.cgi: X共有UIの出し分け', () => {

  test.beforeAll(() => {
    workDir = fs.mkdtempSync(path.join(os.tmpdir(), 'xpost-ui-'));
  });

  test.afterAll(() => {
    fs.rmSync(workDir, { recursive: true, force: true });
    mpc(['stop']);
  });

  /**
   * ダミー資格のapi設定を書く
   * @param {string} dir
   * @param {string} extra
   */
  function writeApiConf(dir, extra = '') {
    const conf = path.join(dir, 'x_api.conf');
    fs.writeFileSync(conf,
      'x_oauth2_client_id="dummy_client_id"\n' +
      'x_oauth2_client_secret="dummy_client_secret"\n' +
      extra);
    return conf;
  }

  test('API未設定(従来)はIntentリンクを出し,フォームは出さない', () => {
    ensurePlaying();
    const dir = makeDir('ui');
    const body = runCgi(INDEX_CGI, { x_api_conf: path.join(dir, 'nonexistent.conf') });

    expect(body).toContain('Share on X');
    expect(body).toMatch(/https:\/\/twitter\.com\/intent\/tweet\?text=/);
    expect(body).not.toContain('x_post_form');
    expect(body).not.toContain('Post to X');
  });

  test('API設定済みはフォームボタンを出し,Intentリンクを消す', () => {
    ensurePlaying();
    const dir = makeDir('ui');
    const apiConf = writeApiConf(dir);

    const body = runCgi(INDEX_CGI, { x_api_conf: apiConf });

    expect(body).toContain('Post to X');
    expect(body).toContain('<form name="x_post_form" method="POST" action="x_post.cgi">');
    expect(body).not.toContain('intent/tweet');
    expect(body).not.toContain('Share on X');
  });

  test('資格が空のapi設定は未設定扱いでIntentリンクを出す', () => {
    ensurePlaying();
    const dir = makeDir('ui');
    const conf = path.join(dir, 'x_api.conf');
    fs.writeFileSync(conf, 'x_oauth2_client_id=""\nx_oauth2_client_secret=""\n');

    const body = runCgi(INDEX_CGI, { x_api_conf: conf });

    expect(body).toContain('Share on X');
    expect(body).not.toContain('x_post_form');
  });

  test('停止中は設定の有無に関わらず何も出さない', () => {
    mpc(['stop']);
    const dir = makeDir('ui');

    const noApi = runCgi(INDEX_CGI, { x_api_conf: path.join(dir, 'nonexistent.conf') });
    expect(noApi).not.toContain('Share on X');
    expect(noApi).not.toContain('Post to X');

    const withApi = runCgi(INDEX_CGI, { x_api_conf: writeApiConf(dir) });
    expect(withApi).not.toContain('Share on X');
    expect(withApi).not.toContain('Post to X');
  });

});

test.describe('x_post.cgi: 投稿の受付と結果ページ', () => {

  test.beforeAll(() => {
    workDir = fs.mkdtempSync(path.join(os.tmpdir(), 'xpost-page-'));
  });

  test.afterAll(() => {
    fs.rmSync(workDir, { recursive: true, force: true });
    mpc(['stop']);
  });

  /**
   * x_post.cgi 実行用の環境(api設定とトークンは一時ファイル,API接続はstub curl)
   * @param {string} dir
   * @param {Record<string, string>} extra
   */
  function cgiEnv(dir, extra = {}) {
    const apiConf = path.join(dir, 'x_api.conf');
    if (!fs.existsSync(apiConf)) {
      fs.writeFileSync(apiConf,
        'x_oauth2_client_id="dummy_client_id"\n' +
        'x_oauth2_client_secret="dummy_client_secret"\n' +
        'x_share_hashtags="NowPlaying"\n');
    }
    const tokenFile = path.join(dir, 'x_token.conf');
    if (!fs.existsSync(tokenFile)) {
      fs.writeFileSync(tokenFile,
        `x_oauth2_access_token="VALID_ACCESS"\n` +
        `x_oauth2_refresh_token="VALID_REFRESH"\n` +
        `x_oauth2_expires_at="${Math.floor(Date.now() / 1000) + 3600}"\n`);
    }
    return {
      x_api_conf: apiConf,
      x_token_file: tokenFile,
      PATH: `${path.join(dir, 'stubbin')}:${process.env.PATH}`,
      CURL_LOG: path.join(dir, 'curl.log'),
      ...extra,
    };
  }

  test('再生中は本文とカバーを添付して投稿し,結果ページへ投稿へのリンクを出す', () => {
    ensurePlaying();
    const dir = makeDir('page');
    fs.mkdirSync(path.join(dir, 'stubbin'));
    writeStubCurl(path.join(dir, 'stubbin'));

    const body = runCgi(X_POST_CGI, cgiEnv(dir));

    expect(body).toContain('投稿しました。');
    expect(body).toContain('https://x.com/i/web/status/1760000000000000000');
    expect(body).toContain('ホームへ戻る');

    // 本文にはハッシュタグが追記され,カバー画像がmedia_idsへ添付される
    const log = fs.readFileSync(path.join(dir, 'curl.log'), 'utf8');
    expect(log).toContain('#NowPlaying');
    expect(log).toContain('media_ids');
    expect(log).toContain('/2/media/upload');
  });

  test('カバー取得に失敗しても本文のみで投稿し,結果ページに注意を添える', () => {
    ensurePlaying();
    const dir = makeDir('page');
    fs.mkdirSync(path.join(dir, 'stubbin'));
    writeStubCurl(path.join(dir, 'stubbin'));

    const body = runCgi(X_POST_CGI, cgiEnv(dir, { COVER_FAIL: '1' }));

    expect(body).toContain('投稿しました。');
    expect(body).toContain('本文のみで投稿します');

    const log = fs.readFileSync(path.join(dir, 'curl.log'), 'utf8');
    expect(log).not.toContain('/2/media/upload');
    expect(log).toContain('-d {"text":"');
  });

  test('投稿に失敗したらAPI応答を生で表示する', () => {
    ensurePlaying();
    const dir = makeDir('page');
    fs.mkdirSync(path.join(dir, 'stubbin'));
    writeStubCurl(path.join(dir, 'stubbin'));

    const body = runCgi(X_POST_CGI, cgiEnv(dir, { TWEET_FAIL: '1' }));

    expect(body).toContain('投稿に失敗しました。');
    expect(body).toContain('"tweet failed"');
    expect(body).toContain('再認可');
    expect(body).toContain('ホームへ戻る');
  });

  test('停止中は投稿を行わない', () => {
    mpc(['stop']);
    const dir = makeDir('page');
    fs.mkdirSync(path.join(dir, 'stubbin'));
    writeStubCurl(path.join(dir, 'stubbin'));

    const body = runCgi(X_POST_CGI, cgiEnv(dir));

    expect(body).toContain('再生中の曲がないため投稿しませんでした。');
    expect(fs.existsSync(path.join(dir, 'curl.log'))).toBe(false);
  });

  test('method=GETでは投稿を行わない', () => {
    ensurePlaying();
    const dir = makeDir('page');
    fs.mkdirSync(path.join(dir, 'stubbin'));
    writeStubCurl(path.join(dir, 'stubbin'));

    const body = runCgi(X_POST_CGI, { ...cgiEnv(dir), REQUEST_METHOD: 'GET' });

    expect(body).toContain('method=POST');
    expect(fs.existsSync(path.join(dir, 'curl.log'))).toBe(false);
  });

});
