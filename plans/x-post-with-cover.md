# X投稿へのカバー画像添付とコード簡素化

## 背景

- 現行のX共有はWeb Intentリンク(plans/x-share-now-playing.md の実装)。
- Intentでは画像を添付できないため、index.cgi に表示中のカバー画像を添付するには
  X API によるサーバ側投稿が必要になる。
- 所有者指示(2026-11-23): 投稿にカバー画像を添付できるようにすること。
  併せてコードを簡素化すること。

## 認証方式の決定: OAuth 2.0 (Authorization Code + PKCE)

当初案だったOAuth 1.0aは採用しない。理由(2026-11 時点の一次情報):

1. v2メディアアップロード `POST /2/media/upload` の公式認証は
   OAuth 2.0ユーザートークン(`media.write`スコープ)のみ。
   OAuth 1.0aでの動作報告は「Bad Authentication data (code 215)」等の失敗例のみ。
   旧来のOAuth 1.0a用 `POST /1.1/media/upload.json` は2025-03-31に廃止済み。
2. X公式見解はOAuth 1.0aを「レガシー。OAuth 2.0への移行を強く推奨。将来的に廃止
   (時期未告知)」。新規アプリではOAuth 1.0a鍵の発行UIが無い場合がある。
3. 投稿 `POST /2/tweets` 自体は現在もOAuth 1.0aを受けるが
   (公式のv2認証対応表で対応) 、メディア添付という要件を満たせない。

 OAuth 2.0ならBearerヘッダを付けるだけで良く、リクエストごとの署名は不要。
 複雑さはトークンのライフサイクル(初回同意と更新)に移る。

## 方式

- 投稿: `POST https://api.x.com/2/tweets` (JSON, Bearer)
- 画像: `POST https://api.x.com/2/media/upload` (multipart, Bearer)
  - 画像は `media_category=tweet_image` (JPG/PNG/GIF/WEBP, 5MBまで)
  - 応答は `{"data":{"id":"..."}}`。この `id` を投稿の `media.media_ids` へ渡す。
- スコープ: `tweet.read users.read tweet.write media.write offline.access`

## 構成(変更一覧)

| 要素 | 種別 | 内容 |
| --- | --- | --- |
| bin/x_share_text | 新規 | 共有本文の生成(mpc current 1回、sep分割、段階フォールバック) |
| bin/coverart_url | 新規 | カバー画像URLの生成(現在曲のディレクトリ + img_server) |
| bin/x_oauth2 | 新規 | 認可URL生成/コード交換/トークン更新(ホスト側ツール) |
| bin/x_post | 新規 | API投稿クライアント(トークン更新/アップロード/投稿) |
| cgi-bin/x_post.cgi | 新規 | 投稿フォームの受付と結果ページ |
| cgi-bin/index.cgi | 変更 | x_share_url/coverart を bin へ委譲して簡素化 |
| cgi-bin/settings/x_api.conf.example | 新規 | アプリ設定例(client_id/client_secret等) |
| tools/apache-shmpd.conf | 変更 | settings配下の .conf への直接アクセスを拒否 |
| .gitignore | 変更 | x_api.conf と x_token.conf を除外 |
| tools/Dockerfile | 変更 | curl を追加 |
| tests/x-post.spec.js | 新規 | CGI直実行 + stub curl による検証 |
| plans/(本書) | 新規 | 設計文書 |

## 設計

### 設定とトークン

`cgi-bin/settings/x_api.conf` (git管理外、exampleを同梱。Apache設定で
直接取得を拒否する):

```sh
# 表示設定の上書き(未定義ならindex.cgiの既定値を使う)
x_share_enabled="yes"
x_share_hashtags="NowPlaying"
x_share_template="%artist% - %title% (%album%)"

# OAuth 2.0アプリ資格(Developer PortalのUser authentication settings)
x_oauth2_client_id=""
x_oauth2_client_secret=""
x_redirect_uri="http://127.0.0.1:18937/callback"
```

`cgi-bin/settings/x_token.conf` (git管理外、bin/x_post が更新する):

```sh
x_oauth2_access_token="..."
x_oauth2_refresh_token="..."
x_oauth2_expires_at="0"    # Unix秒。date +%s と比較
```

- `shmpd.conf` は server_setting.cgi の保存で5変数分だけ書き直されるため、
  X関連の設定はこの別ファイルに置く。
- トークンは返却のたびにローテーションする(更新の応答には新しい
  refresh_tokenが入る)。更新は一時ファイル+mvで原子的に行い、
  更新中の並走を防ぐため mkdir ベースのロック(残骸は作成時刻で期限切れ)
  を使う。トークンファイルのパスは環境変数 `x_token_file` で差し替え可能にし、
  テストは一時ファイルへ向ける。
- 両方ともコミットしない。実運用は rei 上のgit管理外ファイルに置く。
  トークンファイルはCGI実行ユーザ(shmpd, uid 1000)が書ける必要がある。
  rei 側の tekkamelon は uid 1000 なので所有権は最初から揃う。

### Apache (既存穴の塞ぎを兼ねる)

`Alias /cgi-bin/` 配下は今も `Require all granted` のため、
`/cgi-bin/settings/shmpd.conf` がLANから素のテキストとして読める。
settings の Directory ブロックへ `.conf` だけを拒否する FilesMatch を追加する
(`.cgi` の設定UIは動いたままにする):

```apache
<Directory ".../sh-mpd/cgi-bin/settings/">
    <FilesMatch "\.conf">
        Require all denied
    </FilesMatch>
</Directory>
```

### OAuth 2.0 フロー(実装レシピ)

初回の同意(所有者がホスト上で一度だけ実行。bin/x_oauth2):

1. code_verifier と state を乱数で生成
2. code_challenge = BASE64URL(SHA256(verifier))。opensslはこの時だけ使う
   (ホスト側で実行するためコンテナへの追加は不要)
3. 認可URLを表示:
   `https://x.com/i/oauth2/authorize?response_type=code&client_id=...&redirect_uri=...&state=...&code_challenge=...&code_challenge_method=S256&scope=tweet.read%20users.read%20tweet.write%20media.write%20offline.access`
4. 所有者がブラウザで認可すると redirect_uri へ `?code=...&state=...` が
   戻る(ローカルなので到達先は無くてよい。アドレス欄からURLを写す)。
   ペーストされたURL(またはcode)を受け取り state を検証して交換:
   `POST https://api.x.com/2/oauth2/token`
   `grant_type=authorization_code, code, redirect_uri, client_id, code_verifier`
   (confidential client なので client_secret も送る)
5. 応答の access_token / refresh_token / expires_in を x_token.conf へ保存

投稿のたび(bin/x_post):

1. access_token が期限切れ(expires_at <= now)なら更新:
   `POST /2/oauth2/token` `grant_type=refresh_token, refresh_token, client_id`
   応答の新しいトークン群をロック下で x_token.conf へ書き戻す。
   更新に失敗した場合は投稿を行わず「再認可が必要」として結果へ出す。
2. 画像(multipart):
   `curl -sS -X POST -H "Authorization: Bearer ..." -F "media_category=tweet_image" -F "media=@file;type=image/jpeg" https://api.x.com/2/media/upload`
   応答から `data.id` を sed で抽出。
3. 投稿(JSON):
   `curl -sS -X POST -H "Authorization: Bearer ..." -H "Content-type: application/json" -d '{"text":"...","media":{"media_ids":["<id>"]}}' https://api.x.com/2/tweets`
   応答の `data.id` を結果ページのリンクへ使う
   (`https://x.com/i/web/status/<id>`)。

### UI (index.cgi の Now Playing)

| 状態 | 表示 |
| --- | --- |
| 停止中 | 何も出さない(従来どおり) |
| 再生中 + x_api.conf無し/未設定 | 従来のIntentリンク "Share on X" |
| 再生中 + x_api.conf設定済 | `x_post.cgi` へのフォームボタン "Post to X" |

- API設定済みのときIntentリンクは出さない(投稿はトークンのアカウントから
  行われるため、両方を出すと混乱する)。
- トークンの期限切れはこの段階では判定しない。押した結果ページに
  「再認可が必要」と表示して bin/x_oauth2 の手順を案内する。

### 本文とハッシュタグ

- `bin/x_share_text` が本文を生成する。index.cgi(Intent)と
  x_post.cgi(API)の両方がこれを使い、生成源を1つにする。
- ハッシュタグは本文に含めない。Intentは `hashtags=` クエリ、
  APIは x_post.cgi が本文末尾へ ` #tag` を追記する
  (カンマ区切りは空白区切りの #付きに変換する)。

### bin/x_post の引数

```
x_post -t <本文> [-i <カバーURL>]
```

- 資格情報とトークンファイルは環境変数(x_oauth2_* と x_token_file)から取る。
  client_id/secret が未設定なら exit 1。
- `-i` 指定時: curlで取得し media upload へ。拡張子で MIME を判定
  (既定 image/jpeg)。応答から `data.id` を抽出し `media.media_ids` へ入れる。
- カバー取得に失敗した場合は本文のみで投稿し、結果に注意を表示する。
- media upload 自体が失敗した場合は投稿せず exit 1。
- 成功時は投稿応答本文を標準出力、失敗時はAPI応答本文を標準エラーへ出す。
  呼び出し側が結果ページに生で表示し、原因(401/403/429)を隠さない。

### cgi-bin/x_post.cgi

- `settings/shmpd.conf` と `settings/x_api.conf` を読み、
  本文(`bin/x_share_text`)とカバーURL(`bin/coverart_url`)を組み立てて
  `bin/x_post` を呼ぶ。
- 停止中(本文が空)はエラーページ(投稿を行わない)。
- フォームは method="POST" とする(外部への副作用であり、既存のMPD操作
  ボタンとは性質が違う。index.cgi は既にPOST本文を読み捨てている)。
- 結果ページ: 成功時は投稿IDへのリンクと index.cgi への戻るリンク、
  失敗時はエラーと応答本文。stylesheetは既存に合わせる。

## 制約と注意

- 本番コンテナに curl が無い。`tools/Dockerfile` へ追加する。
  base64/coreutils は既にある。openssl は初回同意時のみホスト側で使うため
  コンテナへの追加は不要。main マージ後のデプロイ時にイメージ再ビルドが必要
  (shmpd-cgi-test-harness の手順。マージまでは worktree からのビルドで検証)。
- 投稿本文はJSON。本文中の `"` と `\` はエスケープし、制御文字(0x00-0x1F)は
  除去する。UTF-8の多バイト文字はそのまま通す。
- Free tier の投稿数上限(月次)に注意。失敗応答は結果ページに生表示する。
- `bin/coverart_url` は停止中(mpc current が空)は空を出力する。
  現行 index.cgi の coverart は停止中に不正なURLを出すが、
  favicon用としては無害なため従来動作を踏襲してもよい(img/onerrorで消える)。
- トークンが有効なのは投稿アカウントのものだけ。共有系の既存テストは
  x_api.conf を置かない限り従来のIntent経路のまま影響を受けない。

## テスト観点

1. 回帰: `x_api.conf` 無しで x-share/directory/index/path-based の各specが
   従来どおり全緑(Intentリンクの既存テストを壊さない)。
2. index.cgi 出し分け: x_api.conf 有り(ダミー資格)ではフォームボタンが出て
   Intentリンクが消える。停止中はどちらも出ない(CGI直実行で検証)。
3. bin/x_share_text: 5分岐(全タグ/アルバム欠/アーティスト欠/タイトル欠/全欠)
   を独立検算と突き合わせ。停止中は空。
4. bin/x_oauth2: PKCEの code_challenge が BASE64URL(SHA256(verifier)) と
   一致することを node crypto で独立検算(S256の実装検証)。
5. bin/x_post: PATH先頭へ stub curl を置き、トークンファイルへ一時ファイルを
   指して検証する。
   - 期限切れトークン → まず /2/oauth2/token の更新呼び出し、
     新トークンが一時ファイルへ原子書き込みされる(ローテーション反映)
   - Bearerヘッダの形式
   - media upload の -F 引数(ファイル実体が取得した画像であること、
     media_category)と data.id の抽出
   - /2/tweets のJSON本文(text, media_ids)と data.id の抽出
   - client_id 未設定 → exit 1
   - カバー取得失敗 → 本文のみ投稿(アップロード呼び出しが無い)
   - media upload 失敗 → 投稿呼び出しが無い
6. x_post.cgi: 成功/失敗/停止中の結果ページ(CGI直実行)。
7. Apache: settings 配下の .conf が 403 になること、settings.cgi は
   動いたままなこと(ハーネスで)。

## 実装順序

1. `bin/x_share_text` + `bin/coverart_url` を切り出し、index.cgi を簡素化する。
   この時点で既存specが全緑であること(表示の挙動は変わらない)。
2. `bin/x_oauth2` を実装する(PKCE検算テスト込み)。
3. `bin/x_post` を実装し、stub テスト(x-post.spec.js)を作る。
4. `x_post.cgi` と index.cgi の出し分けを実装する。
5. Apache設定, Dockerfile, .gitignore, README を更新して仕上げる。

## 所有者向けの初回設定(実機での動作確認手順)

コードはstubで検証するため、実投稿の確認には以下が必要(PR本文にも同じ手順を
載せる):

1. X Developer Portal でプロジェクト内にアプリを作成
2. App settings の User authentication settings を設定
   (App permissions: Read and write, callback URL に `http://127.0.0.1:18937/callback`)
3. `cgi-bin/settings/x_api.conf` へ client_id / client_secret を記入
4. ホスト上で `bin/x_oauth2 setup` の表示するURLで認可し、
   戻りURLをペーストしてトークン取得
5. 再生中に index.cgi の "Post to X" で実投稿を確認

## 参考

- メディアアップロード(v2): https://docs.x.com/x-api/media/upload-media
- メディアの上限: https://docs.x.com/x-api/media/introduction
- 投稿: https://docs.x.com/x-api/posts/creation-of-a-post
- OAuth 2.0 (PKCE): https://docs.x.com/resources/fundamentals/authentication/oauth-2-0/authorization-code
- v2認証対応表: https://docs.x.com/fundamentals/authentication/guides/v2-authentication-mapping
