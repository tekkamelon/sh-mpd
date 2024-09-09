#!/bin/sh

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示
set -eu

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
# URLからホスト名を取得
cgi_host () {

	echo "${HTTP_REFERER}" | cut -d"/" -f3

}

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
post_proc () {

	# POSTを変数に代入
	cat_post=$(cat)

	# サーバーの種類及びホストかポートを抽出
	post_key="${cat_post#*\=}"
	post_key="${post_key%%&*}"

	# ホスト名およびポート番号を抽出
	post_args="${cat_post#*\&*\=}"

	# "post_key"が"mpd_host"かつmpdと疎通確認できれば真,そうでなければ偽
	if [ "${post_key}" = "mpd_host" ] && mpc -q --host="${post_args}" ; then

		# 真の場合はPOSTを環境変数に代入
		export MPD_HOST="${post_args}"

		# 変数の一覧を出力,設定ファイルへリダイレクト
 		heredocs >| ../shmpd.conf

		echo "changed MPD host:${MPD_HOST}<br>"

		mpc status | mpc_status2html

	# "post_key"が"mpd_port"かつmpdと疎通確認できれば真,そうでなければ偽
	elif [ "${post_key}" = "mpd_port" ] && mpc -q --port="${post_args}" ; then

		# 真の場合はPOSTを環境変数に代入
		export MPD_PORT="${post_args}"

		# 変数の一覧を出力,設定ファイルへリダイレクト
 		heredocs >| ../shmpd.conf

		echo "changed MPD port:${MPD_PORT}<br>"
	
		mpc status | mpc_status2html

	# "post_key"が"img_server_host"であれば真,それ以外で偽
	elif [ "${post_key}" = "img_server_host" ] ; then

		# 真の場合はPOSTを環境変数に代入
		img_server_host="${post_args}"

		# 変数の一覧を出力,設定ファイルへリダイレクト
 		heredocs >| ../shmpd.conf

		echo "changed coverart server host:${img_server_host}<br>"

	# "post_key"が"img_server_port"かつPOSTが1以上かつ65535以下であれば真,それ以外で偽
	elif [ "${post_key}" = "img_server_port" ] && [ "${post_args}" -ge 1 ] && [ "${post_args}" -le 65535 ] ; then

		# 真の場合はPOSTを環境変数に代入
		img_server_port="${post_args}"

		# 変数の一覧を出力,設定ファイルへリダイレクト
 		heredocs >| ../shmpd.conf

		echo "changed coverart server port:${img_server_port}<br>"

	# 偽の場合はPOSTがあれば真
	elif [ -n "${cat_post}" ] ; then

		# 真の場合はメッセージを表示
		echo "invalid input!"
		
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
		<title>Server setting - sh-MPD:$(cgi_host) -</title>

    </head>

	<header>

		<h1>Server setting</h1>

	</header>

    <body>

		<!-- ホスト名,ポート番号の表示-->
		<div class="box">

			<div>

				<h4>MPD</h4>
				<p>host:${MPD_HOST}</p>
				<p>port:${MPD_PORT}</p>

			</div>

			<div>

				<h4>Coverart server</h4>
				<p>host:${img_server_host}</p>
				<p>port:${img_server_port}</p>

			</div>

		</div>

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
						<p><input type="text" placeholder="default:localhost" name="post_key"></p>

					</span>

				</form>

			</select>
			
		</form>

		<!-- 実行結果を表示 -->
		<p>$(post_proc)</p>
			
    </body>


	<footer>	

		<!-- リンク -->
		<button class="equal_width_button" onclick="location.href='/cgi-bin/queued/queued.cgi'">Queued</button>
		<button class="equal_width_button" onclick="location.href='/cgi-bin/directory/directory.cgi'">Directoty</button>
		<button class="equal_width_button" onclick="location.href='/cgi-bin/index.cgi'">HOME</button>
		<button class="equal_width_button" onclick="location.href='/cgi-bin/playlist/playlist.cgi'">Playlist</button>
		<button class="equal_width_button" onclick="location.href='/cgi-bin/settings/settings.cgi'">Settings</button>

	</footer>	

</html>
EOS
# ====== HTMLここまで ======

