#!/bin/sh

# shellcheck disable=SC1091,SC2154

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
query_check="${QUERY_STRING#*\=}"
search_or_save="${query_check%%&*}"
str_name="$(echo "${query_check#${search_or_save}&input_string=}" | urldecode)"

mpc_proc() {
	if [ -n "${cat_post}" ] ; then
		post_key="${cat_post%\=*}"
		post_value="${cat_post#${post_key}\=}"
		mpc "${post_key}" "${post_value}" >/dev/null 2>&1 || true
	elif [ "${search_or_save}" = "save" ] ; then
		mpc "${search_or_save}" "${str_name}" >/dev/null 2>&1 || true
	fi
}

mpc_proc

echo "Status: 302 Found"
echo "Location: /cgi-bin/queued/queued.html"
echo ""
