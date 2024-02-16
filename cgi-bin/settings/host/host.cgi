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
mpc_post () {

	# POSTを変数に代入
	cat_post=$(cat)

	# POSTを変数展開で加工,ホスト名が有効であれば真,無効であれば偽
	if [ -n "${cat_post#*\=}" ] && mpc -q --host="${cat_post#*\=}" ; then

		# 真の場合はPOSTを環境変数に代入
		export MPD_HOST="${cat_post#*\=}"

		# 変数の一覧を出力,設定ファイルへリダイレクト
		cat <<- EOF >| ../shmpd.conf
		export MPD_HOST="${MPD_HOST}"
		export MPD_PORT="${MPD_PORT}"
		img_server_host="${img_server_host}"
		img_server_port="${img_server_port}"
		stylesheet="${stylesheet}"
		EOF

		# メッセージの出力
		echo "changed host:${cat_post#*\=}<br>" &

	# 偽の場合はPOSTがあれば真,無ければ偽
	elif [ -n "${cat_post}" ] ; then

		# 真の場合はメッセージを表示
		echo "failed to resolve hostname!<br>"

	fi

	# ステータスを表示
	mpc status 2>&1 |
	
	# ": off"に<b>タグを,": on"に<strong>タグを,各行末に改行のタグを付与
	mpc_status2html

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

		<!-- ホスト名,ポート番号の表示-->
		<h4>host:${MPD_HOST}<br>port:${MPD_PORT}<br></h4>

		<form name="setting" method="POST" >

			<span>

				<!-- ホスト名又はIPアドレスの入力欄 -->
				<p><input type="text" placeholder="enter hostname or local IP default:localhost" name="MPD_HOST"></p>

			</span>
			
		</form>

		<!-- 実行結果を表示 -->
		<p>$(mpc_post)</p>
			
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

