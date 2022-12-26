#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# 環境変数で接続先ホスト,ポート番号を設定,データがない場合は"localhost","6600"
export LANG=C
export MPD_HOST=$(cat ../settings/hostname | grep . || echo "localhost") 
export MPD_PORT=$(cat ../settings/port_conf | grep . || echo "6600") 

echo "Content-type: text/html"
echo ""

cat << EOS
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8" />
		<meta name="viewport" content="width=device-width,initial-scale=1.0">
		<link rel="stylesheet" href="/cgi-bin/stylesheet/$(cat ../settings/css_conf | grep . || echo "stylesheet.css" &)">
		<link rel="icon" ref="image/favicon_ios.ico">
		<link rel="apple-touch-icon" href="image/favicon_ios.ico">
        <title>sh-MPD</title>
    </head>
	
	<header>
		<h1>Directory</h1>
	</header>

    <body>
		<h4>host:${MPD_HOST}<br>port:${MPD_PORT}<br></h4>
		<form name="FORM" method="GET" >

					<!-- 検索ワードの入力欄 -->
					<p>search_word:<input type="text" name="search_word"></p>
				
		</form>
	
		<!-- ステータスを表示 --> 
		<form name="music" method="POST" >

				<p>$(# POSTで受け取った文字列を変数に代入

				cat_post=$(cat)

				# POSTを変数展開で加工,空でない場合に真,空の場合に偽
				if [ -n "${cat_post#*\=}" ] ; then

					# 真の場合,POSTを変数展開で加工,デコードしてmpcに渡しキューに追加,再生
					echo "${cat_post#*\=}" | urldecode | mpc insert && mpc next

				else

					# ステータスを表示
					mpc status 2>&1

				fi | sed "s/$/<br>/g"

				)</p>

				<!-- リンク -->
				<button><a href="/cgi-bin/queued/queued.cgi">Queued</a></button>
				<button><a href="/cgi-bin/index.cgi">HOME</a></button>
				<button><a href="/cgi-bin/playlist/playlist.cgi">Playlist</a></button>

				<!-- mpc管理下のディレクトリを再帰的に表示 -->
				$(# 曲の一覧をgrepで検索

				mpc listall | grep -F -i "$(echo "${QUERY_STRING#*\=}" | urldecode)" |

				awk '{

					# 出力をボタン化
					print "<p><button name=button value="$0">"$0"</button></p>"

				}'

				)

		</form>
	</body>

	<footer>
		<!-- リンク -->
		<button><a href="/cgi-bin/queued/queued.cgi">Queued</a></button>
		<button><a href="/cgi-bin/index.cgi">HOME</a></button>
		<button><a href="/cgi-bin/playlist/playlist.cgi">Playlist</a></button>
	</footer>

</html>
EOS

