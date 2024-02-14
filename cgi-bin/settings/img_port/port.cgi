#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# ====== 環境変数の設定 ======
# ロケールの設定
export LC_ALL=C
export LANG=C

# GNU coreutilsの挙動をPOSIXに準拠
export POSIXLY_CORRECT=1

# ホスト名,ポート番号を設定
img_server_host="$(cat ../img_host.conf)"
img_server_port="$(cat ../img_port.conf)"
# ====== 環境変数の設定ここまで ======


# ===== スクリプトによる処理 ======
post () {

	# POSTを変数に代入
	cat_post=$(cat)

	# POSTがありかつ数値であれば真
	if [ -n "${cat_post#*\=}" ] && [ "${cat_post#*\=}" -ge 1 ]; then

		# POSTを変数展開で加工,設定ファイルへのリダイレクト
		echo "${cat_post#*\=}" >| ../img_port.conf &

		# メッセージの出力
		echo "changed port number:${cat_post#*\=}<br>" &

	# 偽の場合はPOSTがあれば真
	elif [ -n "${cat_post}" ] ; then

		echo "please enter port number!"
		
	fi
		
}
# ===== スクリプトによる処理ここまで ======


# ====== HTML ======
echo "Content-type: text/html"
echo ""

cat << EOS
<!DOCTYPE html>
<html>

    <head>

        <meta charset="UTF-8" />
		<meta name="viewport" content="width=device-width,initial-scale=1.0">
		<link rel="stylesheet" href="/cgi-bin/stylesheet/$(cat ../css_conf)">
		<link rel="icon" ref="image/favicon.svg">
		<!-- <link rel="apple-touch-icon" href="image/favicon.svg"> -->
        <title>sh-MPD</title>

    </head>

	<header>

		<h1>settings</h1>

	</header>

    <body>

		<h4>host:${img_server_host}<br>port:${img_server_port}<br></h4>

		<!-- ポート番号の設定 -->
		<form name="setting" method="POST" >

			<span>

				<!-- ポート番号の入力欄 -->
				<p><input type="text" placeholder="enter or port number default:6600" name="MPD_HOST"></p>
					
			</span>

		</form>
			
		<!-- 実行結果を表示 -->
		<p>$(post)</p>
			
    </body>

	<footer>	

		<!-- リンク -->
		<button onclick="location.href='/cgi-bin/queued/queued.cgi'">Queued</button>
		<button onclick="location.href='/cgi-bin/directory/directory.cgi'">Directoty</button>
		<button onclick="location.href='/cgi-bin/index.cgi'">HOME</button>
		<button onclick="location.href='/cgi-bin/playlist/playlist.cgi'">Playlist</button>
		<button onclick="location.href='/cgi-bin/settings/settings.cgi'">Settings</button>

	</footer>	

</html>
EOS
# ====== HTMLここまで ======

