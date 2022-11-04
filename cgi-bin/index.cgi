#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# 環境変数で接続先ホスト,ポート番号を設定,データがない場合は"localhost","6600"
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
		<h4>$(echo "host:$MPD_HOST<br>port:$MPD_PORT<br>")</h4>
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

			$(# 変数展開でクエリを加工,"_"を" "に置換しxargsでmpcに渡し,エラー出力以外を/dev/nullへ
			echo "${QUERY_STRING#*\=}" | tr "_" " " | xargs mpc -q > /dev/null
			)

        </form>

		<form name="format" method="POST" >
			<span>
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
							<span>
								<input type="text" name="search">
							</span>
						</p>
						<p>$(# POSTで受け取った文字列を変数に代入
						cat_post=$(cat)					

						# POSTを変数展開で加工,デコード
						echo ${cat_post#*\=} | urldecode |

						# awkで1フィールド目,3フィールド目をシングルクォート付きで出力
						awk -F'[=&]' '{
							print $1,"\047"$3"\047"
						}' | 

						# xargsでmpcに渡し,エラー出力のみ捨てる
						xargs mpc -q 2> /dev/null
						)</p>

				    </form>
	            </select>

		<form name="FORM" method="GET" >

			<!-- 現在の曲 -->
			<h3>current song</h3>
				<p>$(# ステータスの"playing"及び"paused"をボタン化
				mpc status |

				# "playing"若しくは"paused"をボタン化
				awk '/playing|paused/{

					# "playing"若しくは"paused"を区切り文字に指定
					FS = "playing|paused"

					# "toggle"ボタン化して出力
					print "<button name=button value=toggle>"$1"</button>"

					# 2番目以降のフィールドを表示
					for(i=2;i<NF;++i){printf("%s ",$i)}

					# 行末を改行し表示
					print $NF"<br>"

				}

				# "playing"若しくは"paused"にマッチしない行を改行し表示
				! /playing|paused/{

					print $0"<br>"

				}'
				)</p>
	
			<!-- 次の曲 -->
			<h3>next song</h3>
			<p><button name=button value=next>$(mpc queued | grep . || echo "next song not found")</button></p>
	
		</form>

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

	</footer>

</html>
EOS

