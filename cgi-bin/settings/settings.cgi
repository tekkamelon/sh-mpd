#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# 環境変数の設定
# ホスト名,ポート番号を設定,データがない場合は"localhost","6600"
export LANG=C
export MPD_HOST=$(cat hostname | grep . || echo "localhost") 
export MPD_PORT=$(cat port_conf | grep . || echo "6600") 

echo "Content-type: text/html"
echo ""

cat << EOS
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8" />
		<meta name="viewport" content="width=device-width,initial-scale=1.0">
		<link rel="stylesheet" href="/cgi-bin/stylesheet/$(cat css_conf)">
		<link rel="icon" ref="image/favicon.svg">
		<!-- <link rel="apple-touch-icon" href="image/favicon.svg"> -->
        <title>sh-MPD</title>
    </head>

	<header>
		<h1>settings</h1>
	</header>

    <body>
		<!-- ホスト名の表示 -->
		<h3>hostname:$MPD_HOST</h3>
		<button><a href="/cgi-bin/settings/host/host.cgi">change_host</a></button>
			
		<!-- ポート番号の設定 -->
		<h3>port: $MPD_PORT</h3>
		<button><a href="/cgi-bin/settings/port/port.cgi">change_port</a></button>

		<!-- 出力先デバイスの設定 -->
		<h3>ountput devices list</h3>
		<button><a href="/cgi-bin/settings/outputs/outputs.cgi">select_output_device</a></button>
		
		<!-- CSSの設定 -->
		<h3>CSS setting</h3>
		<button><a href="/cgi-bin/settings/css_select/css_select.cgi">select_css</a></button>
			
    </body>

	<div class="link">
		<footer>	
			<!-- リンク -->
			<button><a href="/cgi-bin/queued/queued.cgi">Queued</a></button>
			<button><a href="/cgi-bin/directory/directory.cgi">Directory</a></button>
			<button><a href="/cgi-bin/index.cgi">HOME</a></button>
			<button><a href="/cgi-bin/playlist/playlist.cgi">Playlist</a></button>
		</footer>	
	</dev>

</html>
EOS

