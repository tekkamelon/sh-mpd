#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# shellcheck disable=SC1091
# shellcheck disable=SC2154

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

# "foo=bar"の"foo","bar"をそれぞれ抽出
post_left="${cat_post%\=*}"
post_right="${cat_post#"${post_left}"\=}"

# クエリを変数展開し代入
query_check="${QUERY_STRING#*\=}"

# "search"か"save"を抽出
search_or_save="${query_check%%&*}"

# テキストエリアからの入力を抽出,デコード
str_name=$(echo "${query_check#"${search_or_save}"\&input_string\=}" | urldecode)

# POSTがあれば真,無ければ偽
if [ -n "${cat_post}" ] ; then
	
	# POSTがあれば選択された楽曲を再生
	mpc_result=$(mpc "${post_left}" "${post_right}")
	
	# プレイリストの保存後に楽曲が選択された場合
	str_name=""

# 偽の場合は"search_or_save"が"save"であれば真
elif [ "${search_or_save}" = "save" ] ; then

	# 標準エラー出力も変数に代入するために一時的に"set -e"を解除
	set +e
	mpc_result=$(mpc "${search_or_save}" "${str_name}" 2>&1)
	set -e

else

	mpc_result=$(mpc status)

fi

# 再生中の楽曲
mpc_current="$(mpc current)"
# ====== 変数の設定ここまで ======


# ===== 関数の宣言 ======
mpc_status () {

	# プレイリスト名が入力されかつ重複がない場合に真
	if [ -n "${str_name}" ] && [ "${search_or_save}" = "save" ] && [ "${mpc_result%:*}" != "MPD error" ] ; then

		# ステータスとメッセージを出力
		mpc status

		echo "saved playlist:${str_name}"

	else

		echo "${mpc_result}"

	fi |

	# 出力をhtmlに加工
	mpc_status2html -v mpc_current="${mpc_current}" 

}

# キュー内の曲の検索
queued () {

	# プレイリストの保存時には"str_name"に空文字を代入
	test "${search_or_save}" = "save" && str_name=""

	# キューされた曲をgrepで検索,idと区切り文字":"を付与
	mpc playlist | grep -F -i -n "${str_name}" |

	# キュー内の楽曲をHTMLで表示,現在再生中の楽曲は"[Now Playing]"を付与
	# "queued_song"にシェル変数"current",post_nameに"play"を渡す
	queued_song -v mpc_current="${mpc_current}" -v post_name="play"

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
			<p>$(mpc_status)</p>

		</form>

		<!-- リンク -->
		<button onclick="location.href='/cgi-bin/queued/remove.cgi'">Remove</button>
		<button onclick="location.href='/cgi-bin/directory/directory.cgi'">Directory</button>
		<button onclick="location.href='/cgi-bin/index.cgi'">HOME</button>
		<button onclick="location.href='/cgi-bin/playlist/playlist.cgi'">Playlist</button>

		<form name="music" method="POST" >

			<!-- キュー内の曲を表示 -->
			$(queued)

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

