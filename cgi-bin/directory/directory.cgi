#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# ====== 変数の設定 ======
# ロケールの設定
export LC_ALL=C
export LANG=C

# GNU coreutilsの挙動をPOSIXに準拠
export POSIXLY_CORRECT=1

# 独自コマンドへPATHを通す
export PATH="$PATH:../../bin"

# ". (ドット)"コマンドで設定ファイルの読み込み
. ../settings/shmpd.conf

# POSTを変数に代入
cat_post=$(cat)

# "foo=bar"の"foo","bar"をそれぞれ抽出
post_left="${cat_post%\=*}"
post_right="${cat_post#"${post_left}"\=}"

# クエリをデコードし"search_str"に代入
search_str=$(echo "${QUERY_STRING#*\=}" | urldecode)
# ====== 変数の設定ここまで ======


# ===== 関数の宣言 ======
# POSTの処理し引数をmpcに渡す
mpc_post () {

	# POSTを変数展開で加工,文字列が1以上の数値であれば真,それ以外で偽
	if [ "${post_right}" -gt 0 ] ; then

		# 楽曲の一覧から"post_right"の番号の行を抽出,結果を挿入
		mpc listall | sed -n "${post_right}"p | mpc add

		# キュー内の楽曲数を変数に代入
		last_line=$(mpc playlist | wc -l)

		echo "play ${last_line}"

	# 偽の場合は"addresult"であれば真,それ以外で偽
	elif [ "${post_left}" = "addresult" ] ; then

		# 楽曲の一覧から"search_str"で検索,結果を挿入
		mpc listall | grep -F -i "${search_str}" | mpc add &

		echo "status"

	# 偽の場合は"all"であれば真,それ以外で偽
	elif [ "${post_right}" = "all" ] ; then

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
	mpc_status2html

}

# mpd管理下の全ての曲を表示
directory_list () {

	# 曲の一覧を出力,行番号と区切り文字":"の付与,検索
	mpc listall | grep -F -i -n "${search_str}" |

	# ":"を">"に置換,標準入力をタグ付きで出力
	awk '{

		sub(":" , ">")

		print "<p><button name=add value="$0"</button></p>"

	}'

}
# ===== 関数の宣言ここまで ======


# ====== HTML ======
echo "Content-type: text/html"
echo ""

cat << EOS
<!DOCTYPE html>
<html>

    <head>

        <meta charset="UTF-8" />
		<meta name="viewport" content="width=device-width,initial-scale=1.0">
		<link rel="stylesheet" href="/cgi-bin/stylesheet/${stylesheet}">
		<link rel="icon" ref="/cgi-bin/image/favicon.ico">
		<link rel="apple-touch-icon" href="/cgi-bin/image/favicon.ico">
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
			<p><button name=add value=all>add all songs</button></p>

		</form>

		<!-- リンク -->
		<button onclick="location.href='/cgi-bin/queued/queued.cgi'">Queued</button>
		<button onclick="location.href='/cgi-bin/index.cgi'">HOME</button>
		<button onclick="location.href='/cgi-bin/playlist/playlist.cgi'">Playlist</button>

		<form name="music" method="POST" >

			<!-- mpc管理下のディレクトリを再帰的に表示 -->
			$(directory_list)
			
			<!-- 検索結果を挿入するボタン -->
			<p><button name=addresult value=>add search result</button></p>

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
