#!/bin/sh

# shellcheck disable=SC1091,SC2154

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
set -eu

# ====== 変数の設定 ======
# ロケールの設定
export LC_ALL=C
export LANG=C

# GNU coreutilsの挙動をPOSIXに準拠
export POSIXLY_CORRECT=1

# 独自コマンドへPATHを通す
export PATH="$PATH:../../bin"

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
		<link rel="icon" ref="/cgi-bin/image/favicon.ico">
		<link rel="apple-touch-icon" href="/cgi-bin/image/favicon.ico">
		<title>Server setting - sh-MPD:$(cgi_host) -</title>

    </head>

	<header>

		<h1>Settings</h1>

	</header>

    <body>
	 
		<h3>Server setting</h3>

		<!-- ホスト名,ポート番号の表示-->
		<div class="box">

			<div>

				<h4>MPD</h4>
				<p>host:${MPD_HOST}</p>
				<p>port:${MPD_PORT}</p>

			</div>

			<div>

				<h4>coverart server</h4>
				<p>host:${img_server_host}</p>
				<p>port:${img_server_port}</p>

			</div>

		</div>

		<p><button onclick="location.href='/cgi-bin/settings/server_setting/server_setting.cgi'">MPD & coverart server setting</button></p>

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
			<button class="equal_width_button" onclick="location.href='/cgi-bin/queued/queued.cgi'">Queued</button>
			<button class="equal_width_button" onclick="location.href='/cgi-bin/directory/directory.cgi'">Directoty</button>
			<button class="equal_width_button" onclick="location.href='/cgi-bin/index.cgi'">HOME</button>
			<button class="equal_width_button" onclick="location.href='/cgi-bin/playlist/playlist.cgi'">Playlist</button>

		</footer>	

	</dev>

</html>
EOS
# ====== HTMLここまで ======

