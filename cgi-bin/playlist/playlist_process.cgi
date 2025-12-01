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
playlist_name="$(echo "${cat_post#*\=}" | urldecode)"

mpc_post() {
	if [ "${cat_post%=*}" = "playlist" ] ; then
		echo "${cat_post%=*} -f \"%file%\" ${playlist_name}" | xargs mpc >/dev/null 2>&1 || true
	else
		echo "${cat_post%=*} \"${playlist_name}\"" | sed -e "s/%20/ /g" -e "s/\"\"/status/" | xargs mpc >/dev/null 2>&1 || true
	fi
}

mpc_post

echo "Status: 302 Found"
echo "Location: /cgi-bin/playlist/playlist.html"
echo ""
