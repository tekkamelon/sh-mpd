#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# ====== 環境変数の設定 ======
export LANG=C

# ホスト名,ポート番号を設定,データがない場合は"localhost","6600"
host="$(cat ../hostname)"
port="$(cat ../port_conf)"

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
		<link rel="stylesheet" href="/cgi-bin/stylesheet/$(cat ../css_conf)">
		<link rel="icon" ref="image/favicon.svg">
		<!-- <link rel="apple-touch-icon" href="image/favicon.svg"> -->
        <title>sh-MPD</title>

    </head>

	<header>

		<h1>settings</h1>

	</header>

    <body>

		<h4>host:${MPD_HOST}<br>port:${MPD_PORT}<br></h4>

		<!-- ポート番号の設定 -->
		<form name="setting" method="POST" >

			<span>

				<!-- ポート番号の入力欄 -->
				<p><input type="text" placeholder="enter or port number default:6600" name="MPD_HOST"></p>
					
			</span>

		</form>
			
		<!-- 実行結果を表示 -->
		<p>$(# POSTを変数に代入

		cat_post=$(cat)

		# POSTを変数展開で加工,ポート番号が有効であれば真,無効であれば偽
		if [ -n "${cat_post#*\=}" ] && mpc -q --port="${cat_post#*\=}" ; then

			# POSTを変数展開で加工,設定ファイルへのリダイレクト
			echo "${cat_post#*\=}" >| ../port_conf &

			# メッセージの出力
			echo "changed port number:${cat_post#*\=}<br>" &
			
			# POSTを環境変数に代入
			export MPD_PORT="${cat_post#*\=}"

		# 偽の場合はPOSTがあれば真,無ければ偽
		elif [ -n "${cat_post}" ] ; then
			
			# 偽であればメッセージを表示
			echo "not a valid port number!<br>"

		else

			# 偽の場合は何もしない
			:
			
		fi

		# ステータスを表示
		mpc status 2>&1 |
			
		# 3行目の": off"に<b>タグを,": on"に<strong>タグを,各行末に改行のタグを付与
		sed -e "3 s/: off/:<b> off<\/b>/g" -e "3 s/: on/:<strong> on<\/strong>/g" -e "s/$/<br>/g"

		)</p>
			
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

