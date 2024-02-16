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
. ../shmpd.conf
# ====== 変数の設定ここまで ======


# ===== 関数の宣言 ======
post () {

	# POSTを変数に代入
	cat_post=$(cat)

	# POSTがありかつ数値であれば真
	if [ -n "${cat_post#*\=}" ] && [ "${cat_post#*\=}" -ge 1 ]; then

		# 真の場合はPOSTを環境変数に代入
		img_server_port="${cat_post#*\=}"

		# 変数の一覧を出力,設定ファイルへリダイレクト
		cat <<- EOF >| ../shmpd.conf
		export MPD_HOST="${MPD_HOST}"
		export MPD_PORT="${MPD_PORT}"
		img_server_host="${img_server_host}"
		img_server_port="${img_server_port}"
		stylesheet="${stylesheet}"
		EOF

		# メッセージの出力
		echo "changed port number:${cat_post#*\=}<br>" &

	# 偽の場合はPOSTがあれば真
	elif [ -n "${cat_post}" ] ; then

		echo "please enter port number!"
		
	fi
		
}
# ===== 関数の宣言ここまで ======


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

