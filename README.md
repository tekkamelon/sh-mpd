# sh-mpd

webブラウザ上からmpdを操作できるCGIシェルスクリプト

## インストール 

- 各種cgiを実行可能なwebサーバーをセットアップ(ここでは割愛)

```sh
# 必要なソフトのインストール

# debian系
$ sudo apt install mpc mpd

# arch系
$ sudo pacman -S mpc mpd

# githubよりclone
$ git clone https://github.com/tekkamelon/sh-mpd

# "urldecode"コマンドに実行権限を付与
$ chmod 755 sh-mpd/urldecode

# "urldecode"をパスの通ったディレクトリに配置 
$ sudo cp sh-mpd/urldecode /usr/local/bin # ※一例

# cgi-bin/をwebサーバーで設定されたディレクトリにコピー
$ sudo cp -r sh-mpd/cgi-bin /usr/lib/ # ※一例

# 上記でコピーしたディレクトリに移動
$ cd /usr/lib/cgi-bin

# 名前付きパイプを作成
$ mkfifo playlist/fifo_listall playlist/fifo_lsplaylist

# 読み書きの権限を付与
$ sudo chmod a+w playlist/fifo_listall playlist/fifo_lsplaylist

#  各cgiファイルに実行権限を付与
$ find . -type f -name '*.cgi' -exec chmod 755 \{\} \;
```

## 開発の目標

### 高い移植性

- シェル固有の拡張機能の使用を廃し,様々なPOSIX準拠環境での動作を可能にする

- 可能な限りPOSIX準拠のコマンドを使用

### 低リソース

- ホスト,クライアント側共に少ないリソースで利用可能

### 動作環境

#### 動作するシェル

- bash ver. 5.1.4

- dash ver. 0.5.11

- mksh ver. 59c-9+b2

- ksh ver. 93u+ 2012-08-01

- yash ver. 2.50

##### 一部不具合あり

- busybox ash ver. 1.30.1 (シバンのオプションを指定しない場合のみ動作)

## トラブルシューティング

### css,ホスト名の変更が出来ない場合(apache2)

```sh
# apache2の実行ユーザーを確認
$ cat /etc/apache2/envvars | grep -e "^export APACHE_RUN_USER" -e "^export APACHE_RUN_GROUP"

# 実行結果(例)
export APACHE_RUN_USER=www-data
export APACHE_RUN_GROUP=www-data

# ホスティングしているディレクトリに移動
$ cd /"YOUR_DIRECTORY"/cgi-bin/

# "APACHE_RUN_USER","APACHE_RUN_GROUP"に合わせてディレクトリの所有ユーザー,グループを変更
$ sudo chown www-data:www-data settings/
```

### "Playlist"ページが開けない場合(apache2)

```sh
# apache2の実行ユーザーを確認
$ cat /etc/apache2/envvars | grep -e "^export APACHE_RUN_USER" -e "^export APACHE_RUN_GROUP"

# 実行結果(例)
export APACHE_RUN_USER=www-data
export APACHE_RUN_GROUP=www-data

# ホスティングしているディレクトリに移動
$ cd /"YOUR_DIRECTORY"/cgi-bin/playlist/

# "APACHE_RUN_USER","APACHE_RUN_GROUP"に合わせて名前付きパイプの所有ユーザー,グループを変更
$ sudo chown www-data:www-data fifo_l*
```

## "urldecode"コマンド引用元

- urldecode:https://github.com/ShellShoccar-jpn/misc-tools
