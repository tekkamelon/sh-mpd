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
export PATH="$PATH:../../../bin"

# ". (ドット)"コマンドで設定ファイルの読み込み
. ../shmpd.conf

# POSTを変数に代入
cat_post=$(cat)

# "foo=bar"の"foo","bar"をそれぞれ抽出
post_left="${cat_post%\=*}"
post_right="${cat_post#"${post_left}"\=}"
# ====== 変数の設定ここまで ======


# ===== 関数の宣言 ======
# POSTを加工しmpcに渡す
mpc_post () {

	# POSTの有無を確認,あれば真,無ければ偽
	if [ -n "${cat_post}" ] ; then

		echo "${post_left}" "${post_right}" 
		
	else

		# 偽の場合は"outputs"を出力
		echo "outputs"

	fi | 

	# 出力をmpcに渡す
	xargs mpc |

	# スペースを区切り文字に設定,1フィールド目が"Output"の行をボタン化
	awk -F" " '$1 == "Output"{

		print "<p><button name=toggleoutput value="$2">"$0"</button></p>"

	}'

}

# ステータスを表示
mpc_status () {
			
	# mpcのエラー出力ごとパイプに流す
	mpc status 2>&1 |

	# ": off"に<b>タグを,": on"に<strong>タグを,各行末に改行のタグを付与
	mpc_status2html

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

	<header>

		<h1>settings</h1>

	</header>

    <body>

		<form name="setting" method="POST" >
			
			<h4>host:${MPD_HOST}<br>port:${MPD_PORT}<br></h4>

			<!-- 出力先デバイスの設定 -->
			<h3>ountput devices list</h3>
			$(mpc_post)

			<!-- ステータスの表示 -->
			<p>$(mpc_status)</p>

		</form>

    </body>

	<footer>	

		<!-- リンク -->
		<button class="equal_width_button" onclick="location.href='/cgi-bin/queued/queued.cgi'">Queued</button>
		<button class="equal_width_button" onclick="location.href='/cgi-bin/directory/directory.cgi'">Directoty</button>
		<button class="equal_width_button" onclick="location.href='/cgi-bin/index.cgi'">HOME</button>
		<button class="equal_width_button" onclick="location.href='/cgi-bin/playlist/playlist.cgi'">Playlist</button>
		<button class="equal_width_button" onclick="location.href='/cgi-bin/settings/settings.cgi'">Settings</button>

	</footer>	

</html>
EOS
# ====== HTML ======

