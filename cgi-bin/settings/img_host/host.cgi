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

# ホスト名,ポート番号を設定
img_server_host="$(cat ../img_host.conf)"
img_server_port="$(cat ../img_port.conf)"
# ====== 変数の設定ここまで ======


# ===== スクリプトによる処理 ======
post () {

	# POSTを変数に代入
	cat_post=$(cat)

	# POSTを変数展開で加工,あれば真,なければ偽
	if [ -n "${cat_post#*\=}" ] ; then

		# 真の場合はPOSTを変数展開で加工,設定ファイルへのリダイレクト
		echo "${cat_post#*\=}" >| ../img_host.conf &

		# メッセージの出力
		echo "changed coverart server host:${cat_post#*\=}<br>" &

	# 偽の場合はPOSTがあれば真
	elif [ -n "${cat_post}" ] ; then

		echo "please enter hostname!"
		
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

		<h1>coverart server setting</h1>

	</header>

    <body>

		<!-- ホスト名,ポート番号の表示-->
		<h4>host:${img_server_host}<br>port:${img_server_port}<br></h4>

		<form name="setting" method="POST" >

			<span>

				<!-- ホスト名又はIPアドレスの入力欄 -->
				<p><input type="text" placeholder="enter hostname or local IP default:localhost" name="8080"></p>

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

