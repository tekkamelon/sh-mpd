#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# 環境変数の設定
export LANG=C

# ホスト名,ポート番号を設定,データがない場合は"localhost","6600"
host="$(cat ../settings/hostname)"
port="$(cat ../settings/port_conf)"
export MPD_HOST="${host}"
export MPD_PORT="${port}"

# "urldecode"にパスを通す
export PATH="$PATH:../../bin"

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
			<p>$(# POSTの処理,POSTが無い場合はステータスの表示

			# POSTの"="をスペースに,"&rm"を"\nrm"に置換,デコードしmpcに渡す
			cat | sed -e "s/=/ /g" -e "s/\&rm/\nrm/g"| urldecode | xargs -l mpc 2>&1 | 

			# 3行目の": off"に<b>タグを,": on"に<strong>タグを,各行末に改行のタグを付与
			sed -e "3 s/: off/:<b> off<\/b>/g" -e "3 s/: on/:<strong> on<\/strong>/g" -e "s/$/<br>/g"
			
			)</p>

		</form>

		<!-- リンク -->
		<button onclick="location.href='/cgi-bin/playlist/playlist.cgi'">Playlist</button>
		<button onclick="location.href='/cgi-bin/queued/queued.cgi'">Queued</button>
		<button onclick="location.href='/cgi-bin/index.cgi'">HOME</button>
		<button onclick="location.href='/cgi-bin/directory/directory.cgi'">Directory</button>

		<form name="music" method="POST" >

			<!-- 削除ボタン -->
			<p><input type="submit" value="Remove select playlist"></p>

			<!-- mpc管理下のプレイリスト,ディレクトリを表示 -->
			$(# プレイリスト及びディレクトリの検索などの処理

			# クエリを変数展開で加工,デコード,変数に代入
			search_str="$(echo "${QUERY_STRING#*\=}" | urldecode)"
			
			# プレイリスト一覧を出力
			mpc lsplaylist |

			# 固定文字列を大文字,小文字を区別せずに検索
			grep -F -i "${search_str}" |

			# タグを付与し出力,ボタン化
			awk '{

				print "<p><input type=checkbox name=rm value="$0">"$0"</p>"

			}'

			)

			<!-- 削除ボタン -->
			<p><input type="submit" value="Remove select playlist"></p>

		</form>

	</body>

	<!-- "jump to bottom"のジャンプ先 -->
	<div id="bottom"></div>

	<footer>
	
		<!-- リンク -->
		<button onclick="location.href='/cgi-bin/playlist/playlist.cgi'">Playlist</button>
		<button onclick="location.href='/cgi-bin/queued/queued.cgi'">Queued</button>
		<button onclick="location.href='/cgi-bin/index.cgi'">HOME</button>
		<button onclick="location.href='/cgi-bin/directory/directory.cgi'">Directory</button>
		
	</footer>

	<!-- 最上部へのジャンプ -->
	<p><a href="#top">jump to top</a></p>

</html>
EOS

