#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# ====== 変数の設定 ======
# ロケールの設定
export LC_ALL=C
export LANG=C

# GNU coreutilsの挙動をPOSIXに準拠
export POSIXLY_CORRECT=1

# ". (ドット)"コマンドで設定ファイルの読み込み
. ./shmpd.conf
# ====== 変数の設定ここまで ======


# ====== HTML ======
echo "Content-type: text/html"
echo ""

cat << EOS
<!DOCTYPE html>
<html>

    <head>

        <meta charset="UTF-8" />
		<meta name="viewport" content="width=device-width,initial-scale=1.0">
		<link rel="stylesheet" href="/cgi-bin/stylesheet/${stylesheet}">
		<link rel="icon" ref="image/favicon.svg">
		<!-- <link rel="apple-touch-icon" href="image/favicon.svg"> -->
        <title>sh-MPD</title>

    </head>

	<header>

		<h1>Settings</h1>

	</header>

    <body>
	 
		<!-- ホスト名の表示 -->
		<h3>MPD server</h3>
		<p>hostname:${MPD_HOST}</p>
		<p>port:${MPD_PORT}</p>
		<p><button onclick="location.href='/cgi-bin/settings/mpd_server/mpd_setting.cgi'">MPD server setting</button></p>
			
		<!-- ポート番号の設定 -->
		<!-- <p><button onclick="location.href='/cgi-bin/settings/port/port.cgi'">change port</button></p> -->

		<!-- カバーアート用サーバー用の設定 -->
		<h3>coverart server</h3>
		<p>hostname:${img_server_host}</p>
		<p>port:${img_server_port}</p>
		<p><button onclick="location.href='/cgi-bin/settings/coverart_server/coverart_setting.cgi'">coverart server setting</button></p>

		<!-- 出力先デバイスの設定 -->
		<h3>ountput devices list</h3>
		<p><button onclick="location.href='/cgi-bin/settings/outputs/outputs.cgi'">select output device</button></p>
		
		<!-- CSSの設定 -->
		<h3>CSS setting</h3>
		<p><button onclick="location.href='/cgi-bin/settings/css_select/css_select.cgi'">select css</button></p>
			
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

