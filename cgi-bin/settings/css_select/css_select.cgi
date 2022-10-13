#!/bin/sh -euxv

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

echo "Content-type: text/html"
echo ""

cat << EOS
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8" />
		<meta name="viewport" content="width=device-width,initial-scale=1.0">
		<link rel="stylesheet" href="/cgi-bin/stylesheet/$(
		# クエリを変数展開で加工,文字列があれば真,なければ偽
		if [ -n "${QUERY_STRING#*\=}" ] ; then

			# 真の場合,クエリを変数展開で加工し出力
			echo ${QUERY_STRING#*\=}

		else

			# 偽の場合は"sh-mpd.conf"の中身を出力,なければ"stylesheet.css"を指定
			cat ../sh-mpd.conf |

			grep ".css" || echo "stylesheet.css"

		fi
		)">
		<link rel="icon" ref="image/favicon.svg">
		<!-- <link rel="apple-touch-icon" href="image/favicon.svg"> -->
        <title>sh-MPD</title>
    </head> <header> <h1>settings</h1> </header>

    <body>
		<!-- ホスト名の設定 -->
		<form name="setting" method="GET" >

			<!-- CSSの設定 -->
			<h3>CSS setting</h3>
			$(# css一覧を表示
			ls  ../../stylesheet | 
			
			# xargsとechoでボタン化
			xargs -I{} echo "<p><button name=css value="{}">"{}"</button></p>"
			)

			$(# クエリを変数展開で加工,文字列があれば真,なければ偽
			if [ -n "${QUERY_STRING#*\=}" ] ; then
	
				# 真の場合,設定ファイルへの書き込み
				cat ../sh-mpd.conf | sed "2 s/.*/$(echo ${QUERY_STRING#*\=})/g" | tee ../sh-mpd.conf > /dev/null

			else

				# 偽の場合は何もしない
				:

			fi
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

