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

# POSTを変数展開で加工,プレイリスト名およびディレクトリ名をデコード
playlist_name=$(echo "${cat_post#*\=}" | urldecode)

# クエリを変数展開で加工,デコード,変数に代入
search_str="$(echo "${QUERY_STRING#*\=}" | urldecode)"

# URLのホスト名を取得
url_hostname=$(cgi_host)
# ====== 変数の設定ここまで ======


# ===== 関数の宣言 ======
# POSTの処理,POSTが無い場合はステータスの表示
mpc_post () {

	# POSTの"name"が"playlist"であれば真,それ以外で偽
	if [ "${cat_post%=*}" = "playlist" ] ; then

		# 変数展開でPOSTの"="をスペースに置換しmpcに渡す
		echo "${cat_post%=*} -f \"%file%\" ${playlist_name}" | xargs mpc 2>&1 |

		# プレイリスト内を表示
		# "playlist_content"にシェル変数"playlist_name"を渡す
		playlist_content -v playlist_name="${playlist_name}"

	else

		# 変数展開でPOSTの"="をスペースに置換
		echo "${cat_post%=*} \"${playlist_name}\"" |

		# "%20"をスペースにデコード,ダブルクォート2つを"status"に置換,mpcに渡す
		sed -e "s/\%20/ /g" -e "s/\"\"/status/" | xargs mpc 2>&1 |

		# ": off"に<b>タグを,": on"に<strong>タグを,各行末に改行のタグを付与
		mpc_status2html -v url_hostname="${url_hostname}"

	fi

}

# プレイリスト検索,表示
list_playlist () {
	
	# プレイリスト一覧を出力
	mpc lsplaylist |

	# 固定文字列を大文字,小文字を区別せずに検索
	grep -F -i "${search_str}" |

	# プレイリストをHTMLに加工
	awk '{

		# プレイリストをキューに追加するボタン
		print "<p><button name=load value="$0">"$0"</button>"

		# プレイリスト内を表示するボタン,クリック時にトップに移動
		print "<a href=#top><button name=playlist value="$0">⋯</button></a></p>"
	
	}'

}
# ===== 関数の宣言ここまで ======


# ====== HTML ======
echo "Content-type: text/html"
echo ""

url_path="${SCRIPT_NAME%.cgi}.html"
echo "Status: 302 Found"
echo "Location: /cgi-bin/${url_path}"
echo ""
