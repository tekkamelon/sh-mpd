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

# クエリを変数展開で加工,文字列があれば真,なければ偽
if [ -n "${QUERY_STRING#*\=}" ] ; then

	# 真の場合は設定ファイルにリダイレクト
	echo "${QUERY_STRING#*\=}" >| ../css_conf &

	# メッセージを代入
	export ECHO_MESSAGE="<p>changed css:${QUERY_STRING#*\=}</p>"

else

	# 設定ファイル内のcssを代入
	css_config="$(cat ../css_conf)"

	export QUERY_STRING="${css_config}"

	# 空文字を代入
	export ECHO_MESSAGE=""

fi
# ====== 環境変数の設定ここまで ======


# ===== スクリプトによる処理 ======
css_list=$(# css一覧を表示

	# cssの一覧を変数として宣言
	css_list=$(ls ../../stylesheet)

	echo "${css_list}" |

	awk '{

		# 出力をボタン化
		print "<p><button name=css value="$0">"$0"</button></p>"

	}'

)
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
		<link rel="stylesheet" href="/cgi-bin/stylesheet/${QUERY_STRING#*\=}">
		<link rel="icon" ref="image/favicon.svg">
		<!-- <link rel="apple-touch-icon" href="image/favicon.svg"> -->
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

			${css_list}
 
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

