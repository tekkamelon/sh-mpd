#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# 環境変数で接続先ホストを設定,ファイルがない場合はローカルホスト
export LANG=C
export MPD_HOST=$(cat ../hostname | grep . || echo "localhost") 
export MPD_PORT=$(cat ../port_conf | grep . || echo "6600") 

echo "Content-type: text/html"
echo ""

cat << EOS
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8" />
		<meta name="viewport" content="width=device-width,initial-scale=1.0">
		<link rel="stylesheet" href="/cgi-bin/stylesheet/$(cat ../css_conf | grep . || echo "stylesheet.css")">
		<link rel="icon" ref="image/favicon.svg">
		<!-- <link rel="apple-touch-icon" href="image/favicon.svg"> -->
        <title>sh-MPD</title>
    </head>

	<header>
		<h1>settings</h1>
	</header>

    <body>
		<form name="setting" method="POST" >
			
			<h4>host:${MPD_HOST}<br>port:${MPD_PORT}<br></h4>

			<!-- 出力先デバイスの設定 -->
			<h3>ountput devices list</h3>
			$(# sedでの空文字の判定の為にPOSTを変数に代入

			cat_post=$(cat)

			echo "${cat_post}" |
	
			# "="を" "に,空白行の場合は"outputs"を出力しmpcに渡す
			sed -e "s/=/ /g" -e "s/^$/outputs/g" | xargs mpc |

			# スペースを区切り文字に設定,1フィールド目が"Output"の行をボタン化
			awk -F" " '$1 == "Output"{

				print "<p><button name=toggleoutput value="$2">"$0"</button></p>"

 			}'

			)

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

