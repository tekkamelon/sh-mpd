#!/bin/sh

# shellcheck disable=SC1091,SC2154

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
set -eu

# ====== 変数の設定 ======
# ロケールの設定
export LC_ALL=C
export LANG=C

# GNU coreutilsの挙動をPOSIXに準拠
export POSIXLY_CORRECT=1

# 独自コマンドへPATHを通す
tmp_path="$(cd "$(dirname "${0}")/../bin" && pwd)"
export PATH="${PATH}:${tmp_path}"

# shmpd.confの有無を確認
if [ -f settings/shmpd.conf ] ; then

	# 設定ファイルを読み込み
	. settings/shmpd.conf

else

	# デフォルトの環境変数を代入
	export MPD_HOST="127.0.0.1"
	export MPD_PORT="6600"

	stylesheet="stylesheet.css"

fi

# POSTを変数に代入
cat_post=$(cat)

# POSTを変数展開し代入
post_check="${cat_post#*\=}"

# "foo=bar"の"foo","bar"をそれぞれ抽出
post_key="${post_check%\&*}"
post_value="${post_check#*\&*\=}"

# クエリを変数展開し代入
query_check="${QUERY_STRING#*\=}"

# URLのホスト名を取得
url_hostname="$(cgi_host)"
# ====== 変数の設定ここまで ======


# ===== 関数の宣言 ======
# 変数展開で加工したPOSTの文字列の有無を判定,あればクエリを加工しmpcへ渡す
mpc_post () {

    # POST値があればデコードしてmpcに渡す
    if [ -n "${post_value}" ]; then

        echo "${post_key}" "'${post_value}'" | urldecode

    else

        # クエリ値を加工
        echo "${query_check}" |

		sed -e "s/_\-/ \-/g" -e "s/_\%2B/ \+/g" -e "s/\%25/\%/g"

    fi |

	# mpcのエラー出力ごと渡す
	xargs mpc 2>&1 |

	mpc_status2html -v url_hostname="${url_hostname}"

}

# カバーアートの取得
coverart () {

	# 変数img_server_host,img_server_portの有無を確認
    if [ -z "${img_server_host:-}" ] || [ -z "${img_server_port:-}" ]; then

        echo ""
        return

    fi

	# 現在の曲を変数に代入
    current_song="$(mpc current -f "%file%")"

	# 曲のパスを変数に代入
    song_path="${current_song%/*}"

	# カバーアートのURLを出力
    echo "http://${img_server_host}:${img_server_port}/${song_path}/Folder.jpg"

}

# 次の曲の表示
next_song () {

	# "mpc queued"を変数に代入
	queued=$(mpc queued)

	# "queued"があれば真,なければ偽
	if [ -n "${queued}" ] ; then

		# 真の場合は"queued"を表示
		echo "${queued}"

	else

		# 偽の場合はメッセージを表示
		echo "next song not found"

	fi

}
# ===== 関数の宣言ここまで ======


url_path="${SCRIPT_NAME%.cgi}.html"
echo "Status: 302 Found"
echo "Location: /cgi-bin/${url_path}"
echo ""

