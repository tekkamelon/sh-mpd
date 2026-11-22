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
//   それ以外(カバー画像の取得)  -> COVER_RESPONSE を返す(COVER_FAIL=1 なら失敗)
function writeStubCurl(dir) {
  const script = `#!/bin/sh
printf '%s\\n' "\${*}" >> "\${CURL_LOG:-/dev/null}"

for arg in "\${@}" ; do
  case "\${arg}" in
    https://api.x.com/2/oauth2/token)
      printf '%s' "\${TOKEN_RESPONSE:-{\\"token_type\\":\\"bearer\\",\\"expires_in\\":7200,\\"access_token\\":\\"ROT_ACCESS\\",\\"refresh_token\\":\\"ROT_REFRESH\\"}}"
      exit 0
      ;;
    https://api.x.com/2/media/upload)
      if [ -n "\${UPLOAD_FAIL:-}" ] ; then
        printf '%s' "{\\"errors\\":[{\\"message\\":\\"upload failed\\"}]}"
        exit 1
      fi
      printf '%s' "\${UPLOAD_RESPONSE:-{\\"data\\":{\\"id\\":\\"MEDIA123\\",\\"media_key\\":\\"3_123\\"}}}"
      exit 0
      ;;
    https://api.x.com/2/tweets)
      if [ -n "\${TWEET_FAIL:-}" ] ; then
        printf '%s' "{\\"errors\\":[{\\"message\\":\\"tweet failed\\"}]}"
        exit 1
      fi
      printf '%s' "\${TWEET_RESPONSE:-{\\"data\\":{\\"id\\":\\"1760000000000000000\\",\\"text\\":\\"ok\\"}}}"
      exit 0
      ;;
  esac
done

if [ -n "\${COVER_FAIL:-}" ] ; then
  exit 22
fi
printf '%s' "\${COVER_RESPONSE:-FAKEJPEGBYTES}"
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
