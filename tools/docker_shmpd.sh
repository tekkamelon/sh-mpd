#!/bin/sh

# sh-MPD の本番コンテナを起動する
#
# 使用例: sh docker_shmpd.sh [image]
#   イメージを省略した場合は sh-mpd-at:latest を使用する
#
# 予約機能(at)のスプールはnamed volumeへ保存し,コンテナの作り直しで消えないようにする
set -eu

# ====== 変数の設定 ======
image="${1:-sh-mpd-at:latest}"
repo="${HOME}/Documents/github/sh-mpd"
volume="shmpd-atspool"
# ====== 変数の設定ここまで ======

docker container run -d --name shmpd \
	--restart unless-stopped \
	--mount "type=bind,src=${repo},dst=/home/shmpd/Documents/github/sh-mpd" \
	-v "${volume}:/var/spool/cron" \
	-p 80:80 \
	"${image}"

