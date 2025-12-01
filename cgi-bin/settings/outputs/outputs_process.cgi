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

cat_post="$(cat)"
post_left="${cat_post%\=*}"
post_right="${cat_post#${post_left}\=}"

mpc_post() {
	if [ -n "${cat_post}" ] ; then
		echo "${post_left}" "${post_right}"
	else
		echo "outputs"
	fi | xargs mpc >/dev/null 2>&1 || true
}

mpc_post

echo "Status: 302 Found"
echo "Location: /cgi-bin/settings/outputs/outputs.html"
echo ""
