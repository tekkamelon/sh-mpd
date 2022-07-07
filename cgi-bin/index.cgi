#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

echo "Content-type: text/html"
echo ""

cat << EOS
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8" />
		<meta name="viewport" content="width=device-width,initial-scale=1.0">
		<link rel="stylesheet" href="stylesheet/stylesheet.css">
		<link rel="icon" ref="image/favicon.svg">
		<!-- <link rel="apple-touch-icon" href="image/favicon.svg"> -->
        <title>sh-MPD</title>
    </head>

	<header>
		<pre style="color: rgb(0, 255, 10)"> 
         __          __  _______  ____ 
   _____/ /_        /  |/  / __ \\/ __ \\
  / ___/ __ \______/ /|_/ / /_/ / / / /
 (__  ) / / /_____/ /  / / ____/ /_/ / 
/____/_/ /_/     /_/  /_/_/   /_____/  
<span style="color: teal">
MPD UI using shellscript and CGi
</span>
	</header>

	    </pre>
    <body>
		<l2>used RAM: $(free -h | sed -n 2p | awk -F" " '{print $3}')</l2>

		<form name="FORM" method="GET" >
			<!-- 音楽の操作ボタンをtableでレイアウト -->

			<table border=1 bordercolor="green" border-collapse:collapse>

				<!-- ヘッダ -->
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
				 		<button name="button" value="volume +5">volume +5</button>
					</td>
					<td>
				 		<button name="button" value="volume -5">volume -5</button>
					</td>
					<td>
				 		<button name="button" value="volume -100">mute</button>
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
				 		<button name="button" value="clear">clear</button>
					</td>
				</tr>
			</table>

			<!-- sedでクエリを加工,xargsでmpcに渡す -->
			$(echo $QUERY_STRING | sed -e "s/button\=//g" -e "s/+\%2B/ +/g" -e "s/\+\-/ \-/g" | xargs mpc -q > /dev/null)

        </form>

		<form name="sp_and_vol" method="POST" >
			<span style="color: teal; ">
	            select format and enter keywords : 
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
						<!-- POSTを取得,awkとurldecodeで加工後,mpcに渡し,標準エラー出力ごと表示 -->
						<p>$(cat | awk -F'[=&]' '{print $2,"\047"$4"\047"}' | urldecode | xargs mpc -q 2>&1 )</p>
				    </form>
	            </select>


		<h3>next song</h3>
			<p>$(mpc queued)</p>

		<h3>mpd status</h3>
			<p>$(mpc | sed "s/$/<br>/g")</p>

		<button><a href="queued/queued.cgi">Queued</a></button>
		<button><a href="directory/directory.cgi">Directoty</a></button>
		<button><a href="playlist/playlist.cgi">Playlist</a></button>

    </body>

	<footer>
		<h4>source code</h4>
		<p><a href="https://github.com/tekkamelon/sh-mpd">git repository</a></p>
		<p><a href="https://github.com/ShellShoccar-jpn/misc-tools">"urlcode" reference source</a></p>

		<h4>debug info</h4>
			<p>QUERY_STRING: $(echo "$QUERY_STRING")</p>
			<p>hostname: $(hostname)</p>
			<p>cgi_version: $(echo $GATEWAY_INTERFACE)</p>
	</footer>

</html>
EOS

