#!/bin/sh

# shellcheck disable=SC1091

set -eu

export LC_ALL=C
export LANG=C
export POSIXLY_CORRECT=1

tmp_path="$(cd "$(dirname "${0}")/../..//bin" && pwd)"
export PATH="${PATH}:${tmp_path}"

if [ -f ../settings/shmpd.conf ] ; then
	. ../settings/shmpd.conf
else
	export MPD_HOST="127.0.0.1"
	export MPD_PORT="6600"
	stylesheet="stylesheet.css"
fi

cat_post="$(cat)"
post_key="${cat_post%\=*}"
post_value="${cat_post#${post_key}\=}"
search_str="$(echo "${QUERY_STRING#*\=}" | urldecode)"

mpc_post() {
	if [ "${post_value}" -gt 0 ] 2>/dev/null ; then
		mpc listall | sed -n "${post_value}"p | mpc add >/dev/null 2>&1 || true
		last_line="$(mpc playlist | wc -l)"
		echo "play ${last_line}" | xargs mpc >/dev/null 2>&1 || true
	elif [ "${post_key}" = "addresult" ] ; then
		mpc listall | grep -F -i "${search_str}" | mpc add >/dev/null 2>&1 || true
	elif [ "${post_value}" = "all" ] ; then
		mpc add / >/dev/null 2>&1 || true
	fi | xargs mpc >/dev/null 2>&1 || true
}

mpc_post

echo "Status: 302 Found"
echo "Location: /cgi-bin/directory/directory.html"
echo ""
