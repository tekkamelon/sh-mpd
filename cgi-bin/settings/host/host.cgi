#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# 環境変数の設定
# ホスト名,ポート番号を設定,データがない場合は"localhost","6600"
export MPD_HOST=$(cat ../hostname | grep . || echo "localhost") 
export MPD_PORT=$(cat ../port_conf | grep . || echo "6600") 
export LANG=C

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

			# POSTの有無を確認
			test -n "${cat_post}" &&

			# POSTを変数展開で加工,ホスト名が有効であれば真,無効であれば偽
			if mpc -q --host="${cat_post#*\=}" ; then

				# POSTを変数展開で加工,設定ファイルへのリダイレクト
				echo "${cat_post#*\=}" >| ../hostname &

				# メッセージの出力
				echo "<p>changed host:${cat_post#*\=}</p>"
				
			else
				
				# 偽であればメッセージを表示
				echo "failed to resolve hostname<br>please enter hostname or local IP adress!<br>"
				
			fi
				
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

