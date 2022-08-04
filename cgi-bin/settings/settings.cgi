#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# 環境変数で接続先ホストを設定,ファイルがない場合はローカルホスト
export MPD_HOST=$(cat ../hostname | cut -d"=" -f2 | grep . || echo $(hostname).local)

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

			<h3>host</h3>
				<span style="color: rgb(0, 255, 10); ">
					<p>
						<button name=host value="export">
						host
						</button>
					</p>
							<input type="text" name="MPD_HOST">
				</span>
	
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
			cat_post=$(cat)

				# host名の変更
				# ,変数展開で加工,teeで保存しgrepの終了ステータスでhostかどうか判断
				echo ${cat_post#host\=} | tee ../hostname | grep export ||
				#| tr "&" " " | grep "export" ||

				# 出力先の変更
				# 変数にexportがない場合に実行
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
	</footer>	

</html>
EOS

