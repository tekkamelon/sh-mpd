#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

echo "Content-type: text/html"
echo ""

cat << EOS
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8" />
		<meta name="viewport" content="width=device-width,initial-scale=1.0">
		<link rel="stylesheet" href="/cgi-bin/stylesheet/stylesheet.css">
		<link rel="icon" ref="image/favicon_ios.ico">
		<link rel="apple-touch-icon" href="image/favicon_ios.ico">
        <title>sh-MPD</title>
    </head>

	<header>
		<h1>Queued</h1>
	</header>

    <body>
		<!-- playlistの処理 -->
		<form name="FORM" method="GET" >
			<p>$(echo ${QUERY_STRING#button\=} | sed "s/\&playlist_name\=/ /g" | xargs mpc)</p>
			<p>debug:$(echo $QUERY_STRING)</p>
			<button name="button" value="save">save playlist</button>
			<button name="button" value="clear">clear</button>
			<button name="button" value="match">match</button>
				<p>
					<!-- playlistの名前の入力欄 -->
					<span style="color: rgb(0, 255, 10); ">
						playlist name:<input type="text" name="playlist_name">
					</span>
				</p>
		</form>
		<form name="music" method="POST" >

				<p>$(# sedでPOSTを加工,デコードしてmpcに渡す
				cat | sed "s/button\=//g" | urldecode | xargs mpc searchplay | sed "s/$/<br>/g" 2>&1
				)</p>

				<!-- リンク -->
				<button><a href="/cgi-bin/directory/directory.cgi">Directory</a></button>
				<button><a href="/cgi-bin/index.cgi">HOME</a></button>
				<button><a href="/cgi-bin/playlist/playlist.cgi">Playlist</a></button>

				<!-- プレイリストの一覧を表示 -->
				$(# クエリ内に"match"がある場合は真,無い場合は偽
				[ $(echo $QUERY_STRING | grep 'match') ] &&

					# 真の場合はクエリを変数展開で加工,デコード
					search_var=$(echo ${QUERY_STRING#button\=*&playlist_name\=} | urldecode) ||

					# 偽の場合は"."で全てにマッチングする行を表示
					search_var="."

				mpc playlist | grep -i ${search_var} |
				# "/"と" - "を区切り文字に指定
				awk -F'/| - ' '{
					print "<p><button name=button value="$1">"$1"</button>",
					"<button name=button value="$NF">"$NF"</button></p>"
				}' |
				# awkで重複行を削除
				awk '!a[$0]++{print}'
				)
		</form>
	</body>

	<footer>	
		<!-- リンク -->
		<button><a href="/cgi-bin/directory/directory.cgi">Directory</a></button>
		<button><a href="/cgi-bin/index.cgi">HOME</a></button>
		<button><a href="/cgi-bin/playlist/playlist.cgi">Playlist</a></button>
	</footer>	

</html>
EOS
