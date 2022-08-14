#!/bin/sh -eux

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# 環境変数で接続先ホストを設定,ファイルがない場合はローカルホスト
export MPD_HOST=$(# hostnameを変数に代入
	hostname_var=$(cat ../hostname)
	# 変数展開で加工
	echo ${hostname_var#export\&MPD_HOST\=} | grep . || echo "localhost"
) 

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
		<!-- ホスト名の設定 -->
		<h3>hostname: $(echo $MPD_HOST)</h4>
		<form name="setting" method="POST" >

			<h3>HOST</h3>
				<span style="color: rgb(0, 255, 10); ">
					<p>
						<button name=host value="export">
						host
						</button>
					</p>
							<input type="text" name="MPD_HOST">
				</span>
			
			<!-- 実行結果を表示 -->
			<p>$(# POSTで受け取った文字列を変数に代入
			cat_post=$(cat)

				# host名の変更,変数展開で加工,teeで保存しgrepの終了ステータスでhostかどうか判断
				echo ${cat_post#*\=} | tee ../hostname | grep export ||

				# 出力先の変更,変数に"export"がない場合に実行
				echo $cat_post | awk -F'[=&]' '{print $3,$4}' | xargs mpc 2>&1 | awk '/Output/{print $0"<br>"}'
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

