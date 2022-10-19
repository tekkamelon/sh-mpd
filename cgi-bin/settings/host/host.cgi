#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# 環境変数で接続先ホスト,ポート番号を設定,データがない場合は"localhost","6600"
export MPD_HOST=$(cat ../hostname | grep . || echo "localhost") 
export MPD_HOST=$(cat ../port_conf | grep . || echo "6600") 

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
			<p>$(# POSTで受け取った文字列を変数に代入
			cat_post=$(cat) 

				# POSTを変数展開で加工,数字,"localhost",".local"のどれかにマッチすれば真
				if echo "${cat_post#*\=}" | grep -q -E "[0-9]|localhost|*\.local" ; then

					# 真の場合,変数展開で加工,teeで設定ファイルへの書き込み
					echo ${cat_post#*\=} | tee ../hostname | 

					# xargsでechoに渡す
					xargs -I{} echo '<p>hostname:{}</p>'

				else
					
					# 偽の場合は何もしない
					:

				fi
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

