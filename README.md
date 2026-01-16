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
