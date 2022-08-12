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
		<link rel="stylesheet" href="/cgi-bin/stylesheet/stylesheet.css">
		<link rel="icon" ref="image/favicon.svg">
		<!-- <link rel="apple-touch-icon" href="image/favicon.svg"> -->
        <title>sh-MPD</title>
    </head>

	<header>
		<h1>settings</h1>
	</header>

    <body>
		<form name="setting" method="POST" >
			
			<!-- 出力先デバイスの設定 -->
			<h3>ountput devices list</h3>
			$(# mpc outputsの出力結果から出力先デバイスの情報のみを表示,POSTで出力先デバイスの番号のみを渡す
			mpc outputs | 
	
			# "Output"を含む行を抽出,ボタン化し出力
			awk '/Output/{
				print "<p><button name=toggleoutput value="$2">"$0"</button></p>"
			}' 
			)
			
			<!-- 実行結果を表示 -->
			<p>$(# POSTで受け取った文字列を変数に代入
				# 出力先の変更,変数に"export"がない場合に実行
				cat | tr "=" " " | xargs mpc 2>&1 | awk '/Output/{print $0"<br>"}'
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

