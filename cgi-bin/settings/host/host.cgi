#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# 環境変数で接続先ホスト,ポート番号を設定,データがない場合は"localhost","6600"
export MPD_HOST=$(cat ../hostname | grep . || echo "localhost") 
export MPD_PORT=$(cat ../port_conf | grep . || echo "6600") 

echo "Content-type: text/html"
echo ""

cat << EOS
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8" />
		<meta name="viewport" content="width=device-width,initial-scale=1.0">
		<link rel="stylesheet" href="/cgi-bin/stylesheet/$(cat ../css_conf | grep . || echo "stylesheet.css")">
		<link rel="icon" ref="image/favicon.svg">
		<!-- <link rel="apple-touch-icon" href="image/favicon.svg"> -->
        <title>sh-MPD</title>
    </head>

	<header>
		<h1>settings</h1>
	</header>

    <body>
		<!-- ホスト名,ポート番号の表示-->
		<h4>$(echo "host:$MPD_HOST<br>port:$MPD_PORT<br>")</h4>
		<form name="setting" method="POST" >

				<span>
					<p>enter hostname or local IP: <input type="text" placeholder="example: foobar.local" name="MPD_HOST"></p>
				</span>
			
			<!-- 実行結果を表示 -->
			<p>$(# POSTをデコード
			cat | urldecode |

			# 区切り文字を"="に指定,数値,"localhost","任意の1文字以上.local"にマッチする場合の処理
			awk -F"=" '/[0-9]/ || /localhost/ || /.\.local/{

				# メッセージを表示	
				print "<p>changed host:"$2"</p>"

				# ファイルに上書き
				print $2 > "../hostname"

			}

			# いずれにもマッチしない場合の処理
			!/[0-9]/ && !/localhost/ && !/.\.local/{

				# メッセージを表示	
				print "<p>please enter hostname or local IP adress!</p>"
				
			}'
			)</p>
			
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

