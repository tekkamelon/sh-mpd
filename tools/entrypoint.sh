#!/bin/sh

# sh-MPD 本番コンテナのentrypoint
# atdを起動し,その後Apacheを前面で実行する(コンテナのPID1になる)
set -eu

# atdのスプールを用意(スプールをvolumeで上書きした場合に備える)
if command -v atd > /dev/null 2>&1 ; then

	for dir in /var/spool/cron/atjobs /var/spool/cron/atspool ; do

		mkdir -p "${dir}"
		chown daemon:daemon "${dir}"
		chmod 1770 "${dir}"

	done

fi

# Apacheの環境変数を読み込む
# (apache2.confが${APACHE_RUN_USER}等を参照し,envvars自身もAPACHE_CONFDIRを参照するため先に与える)
APACHE_CONFDIR="${APACHE_CONFDIR:-/etc/apache2}"
export APACHE_CONFDIR
# shellcheck disable=SC1091
. /etc/apache2/envvars

# atdの起動(atが無い環境では予約機能が使えないだけなので続行する)
if command -v atd > /dev/null 2>&1 ; then

	if ! pgrep -x atd > /dev/null 2>&1 ; then

		atd

	fi

fi

# Apacheを前面で実行
exec apache2 -D FOREGROUND
