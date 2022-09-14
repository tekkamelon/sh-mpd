#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# 環境変数で接続先ホストを設定,ファイルがない場合はローカルホスト
export MPD_HOST=$(# hostnameを変数に代入
	hostname_var=$(cat settings/hostname)
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
		<link rel="stylesheet" href="/cgi-bin/stylesheet/$(cat settings/css_conf | grep . || echo "stylesheet.css")">
		<link rel="icon" ref="image/favicon.svg">
		<!-- <link rel="apple-touch-icon" href="image/favicon.svg"> -->
        <title>sh-MPD</title>
    </head>

	<header>
		<pre> 
         __          __  _______  ____ 
   _____/ /_        /  |/  / __ \\/ __ \\
  / ___/ __ \______/ /|_/ / /_/ / / / /
 (__  ) / / /_____/ /  / / ____/ /_/ / 
/____/_/ /_/     /_/  /_/_/   /_____/  
<span>
MPD UI using shellscript and CGi
</span>
	    </pre>

	</header>

    <body>
		<h4>hostname: $(echo $MPD_HOST)</h4>
		<p>used RAM: $(free -h | awk -F" " 'NR == 2 {print $3}')</p>
		
		<!-- 入力フォーム -->
		<form name="FORM" method="GET" >

			<!-- 音楽の操作ボタンをtableでレイアウト -->
			<table border="1" cellspacing="5">

				<!-- ヘッダ行 -->
				<thead>
					<tr>
						<th colspan=4>control button</th>
					</tr>
				</thead>

				<!-- 1行目 -->
				<tr>
					<td>
				 		<button name="button" value="status">status</button>
					</td>
					<td>
				 		<button name="button" value="volume -100">mute</button>
					</td>
					<td>
				 		<button name="button" value="volume -5">volume -5</button>
					</td>
					<td>
				 		<button name="button" value="volume +5">volume +5</button>
					</td>
				</tr>	

				<!-- 2行目 -->
				<tr>
					<td>
						<button name="button" value="prev">previous</button>
					</td>
					<td>
				 		<button name="button" value="toggle" >play/pause</button>
					</td>
					<td>
				 		<button name="button" value="stop">stop</button>
					</td>
					<td>
				 		<button name="button" value="next">next</button>
					</td>
				</tr>
				 
				<!-- 3行目 -->
				<tr>
					<td>
				 		<button name="button" value="repeat">repeat</button>
					</td>
					<td>
				 		<button name="button" value="random">random</button>
					</td>
					<td>
				 		<button name="button" value="single">single</button>
					</td>
					<td>
				 		<button name="button" value="shuffle">shuffle</button>
					</td>
				</tr>

				<!-- 4行目 -->
				<tr>
					<td>
				 		<button name="button" value="clear">clear</button>
					</td>
					<td>
				 		<button name="button" value="update">update</button>
					</td>
					<td>
				 		<button name="button" value="seek -5%">seek -5%</button>
					</td>
					<td>
				 		<button name="button" value="seek +5%">seek +5%</button>
					</td>
				</tr>
			</table>

			$(# 変数展開でクエリを加工,デコードしxargsでmpcに渡す
			echo ${QUERY_STRING#*\=} | urldecode | xargs mpc -q > /dev/null)

        </form>

		<form name="format" method="POST" >
			<span style="color: teal; ">
				searchplay queued song :
			</span>
	            <select name="args">
	
	                <option value="searchplay">fuzzy</option>

	                <option value="searchplay title">title</option>

	                <option value="searchplay artist">artist</option>

	                <option value="searchplay album">album</option>
							
					</form>
					<form method="POST">
						<p>
							<span style="color: rgb(0, 255, 10); ">
								<input type="text" name="search">
							</span>
						</p>
						<p>$(# POSTを取得,awkとurldecodeで加工後,mpcに渡し,標準エラー出力ごと表示
						cat | awk -F'[=&]' '{print $2,"\047"$4"\047"}' | urldecode | xargs mpc -q 2>&1 
						)</p>

				    </form>
	            </select>

		<h3>current song</h3>
			<p>$(mpc status | sed "s/$/<br>/g")</p>

		<h3>next song</h3>
			<p>$(mpc queued)</p>

		<!-- リンク -->
		<button><a href="queued/queued.cgi">Queued</a></button>
		<button><a href="directory/directory.cgi">Directoty</a></button>
		<button><a href="playlist/playlist.cgi">Playlist</a></button>
		<button><a href="settings/settings.cgi">Settings</a></button>

    </body>

	<footer>
		<h4>source code</h4>
		<p><a href="https://github.com/tekkamelon/sh-mpd">git repository</a></p>
		<p><a href="https://github.com/ShellShoccar-jpn/misc-tools">"urlcode" reference source</a></p>

		<h4>debug info</h4>

			<p>QUERY_STRING: $(echo "$QUERY_STRING")</p>

	</footer>

</html>
EOS

