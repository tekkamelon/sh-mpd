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
export PATH="$PATH:../../bin"

# ". (ドット)"コマンドで設定ファイルの読み込み
. ../settings/shmpd.conf

# POSTを変数に代入
cat_post=$(cat)

query_check="${QUERY_STRING#*\=}"

# "search"か"save"を抽出
search_or_save="${query_check%%&*}"

# テキストエリアからの入力を抽出,デコード
str_name=$(echo "${query_check#*\&input_string\=}" | urldecode)

# POSTがあれば真,無ければ偽
if [ -n "${cat_post}" ] ; then
	
	# POSTがあれば選択された楽曲を再生
	mpc_result=$(mpc "${cat_post%%\=*}" "${cat_post#*\=}")
	
	str_name=""

# 偽の場合は"search_or_save"が"save"であれば真
elif [ "${search_or_save}" = "save" ] ; then

	# このcatがないと正常に動作しない
	mpc_result=$(mpc "${search_or_save}" "${str_name}" 2>&1 | cat -)

else

	mpc_result=$(mpc status)

fi
# ====== 変数の設定ここまで ======


# ===== 関数の宣言 ======
# POSTを加工しmpcに渡す
mpc_post () {

	# 同名のプレイリストが既に存在した場合に真
	if [ "${mpc_result}" = "MPD error: Playlist already exists" ] ; then

		echo "${mpc_result}"

	# 偽の場合は同名のプレイリストがなければ保存成功と判定
	elif [ -n "${str_name}" ] && [ "${search_or_save}" = "save" ] ; then

		# ステータスとメッセージを出力
		# プレイリストの保存時にはステータスを返さないため
		mpc status

		echo "saved playlist:${str_name}"

	else

		echo "${mpc_result}"

	fi |

	mpc_status2html

}

# キュー内の曲の検索
queued_song () {

	# "search_or_save"が"save"で真,それ以外で偽
	if [ "${search_or_save}" = "save" ] ; then

		# 真の場合は"search_str"に空文字を代入
		search_str=""

	else

		search_str="${str_name}"

	fi

	# キューされた曲をgrepで検索,idと区切り文字":"を付与
	mpc playlist | grep -F -i -n "${search_str}" |

	# ":"を">"に置換,標準入力をタグ付きで出力
	awk '{

		sub(":" , ">")

		print "<p><button name=play value="$0"</button></p>"

	}'

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
		<link rel="icon" ref="/cgi-bin/image/favicon.ico">
		<link rel="apple-touch-icon" href="/cgi-bin/image/favicon.ico">
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

