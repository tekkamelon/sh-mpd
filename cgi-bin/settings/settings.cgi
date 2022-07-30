#!/bin/sh -eux

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
		<link rel="stylesheet" href="/cgi-bin/stylesheet/stylesheet.css">
		<link rel="icon" ref="image/favicon.svg">
		<!-- <link rel="apple-touch-icon" href="image/favicon.svg"> -->
        <title>sh-MPD</title>
    </head>

	<header>
		<h1>settings</h1>
	</header>

    <body>
		<form name="setting" method="POST" >
		<h3>host:$(echo $MPD_HOST)</h3>
			<span style="color: rgb(0, 255, 10); ">
				<p>hosname:<input type="text" name="MPD_HOST"></p>
			</span>

		<h3>ountput devices list</h3>
		$(# mpc outputsの出力結果から出力先デバイスの情報のみを表示,POSTで出力先デバイスの番号のみを渡す
		mpc outputs | 

		# "enable"又は"disable"を含む行を抽出,ボタン化し出力
		awk '/enable/ || /disable/{print "<p><button name=toggleoutput value="$2">"$0"</button></p>"}'
		)

		<p>$(# POSTから受け取ったデータをmpcに渡す
		cat | awk -F'[=&]' '{print $3,$4}' | xargs mpc
		)</p>

		</form>
    </body>

	<footer>	
		<!-- リンク -->
		<button><a href="/cgi-bin/directory/directory.cgi">Directory</a></button>
		<button><a href="/cgi-bin/index.cgi">HOME</a></button>
		<button><a href="/cgi-bin/playlist/playlist.cgi">Playlist</a></button>
	</footer>	

</html>
EOS
