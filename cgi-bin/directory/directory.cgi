#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# ====== 環境変数の設定 ======
# ロケールの設定
export LC_ALL=C
export LANG=C

# GNU coreutilsの挙動をPOSIXに準拠
export POSIXLY_CORRECT=1

# 独自コマンドへPATHを通す
export PATH="$PATH:../../bin"

# ホスト名,ポート番号を設定
host="$(cat ../settings/hostname)"
port="$(cat ../settings/port_conf)"
export MPD_HOST="${host}"
export MPD_PORT="${port}"
# ====== 環境変数の設定ここまで ======


# ===== スクリプトによる処理 ======
# POSTやクエリから受け取ったテキストの処理
mpc_post () {

	# POSTの有無に応じてmpcでの処理を分岐

	# POSTで受け取った文字列を変数として宣言
	cat_post=$(cat)

	# POSTを変数展開で加工,文字列があれば真,無ければ偽
	if [ -n "${cat_post#*\=}" ] ; then 

		# 真の場合はPOSTを変数展開で"="をスペースに置換,曲名をダブルクォートで括って出力
		echo "${cat_post%\=*} ""\"${cat_post#*\=}\"" |

		# デコード,mpcに渡す
		urldecode | xargs mpc &

		echo "next"

	# 偽の場合はPOSTを変数展開,"insertresult="であれば真,それ以外で偽
	elif [ "${cat_post#\=*}" = "insertresult=" ] ; then

		# 真の場合はクエリをデコードし"search_str"に代入
		search_str=$(echo "${QUERY_STRING#*\=}" | urldecode)

		# 曲の一覧から"search_str"で検索,結果を挿入
		mpc listall | grep -F -i "${search_str}" | mpc insert &

		echo "next"

	else

		# 偽の場合は"status"を出力
		echo "status"
	
	fi |

	# 出力をmpcに渡す
	xargs mpc 2>&1 |
	
	# ": off"に<b>タグを,": on"に<strong>タグを,各行末に改行のタグを付与
	mpc_status2html

}

# mpd管理下の全ての曲を表示
directory_list () {

	# 曲の一覧をgrepで検索

	# クエリをデコードし"search_str"に代入
	search_str=$(echo "${QUERY_STRING#*\=}" | urldecode)

	# 曲の一覧から"search_str"で検索
	mpc listall | grep -F -i "${search_str}" |

	awk '{

		# 出力をボタン化
		print "<p><button name=insert value="$0">"$0"</button></p>"

	}'

}
# ===== スクリプトによる処理ここまで ======


# ====== HTML ======
echo "Content-type: text/html"
echo ""

cat << EOS
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8" />
		<meta name="viewport" content="width=device-width,initial-scale=1.0">
		<link rel="stylesheet" href="/cgi-bin/stylesheet/$(cat ../settings/css_conf)">
		<link rel="icon" ref="image/favicon_ios.ico">
		<link rel="apple-touch-icon" href="image/favicon_ios.ico">
        <title>sh-MPD</title>
    </head>
	
	<!-- "jump to top"のジャンプ先 -->
	<div id="top"></div>

	<header>
		<h1>Directory</h1>

	</header>

    <body>

		<h4>host:${MPD_HOST}<br>port:${MPD_PORT}<br></h4>
		<form name="FORM" method="GET" >

			<!-- 検索ワードの入力欄 -->
			<p><input type="text" placeholder="search word" name="search_word"></p>
				
		</form>
	
		<form name="music" method="POST" >

		<!-- 最下部へのジャンプ -->
		<p><a href="#bottom">jump to bottom</a></p>

			<!-- ステータスを表示 --> 
			<p>$(mpc_post)</p>

			<!-- 全ての曲を追加するボタン -->
			<p><button name=add value=/>add all songs</button></p>

		</form>

		<!-- リンク -->
		<button onclick="location.href='/cgi-bin/queued/queued.cgi'">Queued</button>
		<button onclick="location.href='/cgi-bin/index.cgi'">HOME</button>
		<button onclick="location.href='/cgi-bin/playlist/playlist.cgi'">Playlist</button>

		<form name="music" method="POST" >

			<!-- mpc管理下のディレクトリを再帰的に表示 -->
			$(directory_list)
			
			<!-- 検索結果を挿入するボタン -->
			<p><button name=insertresult value=>insert search result</button></p>

		</form>
		
	</body>

	<!-- "jump to bottom"のジャンプ先 -->
	<div id="bottom"></div>

	<footer>

		<!-- リンク -->
		<button onclick="location.href='/cgi-bin/queued/queued.cgi'">Queued</button>
		<button onclick="location.href='/cgi-bin/index.cgi'">HOME</button>
		<button onclick="location.href='/cgi-bin/playlist/playlist.cgi'">Playlist</button>

	</footer>

	<!-- 最上部へのジャンプ -->
	<p><a href="#top">jump to top</a></p>

</html>
EOS
# ====== HTMLここまで ======
