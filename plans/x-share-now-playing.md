# 現在再生中の曲をX(旧Twitter)で共有する機能

## 結論

可能である。

`cgi-bin/index.cgi` の Now Playing 付近に、Web Intent へのリンクを置く方式が本プロジェクト(POSIX sh + CGI、JavaScript 非依存)に最も合う。

X API(OAuth)でサーバから直接投稿する方法もあるが、アプリ登録・トークン管理・秘密情報の保管が必要になり、sh-MPD の構成には重い。第一案は Intent リンクとする。

## 前提と制約

- ブラウザ上で X にログインしている利用者が、投稿画面を開いて自分で送信する。
- CGI 側は投稿本文を組み立てて URL を生成するだけであり、投稿そのものは行わない。
- Intent では画像(カバーアート)を添付できない。カバー URL を本文に含めることは可能だが、X 側のカード表示は公開 URL に依存する。LAN 内の `img_server` は外部から見えないことが多い。
- 再生中でない場合はリンクを出さない、または無効化する。
- 曲名・アーティストに `&` `#` 空白 日本語などが含まれるため、クエリは必ず URL エンコードする。現状リポジトリに `urlencode` は無く、`urldecode` のみ存在する。

## 推奨方式: Web Intent

公式の投稿画面を開く URL:

```
https://twitter.com/intent/tweet?text=<urlencoded>
```

`x.com` でも動くが、互換性のため `twitter.com` を使う。

任意パラメータ:

| パラメータ | 用途 |
|---|---|
| `text` | 投稿本文 |
| `hashtags` | カンマ区切り。`#` は付けない |
| `url` | 末尾に付ける URL |
| `via` | メンション用アカウント名 |

参考: [Tweet Button / Web Intents](https://developer.x.com/en/docs/twitter-for-websites/tweet-button/guides/web-intent)

## 本文の組み立て

`mpc current` のフォーマット文字列でタグを取る。

例:

```sh
mpc current -f '%artist% - %title% (%album%)'
```

停止中は空文字になる。空なら共有リンクを出さない。

推奨本文の例:

```
Now Playing: Artist - Title (Album)
#NowPlaying
```

ハッシュタグは `text` に直接書いてもよい。`hashtags=NowPlaying` に分けるとエンコードが単純になる。

ラジオ配信など `%artist%` が空の場合は `%file%` や `%name%` へフォールバックする。

## URL エンコード

POSIX sh で実装する。新規コマンド `bin/urlencode` を置き、`urldecode` と対にするのがよい。

要件:

- 英数字と `-` `_` `.` `~` はそのまま
- 空白は `%20` (Intent では `+` より `%20` の方が無難)
- それ以外は UTF-8 の各バイトを `%HH`
- `printf` とループで実装し、bash 固有構文は使わない

生成例:

```sh
share_text="$(mpc current -f 'Now Playing: %artist% - %title% (%album%)')"
encoded="$(printf '%s' "${share_text}" | urlencode)"
share_url="https://twitter.com/intent/tweet?text=${encoded}&hashtags=NowPlaying"
```

HTML 属性に入れるため、`&` は `&amp;` にする。

```html
<a href="${share_url_html}" target="_blank" rel="noopener noreferrer">Share on X</a>
```

`target="_blank"` は任意。同一タブでもよい。

## index.cgi への組み込み

Now Playing セクション(`<h2>Now Playing</h2>` の直後、カバー画像の前後)にリンクまたはボタンを追加する。

方針:

1. 関数 `x_share_url` を追加し、再生中なら Intent URL、停止中なら空を返す。
2. 空でなければ `<a>` を出力する。
3. 既存の Control Panel の `GET` ボタン群には混ぜない。共有は MPD 操作ではないため、別リンクにする。

見た目は既存の `.icon` とボタンクラスに合わせる。CSS の大幅変更は不要。

## 設定

必須ではない。必要なら `settings/shmpd.conf` に任意項目を足す。

例:

```sh
x_share_enabled="yes"
x_share_hashtags="NowPlaying"
x_share_template="Now Playing: %artist% - %title% (%album%)"
```

未設定時は有効・上記テンプレートをデフォルトとする。

## 採用しない案

### X API v2 で直接投稿

- アプリ登録、OAuth 2.0、リフレッシュトークンが必要
- CGI から秘密鍵を扱うのはリスクが大きい
- 画像投稿はさらに media upload が必要

将来の拡張としては残せるが、初回実装の対象外とする。

### JavaScript の Web Share API

- `navigator.share()` は OS の共有シートを開く
- 本 UI は JS 非依存が基本なので使わない

## テスト観点

- 再生中: リンクがあり、クリックで X の投稿画面が開く(ログイン済みなら本文が入る)
- 停止中: リンクが出ない
- 曲名に `&` `?` `#` 空白 日本語がある場合でも URL が壊れない
- アーティスト空(ラジオ等)でも本文が空にならない
- 既存の再生操作・検索・カバー表示が壊れない

Playwright では外部の X へは行かず、`a[href*="twitter.com/intent/tweet"]` の有無と `href` のエンコードを検証する。

## 実装手順(案)

1. `bin/urlencode` を追加し、単体でエンコード結果を確認する
2. `index.cgi` に `x_share_url` 相当の処理と Now Playing 内リンクを追加する
3. 必要なら `shmpd.conf` にテンプレートとハッシュタグを足す
4. Playwright でリンク生成を検証する

## 参考コマンド

```sh
mpc current -f '%artist%\t%title%\t%album%\t%file%\t%name%'
mpc status
```
