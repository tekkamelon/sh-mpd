#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# 環境変数の設定
# ホスト名,ポート番号を設定,データがない場合は"localhost","6600"
export LANG=C
export MPD_HOST=$(cat ../hostname) 
export MPD_PORT=$(cat ../port_conf)

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
		<!-- ホスト名,ポート番号の表示-->
		<h4>host:${MPD_HOST}<br>port:${MPD_PORT}<br></h4>
		<form name="setting" method="POST" >

				<span>
					<p>enter hostname or local IP: <input type="text" placeholder="example: foobar.local" name="MPD_HOST"></p>
				</span>
			
			<!-- 実行結果を表示 -->
			<p>$(# POSTを変数に代入

			cat_post=$(cat)

			# POSTを変数展開で加工,ホスト名が有効であれば真,無効であれば偽
			if mpc -q --host="${cat_post#*\=}" ; then

				# 真の場合はPOSTを変数展開で加工,設定ファイルへのリダイレクト
				echo "${cat_post#*\=}" >| ../hostname &

				# メッセージの出力
				echo "<p>changed host:${cat_post#*\=}</p>"

				# POSTを環境変数に代入
				export MPD_HOST="${cat_post#*\=}"
				
			# 偽の場合はPOSTがあれば真,無ければ偽
			elif [ -n "${cat_post}" ] ; then

				# 真の場合はメッセージを表示
				echo "<p>failed to resolve hostname!</p>"

			else

				# 偽の場合は何もしない
				:
				
			fi

			# ステータスを表示
			mpc 2>&1 | sed "s/$/<br>/g"	
			
			)</p>
			
		</form>
    </body>

	<footer>	
		<!-- リンク -->
		<button><a href="/cgi-bin/queued/queued.cgi">Queued</a></button>
		<button><a href="/cgi-bin/directory/directory.cgi">Directory</a></button>
		<button><a href="/cgi-bin/index.cgi">HOME</a></button>
		<button><a href="/cgi-bin/playlist/playlist.cgi">Playlist</a></button>
		<button><a href="/cgi-bin/settings/settings.cgi">Settings</a></button>
	</footer>	

</html>
EOS

