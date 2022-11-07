#!/bin/sh -euxv

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# 環境変数で接続先ホストを設定,ファイルがない場合はローカルホスト
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
		<link rel="stylesheet" href="/cgi-bin/stylesheet/$(cat ../css_conf | grep . || echo "stylesheet.css" &)">
		<link rel="icon" ref="image/favicon.svg">
		<!-- <link rel="apple-touch-icon" href="image/favicon.svg"> -->
        <title>sh-MPD</title>
    </head>

	<header>
		<h1>settings</h1>
	</header>

    <body>
		<form name="setting" method="POST" >
			
			<h4>$(echo "host:$MPD_HOST<br>port:$MPD_PORT<br>" &)</h4>

			<!-- 出力先デバイスの設定 -->
			<h3>ountput devices list</h3>
			$(# POSTで受け取った文字列が空かどうかを判定し処理を分岐

			# POSTで受け取った文字列を変数に代入
			cat_post=$(cat)

			# POSTに文字列が含まれていれば真,なければ偽
			if [ -n "${cat_post#*\=}" ] ; then

				# 真の場合,変数展開でPOSTを加工,xargsでmpcに渡す
				echo ${cat_post#*\=} | xargs mpc toggleoutput 

			else

				# 偽の場合,出力デバイスの一覧をボタン化
				mpc outputs 

			fi | 

			# "Output"を含む行をボタン化
			awk '/Output/{

				print "<p><button name=toggleoutput value="$2">"$0"</button></p>"

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

