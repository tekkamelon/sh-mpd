# sh-MPD 本番コンテナのイメージ定義 (Debian 13 trixie)
#
# 旧構成は sh-mpd_amd64 (Debian 11 bullseye を対話的に構築したもの, ビルド元なし)
# を土台に at を足していた。土台の出自が不明で OS も更新できないため,
# Debian 13 から一式を自己完結で構築する。
#
# ビルド: docker build -f tools/Dockerfile -t sh-mpd-at:trixie .
#         (コンテキストはリポジトリ直下: bin/urldecode をそのまま同梱するため)
# 起動:   sh tools/docker_shmpd.sh sh-mpd-at:trixie

FROM debian:13-slim

ENV TZ=Asia/Tokyo
ENV DEBIAN_FRONTEND=noninteractive

# Apache と CGI が使うコマンド, 予約実行用の at
#   psmisc : pgrep (bin/schedule_mpc が atd の稼働確認に使う)
#   mpc    : libmpdclient2 を依存で導入する
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
        apache2 \
        at \
        mpc \
        psmisc \
 && rm -rf /var/lib/apt/lists/*

# CGI 実行ユーザ (uid/gid 1000 は旧イメージと同一に揃える)
#   bind mount するリポジトリは world readable なので uid は読み取りに影響しないが,
#   at のジョブ所有者を旧構成と変えないために合わせる
RUN groupadd -g 1000 shmpd \
 && useradd -u 1000 -g shmpd -m -d /home/shmpd -s /bin/bash shmpd \
 && install -d -o shmpd -g shmpd /home/shmpd/Documents/github

# Apache のランタイムディレクトリ (Debian 13 の slim イメージには存在しない)
# socks は cgid のソケット置場 (無いと CGI が 503 になる)
RUN install -d -m 755 /var/run/apache2 /var/lock/apache2 \
 && install -d -m 755 -o shmpd -g shmpd /var/run/apache2/socks

# Apache のワーカーを shmpd で動かす (CGI もこのユーザで実行される)
RUN sed -i \
        -e 's/^export APACHE_RUN_USER=.*/export APACHE_RUN_USER=shmpd/' \
        -e 's/^export APACHE_RUN_GROUP=.*/export APACHE_RUN_GROUP=shmpd/' \
        /etc/apache2/envvars

# 既定の /usr/lib/cgi-bin は使わず, リポジトリの cgi-bin を /cgi-bin/ に割り当てる
# cgid は Debian の apache2 では既定で無効 (mpm_event と組み合わせるため cgid を使う)
RUN a2disconf serve-cgi-bin \
 && a2enmod cgid
COPY tools/apache-shmpd.conf /etc/apache2/conf-available/shmpd.conf
RUN a2enconf shmpd

# URL デコーダ (CGI は PATH の後ろに bin を通すため, システム側にも同じ実装を置く)
COPY bin/urldecode /usr/local/bin/urldecode
RUN chmod 755 /usr/local/bin/urldecode

COPY tools/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod 755 /usr/local/bin/entrypoint.sh

EXPOSE 80
EXPOSE 6600

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
