#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# 環境変数の設定
# ホスト名,ポート番号を設定,データがない場合は"localhost","6600"
export LANG=C
export MPD_HOST=$(cat ../settings/hostname) 
export MPD_PORT=$(cat ../settings/port_conf) 

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
			<p>search_word:<input type="text" name="search_word"></p>
				
		</form>
	
		<!-- ステータスを表示 --> 
		<form name="music" method="POST" >

		<!-- 最下部へのジャンプ -->
		<p><a href="#bottom">jump to bottom</a></p>

			<p>$(# POSTで受け取った文字列を変数に代入

			cat_post=$(cat)

			# POSTを変数展開で加工,文字列があれば真,無ければ偽
			if [ -n "${cat_post#*\=}" ] ; then 

				# 真の場合はPOSTを変数展開で"="をスペースに置換,曲名をダブルクォートで括って出力
				echo "${cat_post%\=*} ""\"${cat_post#*\=}\"" |
	
				# デコード,mpcに渡す
				urldecode | xargs mpc &

				# "next"を出力
				echo "next"

			else

				# 偽の場合は"status"を出力
				echo "status"
			
			fi |

			# 出力をmpcに渡す
			xargs mpc 2>&1 |
			
			# 出力を改行
			sed "s/$/<br>/g"

			# 全ての曲を追加する
			echo "<p><button name=add value=/>add all songs</button></p>"

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
				print "<p><button name=insert value="$0">"$0"</button></p>"

			}'

			)

		</form>
	</body>

	<!-- "jump to bottom"のジャンプ先 -->
	<div id="bottom"></div>

	<footer>
		<!-- リンク -->
		<button><a href="/cgi-bin/queued/queued.cgi">Queued</a></button>
		<button><a href="/cgi-bin/index.cgi">HOME</a></button>
		<button><a href="/cgi-bin/playlist/playlist.cgi">Playlist</a></button>
	</footer>

	<!-- 最上部へのジャンプ -->
	<p><a href="#top">jump to top</a></p>

</html>
EOS

