#!/bin/sh

# shellcheck disable=SC1091,SC2154

set -eu

export LC_ALL=C
export LANG=C
export POSIXLY_CORRECT=1

tmp_path="$(cd "$(dirname "${0}")/../bin" && pwd)"
export PATH="${PATH}:${tmp_path}"

if [ -f settings/shmpd.conf ] ; then
	. settings/shmpd.conf
else
	export MPD_HOST="127.0.0.1"
	export MPD_PORT="6600"
	stylesheet="stylesheet.css"
fi

cat_post=$(cat)

post_check="${cat_post#*\=}"
post_key="${post_check%\&*}"
post_value="${post_check#*\&*\=}"
query_check="${QUERY_STRING#*\=}"

mpc_post () {
	if [ -n "${post_value}" ]; then
		echo "${post_key}" "'${post_value}'" | urldecode
	else
		echo "${query_check}" | sed -e "s/_\-/ \-/g" -e "s/_\%2B/ \+/g" -e "s/\%25/\%/g"
	fi | xargs mpc >/dev/null 2>&1
}

mpc_post

echo "Status: 302 Found"
echo "Location: /cgi-bin/index.html"
echo ""