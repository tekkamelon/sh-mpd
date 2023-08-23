#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# ====== 環境変数の設定 ======
export LC_ALL=C
export LANG=C

# ホスト名,ポート番号を設定,データがない場合は"localhost","6600"
host="$(cat hostname)"
port="$(cat port_conf)"
export MPD_HOST="${host}"
export MPD_PORT="${port}"
# ====== 環境変数の設定ここまで ======


# ====== HTML ======
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

		<h1>Settings</h1>

	</header>

    <body>
	 
		<!-- ホスト名の表示 -->
		<h3>hostname:${MPD_HOST}</h3>
		<p><button onclick="location.href='/cgi-bin/settings/host/host.cgi'">change_host</button></p>
			
		<!-- ポート番号の設定 -->
		<h3>port:${MPD_PORT}</h3>
		<p><button onclick="location.href='/cgi-bin/settings/port/port.cgi'">change_port</button></p>

		<!-- 出力先デバイスの設定 -->
		<h3>ountput devices list</h3>
		<p><button onclick="location.href='/cgi-bin/settings/outputs/outputs.cgi'">select_output_device</button></p>
		
		<!-- CSSの設定 -->
		<h3>CSS setting</h3>
		<p><button onclick="location.href='/cgi-bin/settings/css_select/css_select.cgi'">select_css</button></p>
			
    </body>

	<div class="link">

		<footer>	

			<!-- リンク -->
			<button onclick="location.href='/cgi-bin/queued/queued.cgi'">Queued</button>
			<button onclick="location.href='/cgi-bin/directory/directory.cgi'">Directoty</button>
			<button onclick="location.href='/cgi-bin/index.cgi'">HOME</button>
			<button onclick="location.href='/cgi-bin/playlist/playlist.cgi'">Playlist</button>

		</footer>	

	</dev>

</html>
EOS
# ====== HTMLここまで ======

