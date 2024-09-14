#!/bin/sh

# shellcheck disable=SC1091,SC2154

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示
set -eu

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

# クエリを変数展開で加工,デコード,変数に代入
search_str="$(echo "${QUERY_STRING#*\=}" | urldecode)"

# URLのホスト名を取得
url_hostname=$(cgi_host)
# ====== 変数の設定ここまで ======


# ===== 関数の宣言 ======
# POSTを加工しmpcに渡す
mpc_post () {

	# 複数の項目の削除に対応
	# POSTの"="をスペースに,"&rm"を"\nrm"に置換,デコード
	echo "${cat_post}" | sed -e "s/=/ /g" -e "s/\&rm/\nrm/g"| urldecode |

	xargs -l mpc 2>&1 | 

	mpc_status2html -v url_hostname="${url_hostname}"

	# プレイリストの削除の結果を表示,"cat_post"があれば真
	if [ -n "${cat_post}" ] ; then

		# 真の場合,ステータスとメッセージを表示
		mpc status 2>&1 | mpc_status2html && echo "<p>Remove selected playlist!</p>"

	fi

}

# プレイリスト一覧を検索,チェックボックス付きで表示
list_playlist () {

	mpc lsplaylist |

	# 固定文字列を大文字,小文字を区別せずに検索
	grep -F -i "${search_str}" |

	awk '{

		print "<p><input type=checkbox name=rm value=", $0, ">", $0, "</p>"

	}'

}
# ====== 関数の宣言ここまで ======


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
		<title>Remove playlist - sh-MPD:$(cgi_host) -</title>

    </head>
	
	<!-- "jump to top"のジャンプ先 -->
	<div id="top"></div>

	<header>
	
		<h1>Remove playlist</h1>
		
	</header>

    <body>

		<h4>${MPD_HOST}<br>port:${MPD_PORT}<br></h4>

		<!-- 入力欄の設定 -->
		<form name="FORM" method="GET" >

			<!-- 検索ワードの入力欄 -->
			<p><input type="text" placeholder="search word" name="search_word"></p>

		</form>
	
		<!-- 最下部へのジャンプ -->
		<p><a href="#bottom">jump to bottom</a></p>

		<!-- mpd.confで設定されたプレイリスト一覧を表示 -->
		<form name="music" method="POST" >

			<!-- ステータスを表示 -->
			<p>$(mpc_post)</p>

		</form>

		<!-- リンク -->
		<button class="equal_width_button" onclick="location.href='/cgi-bin/playlist/playlist.cgi'">Playlist</button>
		<button class="equal_width_button" onclick="location.href='/cgi-bin/queued/queued.cgi'">Queued</button>
		<button class="equal_width_button" onclick="location.href='/cgi-bin/index.cgi'">HOME</button>
		<button class="equal_width_button" onclick="location.href='/cgi-bin/directory/directory.cgi'">Directory</button>
		<button class="equal_width_button" onclick="location.href='/cgi-bin/settings/settings.cgi'">Setting</button>

		<form name="music" method="POST" >

			<!-- 削除ボタン -->
			<p><input type="submit" value="Remove select playlist"></p>

			<!-- mpc管理下のプレイリスト,ディレクトリを表示 -->
			$(list_playlist)

			<!-- 削除ボタン -->
			<p><input type="submit" value="Remove select playlist"></p>

		</form>

	</body>

	<!-- "jump to bottom"のジャンプ先 -->
	<div id="bottom"></div>

	<footer>
	
		<!-- リンク -->
		<button class="equal_width_button" onclick="location.href='/cgi-bin/playlist/playlist.cgi'">Playlist</button>
		<button class="equal_width_button" onclick="location.href='/cgi-bin/queued/queued.cgi'">Queued</button>
		<button class="equal_width_button" onclick="location.href='/cgi-bin/index.cgi'">HOME</button>
		<button class="equal_width_button" onclick="location.href='/cgi-bin/directory/directory.cgi'">Directory</button>
		<button class="equal_width_button" onclick="location.href='/cgi-bin/settings/settings.cgi'">Setting</button>
		
	</footer>

	<!-- 最上部へのジャンプ -->
	<p><a href="#top">jump to top</a></p>

</html>
EOS
# ====== HTMLここまで ======

