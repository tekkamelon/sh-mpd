#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# ====== 環境変数の設定 ======
export LC_ALL=C
export LANG=C

# ホスト名,ポート番号を設定,データがない場合は"localhost","6600"
host="$(cat ../settings/hostname)"
port="$(cat ../settings/port_conf)"
export MPD_HOST="${host}"
export MPD_PORT="${port}"
export PATH="$PATH:../../bin"
# ====== 環境変数の設定ここまで ======


# ===== スクリプトによる処理 ======
# POSTを加工しmpcに渡す
mpc_post () {

	# ====== 変数の宣言 ======			
	# POSTを変数に代入
	cat_post=$(cat)

	# クエリの先頭のみを抽出
	query_check="${QUERY_STRING#*\=}"
	query_check="${query_check%%&*}"

 	# クエリを変数展開で加工,sedでの処理結果を変数に代入
	save_playlist=$(

		echo "${QUERY_STRING#*\=}" |
	
 		# "&input_string"をスペースに,"search[任意の１文字以上]"を置換しデコード
		sed -e "s/&input_string=/ /" -e "s/search.*//g" | urldecode

	)

	# POSTを変数展開で加工,"save_playlist"があれば出力しmpcに渡す
	mpc_result=$(

		# POSTがあれば真,無ければ偽
		if [ -n "${cat_post}" ] ; then
			
			# 真の場合はPOSTを変数展開で加工し出力
			echo "${cat_post%%\=*}" "${cat_post#*\=}"  

		else

			# 偽の場合は"save_playlist"を出力
			echo "${save_playlist}"

		fi | 

		# 出力結果をmpcに渡す,エラー出力を変数に代入するためにcatを通す
		xargs mpc 2>&1 | cat -

	)

	# mpc_resultの結果を確認
	mpc_error_check=$(

		echo "${mpc_result}" |

		# 1行目の先頭が"MPD error: "であれば真
		awk 'NR == 1{

			if(/^MPD error: /){

				# 真の場合はそのまま出力
				print $0

			}

		}'

	)

	# プレイリスト作成後にキュー内の曲を再生するための処理
	# "cat_post"と"save_playlist"の両方があれば真
	if [ -n "${cat_post}" ] && [ -n "${save_playlist}" ] ; then

		# 真の場合は"save_playlist"に空文字を代入
		save_playlist=""

	fi
	# ====== 変数の宣言ここまで ======			


	# "mpc_error_check"があり,なおかつ"query_check"が"save"の場合に真,それ以外で偽
	if [ -n "${mpc_error_check}" ] && [ "${query_check}" = "save" ] ; then

		echo "${mpc_result}"

	# 偽の場合は"save_playlist"があれば真,それ以外で偽
	elif [ -n "${save_playlist}" ] ; then

		# ステータスとメッセージを出力
		mpc status

		echo "saved playlist:${save_playlist#* }"

	else

		echo "${mpc_result}"

	fi |

	# ": off"に<b>タグを,": on"に<strong>タグを,各行末に改行のタグを付与
	mpc_status2html

}

# キュー内の曲の検索
queued_song () {

	# クエリの先頭のみを抽出
	query_check="${QUERY_STRING#*\=}"
	query_check="${query_check%%&*}"

	# "query_check"が"save"で真,それ以外で偽
	if [ "${query_check}" = "save" ] ; then

		# 真の場合は"search_str"に空文字を代入
		search_str=""

	else

		# 偽の場合はクエリを変数展開で加工,デコード,変数に代入
		search_str="$(echo "${QUERY_STRING#*\=*&*\=}" | urldecode)"

	fi

	# キューされた曲をgrepで検索,idと区切り文字":"を付与
	mpc playlist | grep -F -i -n "${search_str}" |

	# ":"を">"に置換,標準入力をタグ付きで出力
	awk '{

		sub(":" , ">")

		print "<p><button name=play value="$0"</button></p>"

	}'

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
		<link rel="stylesheet" href="/cgi-bin/stylesheet/$(cat ../settings/css_conf)">
		<link rel="icon" ref="image/favicon_ios.ico">
		<link rel="apple-touch-icon" href="image/favicon_ios.ico">
		<title>sh-MPD</title>

    </head>

	<!-- "jump to top"のジャンプ先 -->
	<div id="top"></div>

	<header>

		<h1>Queued</h1>

	</header>

    <body>

		<h4>host:${MPD_HOST}<br>port:${MPD_PORT}<br></h4>
		<!-- playlistの処理 -->
		<form name="FORM" method="GET" >

				<p>
					<!-- ドロップダウンリスト -->
	             	<select name="button">
						
						<!-- 検索 -->
						<option value="search">search</option>

						<!-- 保存 -->
						<option value="save">save playlist</option>

		            </select>

					<!-- 検索ワードの入力欄 -->
					<span>

						<p><input type="text" placeholder="search word or playlist name" name="input_string"></p>

					</span>

				</p>
		</form>

		<!-- 最下部へのジャンプ -->
		<p><a href="#bottom">jump to bottom</a></p>

		<form name="music" method="POST" >
			
			<!-- ステータスの表示 -->
			<p>$(mpc_post)</p>

		</form>

		<!-- リンク -->
		<button onclick="location.href='/cgi-bin/queued/remove.cgi'">Remove</button>
		<button onclick="location.href='/cgi-bin/directory/directory.cgi'">Directory</button>
		<button onclick="location.href='/cgi-bin/index.cgi'">HOME</button>
		<button onclick="location.href='/cgi-bin/playlist/playlist.cgi'">Playlist</button>

		<form name="music" method="POST" >

			<!-- キュー内の曲を表示 -->
			$(queued_song)

		</form>

	</body>

	<!-- "jump to bottom"のジャンプ先 -->
	<div id="bottom"></div>

	<footer>

		<!-- リンク -->
		<button onclick="location.href='/cgi-bin/queued/remove.cgi'">Remove</button>
		<button onclick="location.href='/cgi-bin/directory/directory.cgi'">Directory</button>
		<button onclick="location.href='/cgi-bin/index.cgi'">HOME</button>
		<button onclick="location.href='/cgi-bin/playlist/playlist.cgi'">Playlist</button>

	</footer>

	<!-- 最上部へのジャンプ -->
	<p><a href="#top">jump to top</a></p>

</html>
EOS
# ====== HTMLここまで ======

