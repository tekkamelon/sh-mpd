#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# 環境変数の設定
export LANG=C

# クエリを変数展開で加工,文字列があれば真,なければ偽
if [ -n "${QUERY_STRING#*\=}" ] ; then

	# 真の場合は設定ファイルにリダイレクト
	echo "${QUERY_STRING#*\=}" >| ../css_conf &

	# メッセージを代入
	export ECHO_MESSAGE="<p>changed css:"${QUERY_STRING#*\=}"</p>"

else

	# 設定ファイル内のcssを代入
	export QUERY_STRING=$(cat ../css_conf)

	# 空文字を代入
	export ECHO_MESSAGE=""

fi

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
    </head> <header> <h1>settings</h1> </header>

    <body>
		<!-- ホスト名の設定 -->
		<form name="setting" method="GET" >

			<!-- CSSの設定 -->
			<h3>CSS setting</h3>

			<!-- css変更時のメッセージを表示 -->
			${ECHO_MESSAGE}

			$(# css一覧を表示

			ls ../../stylesheet |
			
			awk '{

				# 出力をボタン化
				print "<p><button name=css value="$0">"$0"</button></p>"

			}'
			
			)
 
		</form>
    </body>

	<footer>	
		<!-- リンク -->
		<button><a href="/cgi-bin/queued/queued.cgi">Queued</a></button>
		<button><a href="/cgi-bin/directory/directory.cgi">Directory</a></button>
		<button><a href="/cgi-bin/index.cgi">HOME</a></button>
		<button><a href="/cgi-bin/playlist/playlist.cgi">Playlist</a></button>
		<button><a href="/cgi-bin/settings/settings.cgi">Settings</a></button>
	</footer>	

</html>
EOS

