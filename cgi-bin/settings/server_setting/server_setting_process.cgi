#!/bin/sh

set -eu

export LC_ALL=C
export LANG=C
export POSIXLY_CORRECT=1

tmp_path="$(cd "$(dirname "${0}")/../../../bin" && pwd)"
export PATH="${PATH}:${tmp_path}"

if [ -f ../shmpd.conf ] ; then
	. ../shmpd.conf
fi

cat_post="$(cat)"
post_key="${cat_post#*\=}"
post_key="${post_key%%&*}"
post_args="${cat_post#*\&*\=}"

heredocs() {
	cat <<- EOF
export MPD_HOST="${MPD_HOST}"
export MPD_PORT="${MPD_PORT}"
img_server_host="${img_server_host}"
img_server_port="${img_server_port}"
stylesheet="${stylesheet}"
	EOF
}

post_proc() {
	if [ "${post_key}" = "mpd_host" ] && mpc -q --host="${post_args}" ; then
		export MPD_HOST="${post_args}"
		heredocs > ../shmpd.conf
	elif [ "${post_key}" = "mpd_port" ] && mpc -q --port="${post_args}" ; then
		export MPD_PORT="${post_args}"
		heredocs > ../shmpd.conf
	elif [ "${post_key}" = "img_server_host" ] ; then
		img_server_host="${post_args}"
		heredocs > ../shmpd.conf
	elif [ "${post_key}" = "img_server_port" ] && [ "${post_args}" -ge 1 ] && [ "${post_args}" -le 65535 ] ; then
		img_server_port="${post_args}"
		heredocs > ../shmpd.conf
	fi
}

post_proc

echo "Status: 302 Found"
echo "Location: /cgi-bin/settings/server_setting/server_setting.html"
echo ""
