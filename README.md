# sh-mpd

webブラウザ上からmpdを操作できるCGIシェルスクリプト

## 開発の目標

### 高い移植性

- シェル固有の拡張機能の使用を廃し,様々なPOSIX準拠環境での動作を可能にする

- 可能な限りPOSIX準拠のコマンドを使用

#### 開発の動機など

- https://scrapbox.io/mpd/sh-MPD

### 低リソース

- ホスト,クライアント側共に少ないリソースで利用可能

### 動作環境

#### 動作するシェル

- bash ver. 5.1.4

- dash ver. 0.5.11

- mksh ver. 59c-9+b2

- ksh ver. 93u+ 2012-08-01

- yash ver. 2.50

## インストール 

- 各種cgiを実行可能なwebサーバーをセットアップ(ここでは割愛)

```sh
# 必要なソフトのインストール

# debian系
sudo apt install mpc mpd

# arch系
sudo pacman -S mpc mpd

# fedora系
sudo dnf install mpc mpd

# centos系
sudo yum install mpc mpd

# githubよりclone
git clone https://github.com/tekkamelon/sh-mpd

# cgi-bin/をwebサーバーで設定されたディレクトリにコピー
sudo cp -r sh-mpd/cgi-bin /usr/lib/ # ※一例

#  各cgiファイルに実行権限を付与
find /usr/lib/cgi-bin -type f -name '*.cgi' -exec chmod 755 \{\} \;
```

## 貢献

バグ報告や機能リクエスト,プルリクエストを歓迎いたします.GitHubのIssueまたはPull Requestよりお寄せください

## カバーアートの表示

- ファイル名を"Folder.jpg"とした画像ファイルを用意

- "Folder.jpg"を各アルバムの音楽ファイルの入ったディレクトリに配置

- 各種webサーバーでmpd.confの"music_directory"以下をホスティング,direcroty listingを行う

```sh
# python3でホスティングする例
cd # mpd.confの"music_directory"
python3 -m http.server 8080 # ポート番号は例
```

- "Server setting"で"cover art host"を設定（例: http://localhost:8080/）

## X共有機能

- 再生中にトップページの"Now Playing"欄へ共有用の導線を表示(停止中は表示しない)
- 本文は`アーティスト名 - タイトル名 (アルバム名)`の形式,末尾にハッシュタグ`#NowPlaying`を付与
- アーティスト名等が無い場合(Webラジオ等)は取得できたタグやストリーム名で代替

### Web Intent による共有(既定)

- X APIの設定が無いときは"Share on X"リンクを表示する
- リンクを開くとXの投稿画面が開き,再生中の曲名等が本文に入る(投稿自体は手動)

### API投稿とカバー画像の添付(任意)

`cgi-bin/settings/x_api.conf`へOAuth 2.0アプリ資格を記入すると,"Share on X"リンクの代わりに
"Post to X"ボタンを表示する。ボタンを押すとサーバからX API v2で投稿を行い,再生中の曲の
カバー画像(`Folder.jpg`)を添付する。

- 認証はOAuth 2.0 (Authorization Code + PKCE)。スコープは`tweet.write`と`media.write`を含む
- トークンは`cgi-bin/settings/x_token.conf`へ自動保存され,期限切れのたびに自動更新される
- カバー画像の取得に失敗したときは本文のみで投稿し,結果ページに注意を表示する
- 投稿に失敗したときは結果ページにAPI応答を生で表示し,原因(401/403/429等)を隠さない

設定とトークンはgit管理外。本リポジトリ同梱のApache設定(`tools/apache-shmpd.conf`)により,
`cgi-bin/settings/`配下の`.conf`への直接アクセスは403になる。

#### 初回設定手順

1. [X Developer Portal](https://developer.x.com/)でプロジェクトとアプリを作成する
2. App settings の User authentication settings を設定する
    - App permissions: Read and write
    - Callback URI / Redirect URL: `http://127.0.0.1:18937/callback`
3. `cgi-bin/settings/x_api.conf.example`を`cgi-bin/settings/x_api.conf`へ複製し,
   `x_oauth2_client_id`と`x_oauth2_client_secret`を記入する
4. ホスト上で`bin/x_oauth2 setup`を実行し,表示されたURLをブラウザで開いて認可する
5. 認可後のリダイレクト先URL(アドレス欄)をコピーして次へ渡す
    ```sh
    bin/x_oauth2 exchange '<リダイレクト先のURL>'
    ```
6. 再生中にトップページの"Post to X"を押して実投稿を確認する

トークンの更新に失敗したとき(再認可が必要なとき)は,再度`bin/x_oauth2 setup`からやり直す。

### 設定(未設定時は既定値)

`shmpd.conf`と`x_api.conf`のどちらにも書ける。設定画面("Server settings")の保存は
`shmpd.conf`を書き戻すため,これらの項目は`x_api.conf`側へ置くことを推奨する。

```sh
x_share_enabled="yes" # "yes"以外で無効
x_share_hashtags="NowPlaying" # 空文字でハッシュタグ無し(`#`は付けない)
x_share_template="%artist% - %title% (%album%)" # アーティスト名,タイトル名,アルバム名が揃っている場合の本文(`mpc current -f`の書式)
```

## スケジュール機能

- 指定時刻に再生/一時停止/停止を行う予約機能
- トップページのメニューから"Schedule"を開いて使用
- 内部ではホストの`at`/`atd`を使用(`at`,`atq`,`atrm`コマンドと`atd`の稼働が必須)
- `at`が無い環境では予約一覧の取得に失敗した旨を表示

### 使用方法

1. "Reserve"欄で次のいずれかを入力し,"Action"(`play`/`pause`/`stop`)を選んで"Reserve"を押す
    - `Minutes (1-10080)`: 何分後に実行するか(例: `30`で30分後,上限は7日=10080分)
    - `Time (HH:MM)`: 何時に実行するか(例: `21:30`,24時間表記)
        - 過去の時刻は翌日の同時刻扱い(`at`の仕様)
        - 基準時刻は"Reservations"欄の"現在時刻"(サーバー側の時刻,タイムゾーンに注意)
2. "Reservations"欄で予約一覧を確認
3. 取り消す場合は各予約の"Cancel"を押す

### 設定(cgi-bin/settings/shmpd.conf,未設定時は有効)

```sh
schedule_enabled="yes" # "yes"以外で無効(無効時はフォームを表示しない)
```

## トラブルシューティング

### css,ホスト名の変更が出来ない場合(apache2)

```sh
# apache2の実行ユーザーを確認
cat /etc/apache2/envvars | grep -e "^export APACHE_RUN_USER" -e "^export APACHE_RUN_GROUP"

# 実行結果(例)
export APACHE_RUN_USER=www-data
export APACHE_RUN_GROUP=www-data

# ホスティングしているディレクトリに移動
cd /"YOUR_DIRECTORY"/cgi-bin/

# "APACHE_RUN_USER","APACHE_RUN_GROUP"に合わせてディレクトリの所有ユーザー,グループを変更
sudo chown www-data:www-data settings/
```

### css,ホスト名の変更が出来ない場合(nginx)

```sh
# nginxの実行ユーザーを確認
grep user /etc/nginx/nginx.conf

# 実行結果(例)
user nginx;

# ホスティングしているディレクトリに移動
cd /"YOUR_DIRECTORY"/cgi-bin/

# 実行ユーザーに合わせてディレクトリの所有ユーザー,グループを変更
sudo chown nginx:nginx settings/
```

## 引用元

- urldecode

	- https://github.com/ShellShoccar-jpn/misc-tools/blob/master/urldecode

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。詳細はLICENSEファイルを参照してください。
