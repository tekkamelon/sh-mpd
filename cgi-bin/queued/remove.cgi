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

# クエリを変数展開で加工,デコード,変数に代入
search_str="$(echo "${QUERY_STRING#*\=}" | urldecode)"

# 再生中の楽曲
mpc_current="$(mpc current)"
# ====== 変数の設定ここまで ======


# ===== 関数の宣言 ======
mpc_post () {

	# 複数の項目の削除に対応
	# POSTの"="を" "に置換,"&del"を削除
	echo "${cat_post}" | sed -e "s/=/ /g" -e "s/\&del//g" |

	xargs mpc 2>&1 |

	mpc_status2html -v mpc_current="${mpc_current}" 

	# 曲の削除の結果の表示,"cat_post"があれば真
	if [ -n "${cat_post}" ] ; then

		# 真の場合,ステータスとメッセージを表示
		mpc status 2>&1 | mpc_status2html && echo "<p>Remove selected song!</p>"

	fi

}

# キュー内の曲の検索,チェックボックス付きで表示
queued () {

	# 再生中の楽曲
	mpc_current="$(mpc current)"

	# キューされた曲をgrepで検索,idと区切り文字":"を付与
	mpc playlist | grep -F -i -n "${search_str}" |

	# キュー内の楽曲をHTMLで表示,現在再生中の楽曲は"[Now Playing]"を付与
	# "queued_song"にシェル変数"current",post_nameに"del"を渡す
	queued_song -v mpc_current="${mpc_current}" -v post_name="del" 

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

		<h1>Remove queued song</h1>

	</header>

    <body>

		<h4>host:${MPD_HOST}<br>port:${MPD_PORT}<br></h4>

		<!-- playlistの処理 -->
		<form name="FORM" method="GET" >

			</select>

			<!-- 検索ワードの入力欄 -->
			<span>

				<p><input type="text" placeholder="search word" name="input_string"></p>

			</span>

		</form>

		<!-- 最下部へのジャンプ -->
		<p><a href="#bottom">jump to bottom</a></p>

		<form name="music" method="POST" >
			
			<!-- ステータスの表示 -->
			<p>$(mpc_post)</p>

		</form>

		<!-- リンク -->
		<button onclick="location.href='/cgi-bin/queued/queued.cgi'">Queued</button>
		<button onclick="location.href='/cgi-bin/directory/directory.cgi'">Directory</button>
		<button onclick="location.href='/cgi-bin/index.cgi'">HOME</button>
		<button onclick="location.href='/cgi-bin/playlist/playlist.cgi'">Playlist</button>

		<form name="music" method="POST" >

			<!-- 削除ボタン -->
			<p><input type="submit" value="Remove select song"></p>

			<!-- キュー内の曲を表示 -->
			$(queued)

			<!-- 削除ボタン -->
			<p><input type="submit" value="Remove select song"></p>

		</form>

	</body>

	<!-- "jump to bottom"のジャンプ先 -->
	<div id="bottom"></div>

	<footer>

		<!-- リンク -->
		<button onclick="location.href='/cgi-bin/queued/queued.cgi'">Queued</button>
		<button onclick="location.href='/cgi-bin/directory/directory.cgi'">Directory</button>
		<button onclick="location.href='/cgi-bin/index.cgi'">HOME</button>
		<button onclick="location.href='/cgi-bin/playlist/playlist.cgi'">Playlist</button>

	</footer>

	<!-- 最上部へのジャンプ -->
	<p><a href="#top">jump to top</a></p>

</html>
EOS
# ====== HTMLここまで ======

