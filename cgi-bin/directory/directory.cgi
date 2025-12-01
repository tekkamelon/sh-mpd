#!/bin/sh

# shellcheck disable=SC1091

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
tmp_path="$(cd "$(dirname "${0}")/../../bin" && pwd)"
export PATH="${PATH}:${tmp_path}"

# shmpd.confの有無を確認
if [ -f ../settings/shmpd.conf ] ; then

	# 設定ファイルを読み込み
	. ../settings/shmpd.conf


else

	# デフォルトの環境変数を代入
	export MPD_HOST="127.0.0.1"
	export MPD_PORT="6600"

	stylesheet="stylesheet.css"

fi

# POSTを変数に代入
cat_post=$(cat)

# "foo=bar"の"foo","bar"をそれぞれ抽出
post_key="${cat_post%\=*}"
post_value="${cat_post#"${post_key}"\=}"

# クエリをデコードし"search_str"に代入
search_str=$(echo "${QUERY_STRING#*\=}" | urldecode)

# URLのホスト名を取得
url_hostname=$(cgi_host)
# ====== 変数の設定ここまで ======


# ===== 関数の宣言 ======
# POSTの処理し引数をmpcに渡す
mpc_post () {

	# POSTを変数展開で加工,文字列が1以上の数値であれば真,それ以外で偽
	if [ "${post_value}" -gt 0 ] ; then

		# 楽曲の一覧から"post_value"の番号の行を抽出,結果を挿入
		mpc listall | sed -n "${post_value}"p | mpc add

		# キュー内の楽曲数を変数に代入
		last_line=$(mpc playlist | wc -l)

		echo "play ${last_line}"

	# 偽の場合は"addresult"であれば真,それ以外で偽
	elif [ "${post_key}" = "addresult" ] ; then

		# 楽曲の一覧から"search_str"で検索,結果を挿入
		mpc listall | grep -F -i "${search_str}" | mpc add &

		echo "status"

	# 偽の場合は"all"であれば真,それ以外で偽
	elif [ "${post_value}" = "all" ] ; then

		# すべての楽曲をキューに追加
		mpc add / &

		echo "status"

	else

		# 偽の場合は"status"を出力
		echo "status"
	
	# エラー出力を捨てる
	fi 2> /dev/null |

	# 出力をmpcに渡す
	xargs mpc 2>&1 |
	
	# ": off"に<b>タグを,": on"に<strong>タグを,各行末に改行のタグを付与
	mpc_status2html -v url_hostname="${url_hostname}"

}

# mpd管理下の全ての曲を表示
directory_list () {

	# 再生中の楽曲
	mpc_current="$(mpc current -f "%file%")"

	# 曲の一覧を出力,行番号と区切り文字":"の付与,検索
	mpc listall | grep -F -i -n "${search_str}" |

	# キュー内の楽曲をHTMLで表示,現在再生中の楽曲は"[Now Playing]"を付与
	# "queued_song"にシェル変数"current",post_nameに"add"を渡す
	queued_song -v mpc_current="${mpc_current}" -v post_name="add"

}
# ===== 関数の宣言ここまで ======


# ====== HTML ======
echo "Content-type: text/html"
echo ""

url_path="${SCRIPT_NAME%.cgi}.html"
echo "Status: 302 Found"
echo "Location: /cgi-bin/${url_path}"
echo ""
