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

# 独自コマンドへPATHを通す
export PATH="$PATH:../../../bin"

# ". (ドット)"コマンドで設定ファイルの読み込み
. ../shmpd.conf
# ====== 変数の設定ここまで ======


# ===== 関数の宣言 ======
# ヒアドキュメントで設定ファイルの変数を出力
heredocs () {

	cat <<- EOF
	export MPD_HOST="${MPD_HOST}"
	export MPD_PORT="${MPD_PORT}"
	img_server_host="${img_server_host}"
	img_server_port="${img_server_port}"
	stylesheet="${stylesheet}"
	EOF

}

# POSTの文字列に応じて処理を分岐
branch_post () {

	# POSTを変数に代入
	cat_post=$(cat)

	# hostかportを変数展開で抽出
	host_or_port="${cat_post#*\=}"
	host_or_port="${host_or_port%%&*}"

	# "host_or_port"が"host"であれば真,それ以外で偽
	if [ "${host_or_port}" = "mpd_host" ] && mpc -q --host="${cat_post#*\&*\=}" ; then

		# 真の場合はPOSTを環境変数に代入
		export MPD_HOST="${cat_post#*\&*\=}"

		# 変数の一覧を出力,設定ファイルへリダイレクト
 		heredocs >| ../shmpd.conf

		# メッセージの出力
		echo "changed MPD host:${MPD_HOST}<br>"

		mpc status | mpc_status2html

	# "host_or_port"が"port"かつPOSTが数値であればであれば真,それ以外で偽
	elif [ "${host_or_port}" = "mpd_port" ] && mpc -q --port="${cat_post#*\&*\=}" ; then

		# 真の場合はPOSTを環境変数に代入
		export MPD_PORT="${cat_post#*\&*\=}"

		# 変数の一覧を出力,設定ファイルへリダイレクト
 		heredocs >| ../shmpd.conf

		# メッセージの出力
		echo "changed MPD port:${MPD_PORT}<br>"
	
		mpc status | mpc_status2html

	elif [ "${host_or_port}" = "img_server_host" ] ; then

		# 真の場合はPOSTを環境変数に代入
		img_server_host="${cat_post#*\&*\=}"

		# 変数の一覧を出力,設定ファイルへリダイレクト
 		heredocs >| ../shmpd.conf

		# メッセージの出力
		echo "changed coverart server host:${img_server_host}<br>"

	# "host_or_port"が"port"かつPOSTが数値であればであれば真,それ以外で偽
	elif [ "${host_or_port}" = "img_server_port" ] && [ "${cat_post#*\&*\=}" -ge 1 ] ; then

		# 真の場合はPOSTを環境変数に代入
		img_server_port="${cat_post#*\&*\=}"

		# 変数の一覧を出力,設定ファイルへリダイレクト
 		heredocs >| ../shmpd.conf

		# メッセージの出力
		echo "changed coverart server port:${img_server_port}<br>"

	# 偽の場合はPOSTがあれば真
	elif [ -n "${cat_post}" ] ; then

		# 真の場合はメッセージを表示
		echo "please enter hostname or port number!<br>"
		
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
        <title>sh-MPD</title>

    </head>

	<header>

		<h1>Server setting</h1>

	</header>

    <body>

		<!-- ホスト名,ポート番号の表示-->
		<h3>MPD</h3>
		<p>host:${MPD_HOST}<br>port:${MPD_PORT}</p>

		<h3>Coverart server</h3>
		<p>host:${img_server_host}<br>port:${img_server_port}</p>
		<form name="setting" method="POST" >

			<span>

				select setting items :

			</span>

			<!-- ドロップダウンメニュー -->
			<select name="args">

				<option value="mpd_host">MPD host</option>

				<option value="mpd_port">MPD port</option>

				<option value="img_server_host">coverart server host</option>

				<option value="img_server_port">coverart server port</option>

				</form>

				<!-- 入力フォーム -->
				<form method="POST">

					<span>

						<!-- ホスト名又はIPアドレスの入力欄 -->
						<p><input type="text" placeholder="default:localhost" name="host_or_port"></p>

					</span>

				</form>

			</select>
			
		</form>

		<!-- 実行結果を表示 -->
		<p>$(branch_post)</p>
			
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

