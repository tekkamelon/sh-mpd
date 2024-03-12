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

# ". (ドット)"コマンドで設定ファイルの読み込み
. ../shmpd.conf

# クエリを変数展開で加工,文字列があれば真,なければ偽
if [ -n "${QUERY_STRING#*\=}" ] ; then

	# 真の場合は変数の一覧を出力,設定ファイルへリダイレクト
	cat <<- EOF >| ../shmpd.conf &
	export MPD_HOST="${MPD_HOST}"
	export MPD_PORT="${MPD_PORT}"
	img_server_host="${img_server_host}"
	img_server_port="${img_server_port}"
	stylesheet="${QUERY_STRING#*\=}"
	EOF

	# "stylesheet"にクエリを代入
	stylesheet="${QUERY_STRING#*\=}"

	# メッセージを代入
	export ECHO_MESSAGE="<p>changed css:${stylesheet}</p>"

else

	# 空文字を代入
	export ECHO_MESSAGE=""

fi
# ====== 変数の設定ここまで ======


# ===== 関数の宣言 ======
css_list () {

	# cssの一覧を変数として宣言
	css_list=$(ls ../../stylesheet)

	echo "${css_list}" |

	awk '{

		# 出力をボタン化
		print "<p><button name=css value="$0">"$0"</button></p>"

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

	<header>

		<h1>settings</h1>
	
	</header>

    <body>

		<!-- ホスト名の設定 -->
		<form name="setting" method="GET" >

			<!-- CSSの設定 -->
			<h3>CSS setting</h3>

			<!-- css変更時のメッセージを表示 -->
			${ECHO_MESSAGE}

			$(css_list)
 
		</form>
    </body>

	<footer>	

		<!-- リンク -->
		<button onclick="location.href='/cgi-bin/queued/queued.cgi'">Queued</button>
		<button onclick="location.href='/cgi-bin/directory/directory.cgi'">Directoty</button>
		<button onclick="location.href='/cgi-bin/index.cgi'">HOME</button>
		<button onclick="location.href='/cgi-bin/playlist/playlist.cgi'">Playlist</button>
		<button onclick="location.href='/cgi-bin/settings/settings.cgi'">Settings</button>

	</footer>	

</html>
EOS
# ====== HTMLここまで ======

