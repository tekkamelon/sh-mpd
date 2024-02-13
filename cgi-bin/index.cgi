#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# ====== 環境変数の設定 ======
# ロケールの設定
export LC_ALL=C
export LANG=C

# GNU coreutilsの挙動をPOSIXに準拠
export POSIXLY_CORRECT=1

# 独自コマンドへPATHを通す
export PATH="$PATH:../bin"

# ホスト名,ポート番号を設定
host="$(cat settings/hostname)"
port="$(cat settings/port_conf)"
export MPD_HOST="${host}"
export MPD_PORT="${port}"

# 画像サーバーのホスト名,ポート番号を設定
img_host="$(cat settings/img_host.conf)"
img_port="$(cat settings/img_port.conf)"
# ====== 環境変数の設定ここまで ======


# ===== スクリプトによる処理 ======
# "control button",入力欄から受け取ったPOSTやクエリの処理
mpc_post () {

	# 変数展開で加工したPOSTの文字列の有無を判定,あればクエリを加工しmpcへ渡す

	# POSTを変数に代入
	cat_post=$(cat) 
	
	# POSTの有無を確認,あれば真,なければ偽
	if [ -n "${cat_post#*\&*\=}" ] ; then
	
		# 真の場合はPOSTを変数展開で加工,再度代入
		cat_post="${cat_post#*\=}"

		# POSTを変数展開で加工,最後の引数をシングルクォート付きで出力,デコード
		echo "${cat_post%%\&*}" "'${cat_post#*\&*\=}'" | urldecode

	else

		# 偽の場合はクエリを変数展開で加工
		echo "${QUERY_STRING#*\=}" |

		# "volume","seek","mute"時の文字列をデコード
		sed -e "s/_\-/ \-/g" -e "s/_\%2B/ \+/g" -e "s/\%25/\%/g"
	
	fi |

	# mpcのエラー出力ごと渡す
	xargs mpc 2>&1 | 

	# ": off"に<b>タグを,": on"に<strong>タグを,各行末に改行のタグを付与
	mpc_status2html

}

# 次の曲の処理
next_song () {

	# "message"に実行結果がない場合のメッセージを代入
	message="next song not found"
	
	# "mpc queued"を変数に代入
	queued=$(mpc queued)

	# "mpc queued"の実行結果があれば"message"に"queued"を代入
	test -n "${queued}" && message="${queued}"

	# メッセージを出力
	echo "${message}"

}

# カバーアートの表示
coverart () {
	
	# ステータスから曲名を抽出
	current_song=$(mpc status | head -n 1 | awk -F" - " '{print $2}')

	# 曲一覧から曲名で検索
	search_dir=$(mpc listall | grep "${current_song}")

	# ディレクトリのみ抽出
	dir=$(dirname "${search_dir}")

	# 画像のパスを生成,それ以外を除外
	echo "${dir}/Folder.jpg"| grep "Folder.jpg"

}
# ===== スクリプトによる処理ここまで ======


# ====== HTML ======
echo "Content-type: text/html"
echo ""

cat << EOS
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8" />
		<meta name="viewport" content="width=device-width,initial-scale=1.0">
		<link rel="stylesheet" href="/cgi-bin/stylesheet/$(cat settings/css_conf)">
		<link rel="icon" ref="image/favicon.png">
		<link rel="apple-touch-icon" href="image/favicon.png">
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
MPD UI using shellscript and CGI
</span>
	</header>

    <main>
		<h4>host:${MPD_HOST}<br>port:${MPD_PORT}<br></h4>

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

								<input type="text" placeholder="search word" name="search">

							</span>

						</p>

				    </form>

	            </select>

		<form name="FORM" method="GET" >

			<h3>current song</h3>

			<!-- カバーアートの表示 -->
			<img src="http://${img_host}:${img_port}/$(coverart)" alt="coverart" />

			<!-- 現在のステータス -->
			<p>$(mpc_post)</p>

			<!-- 次の曲 -->
			<h3>next song</h3>
			<p><button name=button value=next>$(next_song)</button></p>
	
		</form>

	</main>

	<aside>

		<!-- リンク -->
		<h3>MENU</h3>
		<button onclick="location.href='queued/queued.cgi'">Queued</button>
		<button onclick="location.href='directory/directory.cgi'">Directoty</button>
		<button onclick="location.href='playlist/playlist.cgi'">Playlist</button>
		<button onclick="location.href='settings/settings.cgi'">Settings</button>

		<!-- mpdの統計を表示 -->
		<h3>MPD statistics</h3>

			<p>$(mpc stats | sed "s/$/<br>/g")</p>

		<!-- ソースコードのリンク -->
		<footer>

			<h3>source code</h3>
			<p><a href="https://github.com/tekkamelon/sh-mpd">git repository</a></p>

			<h3>reference source code</h3>
			<p><a href="https://github.com/ShellShoccar-jpn/misc-tools">"urldecode"</a></p>
			<p><a href="https://github.com/andybrewer/mvp/">"mvp.css"</a></p>
			<p><a href="https://github.com/xz/new.css">"new.css"</a></p>

		</footer>

	</aside>

</div>
</body>

</html>
EOS
# ====== HTMLここまで ======
