#!/bin/sh

# shellcheck disable=SC1091

set -eu

export LC_ALL=C
export LANG=C
export POSIXLY_CORRECT=1

tmp_path="$(cd "$(dirname "${0}")/../bin" && pwd)"
export PATH="${PATH}:${tmp_path}"

if [ -f settings/shmpd.conf ] ; then
	. settings/shmpd.conf
fi

url_hostname="$(cd "$(dirname "${0}")/../bin" && ./cgi_host)"

echo "Content-Type: text/plain; charset=UTF-8"
echo ""

mpc status 2>&1 | mpc_status2html -v url_hostname="${url_hostname}"