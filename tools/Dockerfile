# sh-MPD 本番コンテナのイメージ定義
#
# 土台の sh-mpd_amd64 (Debian 11 + Apache + mpc + sh-MPD の配置) は
# 本リポジトリにビルド元が無く, ホスト上で対話的に作成されたものを使用している。
# この定義はそこへ予約実行用の at/atd を足し, entrypoint を明示するためのもの。
#
# ビルド: docker build -t sh-mpd-at:latest tools/
# 起動:   sh tools/docker_shmpd.sh

FROM sh-mpd_amd64

# 予約実行のため at/atd を導入する
# イメージ内に init が無いため, entrypoint で atd を起動してから Apache を前面実行する
RUN apt-get update \
 && apt-get install -y --no-install-recommends at \
 && rm -rf /var/lib/apt/lists/*

COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 755 /usr/local/bin/entrypoint.sh

EXPOSE 80
EXPOSE 6600

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
