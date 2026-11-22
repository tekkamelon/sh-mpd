# X投稿へのカバー画像添付とコード簡素化

## 背景

- 現行のX共有はWeb Intentリンク(plans/x-share-now-playing.md の実装)。
- Intentでは画像を添付できないため、index.cgi に表示中のカバー画像を添付するには
  X API によるサーバ側投稿が必要になる。
- 所有者指示(2026-11-23): 投稿にカバー画像を添付できるようにすること。
  併せてコードを簡素化すること。

## 方式: X API v2 + v1.1 media upload (OAuth 1.0a user context)

- 投稿: `POST https://api.twitter.com/2/tweets` (JSON本文)
- 画像: `POST https://upload.twitter.com/1.1/media/upload.json` (multipart/form-data)
- 認証: OAuth 1.0a (HMAC-SHA1署名)。X API Free tier でも
  投稿とメディアアップロードは利用可能。資格情報は4組:
  consumer key/secret と access token/secret。

## 構成(変更一覧)

| 要素 | 種別 | 内容 |
| --- | --- | --- |
| bin/x_share_text | 新規 | 共有本文の生成(mpc current 1回、sep分割、段階フォールバック) |
| bin/coverart_url | 新規 | カバー画像URLの生成(現在曲のディレクトリ + img_server) |
| bin/x_post | 新規 | API投稿クライアント(署名/アップロード/投稿) |
| cgi-bin/x_post.cgi | 新規 | 投稿フォームの受付と結果ページ |
| cgi-bin/index.cgi | 変更 | x_share_url/coverart を bin へ委譲して簡素化 |
| cgi-bin/settings/x_api.conf.example | 新規 | 設定例(実ファイルはgit管理外) |
| .gitignore | 変更 | cgi-bin/settings/x_api.conf を除外 |
| tools/Dockerfile | 変更 | curl openssl を追加 |
| tests/x-post.spec.js | 新規 | CGI直実行 + stub curl による検証 |
| plans/(本書) | 新規 | 設計文書 |

## 設計

### 設定ファイル

`cgi-bin/settings/x_api.conf` (git管理外、`x_api.conf.example` を同梱):

```sh
# 上書き可能な表示設定(未定義ならindex.cgiの既定値を使う)
x_share_enabled="yes"
x_share_hashtags="NowPlaying"
x_share_template="%artist% - %title% (%album%)"

# API投稿の資格情報(未設定ならWeb Intentへフォールバック)
x_api_consumer_key=""
x_api_consumer_secret=""
x_api_access_token=""
x_api_access_token_secret=""
```

- `shmpd.conf` は server_setting.cgi の保存で5変数分だけ書き直されるため、
  X関連の設定はこの別ファイルに置く。既存の `x_share_*` を shmpd.conf へ
  手で追記する運用は本機能で廃止する(既定値はコード側が持つ)。
- ファイルが無い、または `x_api_*` が未設定(空) → Intentフォールバック。

### UI (index.cgi の Now Playing)

| 状態 | 表示 |
| --- | --- |
| 停止中 | 何も出さない(従来どおり) |
| 再生中 + API未設定 | 従来のIntentリンク "Share on X" |
| 再生中 + API設定済 | `x_post.cgi` へのフォームボタン "Post to X" |

- API設定済みのときIntentリンクは出さない(投稿はトークンのアカウントから
  行われるため、両方を出すと混乱する)。

### 本文とハッシュタグ

- `bin/x_share_text` が本文を生成する。index.cgi(Intent)と
  x_post.cgi(API)の両方がこれを使い、生成源を1つにする。
- ハッシュタグは本文に含めない。Intentは `hashtags=` クエリ、
  APIは x_post.cgi が本文末尾へ ` #tag` を追記する
  (カンマ区切りは空白区切りの #付きに変換する)。

### OAuth 1.0a 署名(実装レシピ)

- 署名対象パラメータは oauth_* の6つ固定(アルファベット順に並べればよい):
  `oauth_consumer_key, oauth_nonce, oauth_signature_method, oauth_timestamp,
  oauth_token, oauth_version`
- JSON本文とmultipart本文は署名対象外(form-urlencodedのみが対象のため)。
- 手順:
  1. `nonce`: `head -c 16 /dev/urandom | od -An -tx1 | tr -d ' \n'`
  2. `timestamp`: `date +%s`
  3. 値をすべて `urlencode` でエンコードし `k=v` を `&` で結合
  4. base string = `POST&<enc(endpoint URL)>&<enc(結合したパラメータ群)>`
  5. signing key = `<enc(consumer_secret)>&<enc(token_secret)>`
     (opensslへ渡す際はエンコード済み文字列をそのまま使う)
  6. `printf '%s' "${base_string}" | openssl dgst -sha1 -hmac "${signing_key}" -binary | openssl base64 | tr -d '\n'`
  7. ヘッダは `Authorization: OAuth oauth_consumer_key="<enc>", ..., oauth_signature="<enc(base64)>"`

### bin/x_post の引数

```
x_post -t <本文> [-i <カバーURL>]
```

- 資格情報は環境変数(x_api_* 4変数)から取る。不足なら exit 1。
- `-i` 指定時: curl で取得し media upload へ `-F media=@file;type=image/jpeg`
  (拡張子で MIME を判定、既定 image/jpeg)。応答から `media_id_string` を
  sed で抽出し、/2/tweets の `media.media_ids` へ入れる。
- カバー取得に失敗した場合は本文のみで投稿し、結果に注意を表示する
  (添付を必須とはしない)。
- media upload 自体が失敗した場合(資格不良を含む)は投稿せず exit 1。
- 成功時は応答本文(`data.id`)を標準出力へ出す。失敗時は応答本文を
  標準エラーへ出す。呼び出し側が結果ページに生で表示し、原因
  (401 署名不良 / 429 制限)を隠さない。

### cgi-bin/x_post.cgi

- `settings/shmpd.conf` と `settings/x_api.conf` を読み、
  本文(`bin/x_share_text`)とカバーURL(`bin/coverart_url`)を組み立てて
  `bin/x_post` を呼ぶ。
- 停止中(本文が空)はエラーページ(投稿を行わない)。
- 結果ページ: 成功時は投稿IDと index.cgi への戻るリンク、
  失敗時はエラーと応答本文。stylesheetは既存に合わせる。
- フォームのmethodは実装に任せる(既存ボタンと同じGETでも、
  外部副作用であることを示すPOSTでもよい。index.cgi は既に
  POST本文を読み捨てているためどちらも動く)。

## 制約と注意

- 本番コンテナ(Debian 13 slim)に curl/openssl が無い。
  `tools/Dockerfile` の apt-get へ `curl openssl` を追加する必要がある。
  main マージ後のデプロイ時にイメージ再ビルドが必要
  (shmpd-cgi-test-harness の手順。マージまでは worktree からのビルドで検証)。
- POST /2/tweets の本文はJSON。本文中の `"` と `\` はエスケージし、
  制御文字(0x00-0x1F)は除去する。UTF-8の多バイト文字はそのまま通す。
- Free tier の投稿数上限(月次)がある。失敗応答は結果ページに生表示し、
  原因を隠さない。
- 資格情報はコミットしない。example は空欄で、実運用は rei 上の
  git管理外ファイルに置く。
- `bin/coverart_url` は停止中(mpc current が空)は空を出力する。
  現行 index.cgi の coverart は停止中に不正なURLを出すが、
  favicon用としては無害なため従来動作を踏襲してもよい(img/onerrorで消える)。

## テスト観点

1. 回帰: `x-api.conf` 無しで x-share/directory/index/path-based の各specが
   従来どおり全緑(Intentリンクの既存テストを壊さない)。
2. index.cgi 出し分け: x_api.conf 有り(ダミー資格)ではフォームボタンが出て
   Intentリンクが消える。停止中はどちらも出ない(CGI直実行で検証)。
3. bin/x_share_text: 5分岐(全タグ/アルバム欠/アーティスト欠/タイトル欠/全欠)
   を独立検算と突き合わせ。停止中は空。
4. bin/x_post: PATH先頭へ stub curl を置いて検証する。
   - `Authorization: OAuth` ヘッダの形式(6パラメータと署名の存在)
   - 署名の正しさ: stub が記録した nonce/timestamp/consumer_key 等から
     node の `crypto` で独立に署名を再計算し、stub 記録の署名と一致比較
   - media upload の `-F` 引数(ファイル実体が取得した画像であること)
   - /2/tweets の JSON本文(text, media_ids)
   - 資格情報なし → exit 1
   - カバー取得失敗 → 本文のみ投稿
   - media upload 失敗 → 投稿呼び出しが無い
5. x_post.cgi: 成功/失敗の結果ページ(CGI直実行)。

## 実装順序

1. `bin/x_share_text` + `bin/coverart_url` を切り出し、index.cgi を簡素化する。
   この時点で既存specが全緑であること(表示の挙動は変わらない)。
2. `bin/x_post` を実装し、stub テスト(x-post.spec.js)を作る。
3. `x_post.cgi` と index.cgi の出し分けを実装する。
4. Dockerfile, .gitignore, README を更新して仕上げる。

## 参考

- POST /2/tweets: https://docs.x.com/x-api/posts/creation-of-a-post
- media upload: https://docs.x.com/resources/fundamentals/media-upload
- 認証: https://docs.x.com/resources/fundamentals/authentication/oauth-1-0a
