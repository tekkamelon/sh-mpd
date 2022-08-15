#!/bin/sh -eu

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
		<link rel="stylesheet" href="/cgi-bin/stylesheet/$(cat css_conf | grep . || echo "stylesheet.css")">
		<link rel="icon" ref="image/favicon.svg">
		<!-- <link rel="apple-touch-icon" href="image/favicon.svg"> -->
        <title>sh-MPD</title>
    </head>

	<header>
		<h1>settings</h1>
	</header>

    <body>
		<!-- ホスト名の設定 -->
		<h3>hostname: $(# "hostname"を表示,ファイルが空の場合は"localhost"を表示
		cat hostname | grep . || echo "localhost"
		)</h3>
		<button><a href="/cgi-bin/settings/host/host.cgi">change_host</a></button>
			
		<!-- 出力先デバイスの設定 -->
		<h3>ountput devices list</h3>
		<button><a href="/cgi-bin/settings/outputs/outputs.cgi">select_output_device</a></button>
		
		<!-- CSSの設定 -->
		<h3>CSS setting</h3>
		<button><a href="/cgi-bin/settings/css_select/css_select.cgi">select_css</a></button>

    </body>

	<footer>	
		<!-- リンク -->
		<button><a href="/cgi-bin/queued/queued.cgi">Queued</a></button>
		<button><a href="/cgi-bin/directory/directory.cgi">Directory</a></button>
		<button><a href="/cgi-bin/index.cgi">HOME</a></button>
		<button><a href="/cgi-bin/playlist/playlist.cgi">Playlist</a></button>
	</footer>	

</html>
EOS

