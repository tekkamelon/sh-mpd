# 一定時間後または指定時刻に再生/停止する

## 結論

実装可能である。ただし MPD は予約を保持しない。CGI リクエストの中で `sleep` して待つ方式は採用しない。

第一案は、CGI が予約内容を検証したあと、ホストのワンショットスケジューラ `at` に `mpc play` / `mpc pause` / `mpc stop` を渡す方式とする。

## 前提と制約

- 既存 UI は POSIX sh の CGI であり、JavaScript 非依存を崩さない。
- 再生制御そのものは既存どおり `mpc` で足りる。足りないのは「時刻が来たら実行する側」である。
- Web サーバはレスポンス後に CGI の子プロセスを殺すことがある。`sleep ... &` や CGI 内の待ちは予約が消えるため禁止する。
- `at` のジョブはクリーンな環境で走る。`MPD_HOST` と `MPD_PORT` をジョブスクリプトへ明示的に埋め込む。
- `at` と `atd` が入り、CGI 実行ユーザが `at` を使えることが前提である。使えない環境ではページに理由を出し、黙って失敗しない。
- 毎日繰り返しは crontab の書き換えになり危険なので、初回実装の対象外とする。

## 採用する操作

許可する `mpc` サブコマンドは次だけとする。ユーザ入力をシェルコマンドとして渡さない。

| 値 | 実行 |
|---|---|
| `play` | `mpc play` |
| `pause` | `mpc pause` |
| `stop` | `mpc stop` |

`toggle` は予約時刻の状態に依存し、意図と逆になり得るため初回は入れない。

## 受け付ける時刻

2 種類だけにする。

1. 相対: 整数の分。`1` から `10080`(7日)まで。`at` へは `now + N minutes` を渡す。
2. 絶対: `HH:MM`(24時間)。日付は初回は扱わない。`at` の仕様どおり、その時刻が当日の過去なら翌日になる実装が多い。ページにその注意を書く。

検証に失敗した文字列は `at` に渡さない。正規表現の例:

- 分: `^[0-9]+$` かつ範囲チェック
- 時刻: `^([01][0-9]|2[0-3]):[0-5][0-9]$`

## 推奨構成

### `bin/schedule_mpc`

CGI から呼ぶ唯一の入口にする。サブコマンドは固定する。

```
schedule_mpc add --after MINUTES --action play|pause|stop
schedule_mpc add --at HH:MM --action play|pause|stop
schedule_mpc list
schedule_mpc cancel JOBID
```

`add` の処理:

1. 引数を検証する。
2. `command -v at` と `atd` の稼働を確認する。確認できない場合は 0 以外で終了し、理由を標準エラーに出す。
3. 実行用スクリプトを一時ファイルに書く。中身は環境変数の代入と `mpc` 1 コマンドだけにする。
4. `at -f スクリプト now + N minutes` または `at -f スクリプト HH:MM` を実行する。
5. `at` の標準エラーからジョブ番号を取り、成功メッセージを出す。
6. 一時スクリプトは `at` が読み終えたあと削除してよい。`at` はジョブを自身のスプールへコピーする。

ジョブスクリプトの形(生成物。ユーザ文字列は入れない):

```sh
#!/bin/sh
export MPD_HOST="..."
export MPD_PORT="..."
export PATH="/usr/bin:/bin"
mpc play
```

`MPD_HOST` にシェルメタ文字が混ざることは想定しない。設定値は既存の `shmpd.conf` から読み、ジョブへ書くときは英数字、`.`、`:`、`-` 以外を拒否する。

### 一覧と取消

- 一覧は `atq` を使い、本ツールが投入したジョブだけを表示する。判別のためジョブスクリプトの先頭コメントに `# sh-mpd schedule action=play when=HH:MM` を入れる。表示時は `at -c JOBID` からその行だけ抜く。
- 取消は `atrm JOBID`。JOBID は数字だけ許可する。
- 他ユーザや他用途の `at` ジョブは、コメントが無ければ一覧にも取消ボタンにも出さない。

### CGI

新規ページ `cgi-bin/schedule/schedule.cgi` を置く。`index.cgi` の既存コントロールボタンには混ぜない。ナビゲーションに Schedule へのリンクを足す。

フォームは POST のみ。

- `mode=after` と `minutes`
- `mode=at` と `clock`
- `action=play|pause|stop`
- 取消は `cancel` と `jobid`

処理後は同ページへ戻り、結果を `<pre>` か短い段落で示す。既存ページと同様、接続確認は `check_mpd_connection` を使う。

HTML は既存の `index.cgi` のヘッダ・ナビゲーション・stylesheet の読み方に合わせる。JavaScript は足さない。

## 設定

必須項目は増やさない。`MPD_HOST` と `MPD_PORT` は既存の `settings/shmpd.conf` を使う。

任意で次を足してよい。未設定なら予約機能は有効とする。

```sh
schedule_enabled="yes"
```

`no` のときはフォームを出さず、無効である旨だけ表示する。

## 採用しない案

### CGI 内の `sleep` やバックグラウンド待ち

リクエストを握る、またはレスポンス後にプロセスが消える。採用しない。

### `cron` で単発予約

分単位の単発には向かず、crontab 編集は権限と競合の問題が大きい。毎日繰り返しを別計画にするときの候補に留める。

### `systemd-run --on-active` / timer

使えるホストでは同等以上に堅いが、本プロジェクトの目標である POSIX 寄りの移植性を落とす。`at` が無い場合の代替として文書に残すだけで、初回コードパスには入れない。

### MPD のプロトコル拡張やクライアント側タイマ

MPD は壁時計の予約を保存しない。ブラウザ側タイマはタブを閉じると消える。

## エラー表示

次は区別して表示する。

- `at` または `atd` が無い
- 実行ユーザが `at` を拒否された (`at.allow` / `at.deny`)
- 時刻または分が不正
- `action` が許可リスト外
- `mpc` へ届かない(予約登録時の接続確認で落とす。実行時刻の失敗は `at` のメールまたはログに残るため、初回は追従しない)

## テスト観点

- 不正な `action`、分、時刻、JOBID は `at` を呼ばずに失敗する
- 生成スクリプトにユーザ入力のシェル構文が混ざらない
- `at` が PATH に無いとき、CGI が理由を出す
- 一覧は `# sh-mpd schedule` の付いたジョブだけを出す
- 再生中ページの既存ボタン (`toggle` など) が壊れない

Playwright で本物の `atd` は必須にしない。テスト時は PATH 先頭に偽物の `at` / `atq` / `atrm` を置き、引数と生成スクリプトを検証する。MPD 接続が必要な表示試験は、既存テストの前提に合わせる。

## 実装手順

1. `bin/schedule_mpc` を追加し、検証と `at` 呼び出しをそこに閉じる
2. 偽物の `at` で `add` / `list` / `cancel` を手で確認する
3. `cgi-bin/schedule/schedule.cgi` を追加する
4. `index.cgi` のナビゲーションにリンクを足す
5. 必要なら `schedule_enabled` を読む
6. Playwright では偽物コマンドでフォームの拒否と成功表示を見る

## 参考

- 既存の mpc 受け渡し: `cgi-bin/index.cgi` の `mpc_post`
- 設定: `cgi-bin/settings/shmpd.conf`
- `at` の時刻指定: `man at`
