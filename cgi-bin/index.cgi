#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# 環境変数で接続先ホスト,ポート番号を設定,データがない場合は"localhost","6600"
export LANG=C
export MPD_HOST=$(cat settings/hostname | grep . || echo "localhost") 
export MPD_PORT=$(cat settings/port_conf | grep . || echo "6600") 

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

<body>
<div class="layout">
	<header>
		<pre> 
         __          __  _______  ____ 
   _____/ /_        /  |/  / __ \\/ __ \\
  / ___/ __ \______/ /|_/ / /_/ / / / /
 (__  ) / / /_____/ /  / / ____/ /_/ / 
/____/_/ /_/     /_/  /_/_/   /_____/  
	    </pre>
<span>
MPD UI using shellscript and CGi
</span>
	</header>

    <main>
		<h4>host:${MPD_HOST}<br>port:${MPD_PORT}<br></h4>
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
				 		<button name="button" value="volume_-100">mute</button>
					</td>
					<td>
				 		<button name="button" value="volume_-5">volume -5</button>
					</td>
					<td>
				 		<button name="button" value="volume_+5">volume +5</button>
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
				 		<button name="button" value="seek_-5%">seek -5%</button>
					</td>
					<td>
				 		<button name="button" value="seek_+5%">seek +5%</button>
					</td>
				</tr>
			</table>

        </form>

		<form name="format" method="POST" >
			<span>
				searchplay queued song :
			</span>

	            <select name="args">
	
	                <option value="searchplay">fuzzy</option>

	                <option value="searchplay artist">artist</option>

	                <option value="searchplay album">album</option>
					
	                <option value="searchplay title">title</option>
							
	                <option value="searchplay filename">filename</option>

					</form>
					<form method="POST">
						<p>
							<span>
								<input type="text" name="search">
							</span>
						</p>
				    </form>
	            </select>

		<form name="FORM" method="GET" >

			<!-- 現在のステータス -->
			<h3>current song</h3>
	
			<p>$(# 変数展開で加工したPOSTの文字列の有無を判定,あればクエリを加工しmpcへ渡す

			# POSTを変数に代入
			cat_post=$(cat) 
			
			# POSTとクエリを出力,sedで空白行を削除
			{ echo "${cat_post#*\=}" ; echo "${QUERY_STRING}" ; } | sed "/^$/d" |

			# 区切り文字を"=","&"に設定,1行目のみに処理
			awk -F"[=&]" 'NR == 1{

				# 1フィールド目に"button"があれば真,なければ偽
				if($1 == "button"){

					# 真の場合は"_"をスペースに置換,最終フィールドを出力
					sub("_" , " ")
					
					print $NF

				}

				else{

					# 偽の場合は1フィールド目,最終フィールドを出力
					print $1,$NF

				}

			}' | 

			# デコードしmpcのエラー出力ごとsedに渡す
			urldecode | xargs mpc 2>&1 | sed "s/$/<br>/g"

			)</p>

			<!-- 次の曲 -->
			<h3>next song</h3>
			<p><button name=button value=next>$(mpc queued | grep . || echo "next song not found")</button></p>
	
		</form>

	</main>

	<aside>
		<h3>MENU</h3>
		<!-- リンク -->
		<button><a href="queued/queued.cgi">Queued</a></button>
		<button><a href="directory/directory.cgi">Directoty</a></button>
		<button><a href="playlist/playlist.cgi">Playlist</a></button>
		<button><a href="settings/settings.cgi">Settings</a></button>

		<footer>
			<h4>source code</h4>
			<p><a href="https://github.com/tekkamelon/sh-mpd">git repository</a></p>
			<p><a href="https://github.com/ShellShoccar-jpn/misc-tools">"urldecode" reference source</a></p>
		</footer>
	</aside>

</div>
</body>

</html>
EOS

