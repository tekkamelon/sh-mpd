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
search_str="$(echo "${QUERY_STRING#*\=}" | urldecode)"

mpc_post() {
	echo "${cat_post}" | sed -e "s/=/ /g" -e "s/\&del//g" | xargs mpc >/dev/null 2>&1 || true
}

mpc_post

echo "Status: 302 Found"
echo "Location: /cgi-bin/queued/remove.html"
echo ""
