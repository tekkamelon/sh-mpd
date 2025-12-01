#!/bin/sh

# shellcheck disable=SC1091,SC2154

set -eu

export LC_ALL=C
export LANG=C
export POSIXLY_CORRECT=1

tmp_path="$(cd "$(dirname "${0}")/../../../bin" && pwd)"
export PATH="${PATH}:${tmp_path}"

if [ -f ../shmpd.conf ] ; then
	. ../shmpd.conf
fi

query_check="${QUERY_STRING#*\=}"

if [ -n "${query_check}" ] ; then
	cat <<- EOF > ../shmpd.conf
export MPD_HOST="${MPD_HOST}"
export MPD_PORT="${MPD_PORT}"
img_server_host="${img_server_host}"
img_server_port="${img_server_port}"
stylesheet="${query_check}"
	EOF
fi

echo "Status: 302 Found"
echo "Location: /cgi-bin/settings/css_select/css_select.html"
echo ""
