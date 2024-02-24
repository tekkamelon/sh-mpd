#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# ====== 変数の設定 ======
# ロケールの設定
export LC_ALL=C
export LANG=C

# GNU coreutilsの挙動をPOSIXに準拠
export POSIXLY_CORRECT=1

# 独自コマンドへPATHを通す
export PATH="$PATH:../bin"

# ". (ドット)"コマンドで設定ファイルの読み込み
. settings/shmpd.conf
# ====== 変数の設定ここまで ======


# ===== 関数の宣言 ======
# 変数展開で加工したPOSTの文字列の有無を判定,あればクエリを加工しmpcへ渡す
mpc_post () {

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

# カバーアートの取得
coverart () {

	# 再生中の曲の相対パスを抽出
	current_song=$(mpc current -f "%file%")

	# ディレクトリのみ抽出
	dirname "${current_song}" |

	awk '{

		# "dir"の行頭が"http"であれば真,それ以外で偽
		if(/^http:/){

			# 真の場合はウェブラジオ用の画像を指定
			printf "image/web_radio.svg"

		}else{

			# 偽の場合はカバーアート用の画像サーバーを指定
			printf "http://'${img_server_host}':'${img_server_port}'/"$0"/Folder.jpg"

		}

	}'

}

# 次の曲の表示
next_song () {

	# "mpc queued"を変数に代入
	queued=$(mpc queued)

	# "queued"があれば真,なければ偽
	if [ -n "${queued}" ] ; then

		# 真の場合は"queued"を表示
		echo "${queued}"

	else

		# 偽の場合はメッセージを表示
		echo "next song not found"

	fi

}
# ===== 関数の宣言ここまで ======


# ====== HTML ======
echo "Content-type: text/html"
echo ""

cat << EOS
<!DOCTYPE html>
<html>

    <head>

        <meta charset="UTF-8" />
		<meta name="viewport" content="width=device-width,initial-scale=1.0">
		<link rel="stylesheet" href="/cgi-bin/stylesheet/${stylesheet}">
		<link rel="icon" ref="image/favicon.png">
		<link rel="apple-touch-icon" href="image/favicon.png">
        <title>sh-MPD</title>

    </head>

	<body>

		<div class="layout">

			<!-- ヘッダー -->
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

			<!-- control buttonからnext_songまで -->
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

				<!-- 入力フォーム -->
				<form name="format" method="POST" >

					<span>

						searchplay queued song :

					</span>

					<!-- ドロップダウンメニュー -->
					<select name="args">

						<option value="searchplay">fuzzy</option>

						<option value="searchplay artist">artist</option>

						<option value="searchplay album">album</option>
						
						<option value="searchplay title">title</option>
								
						<option value="searchplay filename">filename</option>

						<span>

							<input type="text" placeholder="search word" name="search">

						</span>

					</select>

				</form>

				<form name="FORM" method="GET" >

					<h3>Current</h3>

					<!-- 現在のステータス -->
					<p>$(mpc_post)</p>

					<!-- カバーアートの表示 -->
					<div class="resize">

						<img src="$(coverart)" alt="coverart" >

					</div>

					<!-- 次の曲 -->
					<h3>Next</h3>
					<p><button name=button value=next>$(next_song)</button></p>

				</form>

			</main>

			<!-- サイドバー -->
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
