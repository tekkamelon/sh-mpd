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

    <body>
		<form name="music" method="POST" >

			<h1>Playlist</h1>
				<p>$(cat | urldecode | cut -d"=" -f 2 | sed -e "s/^/\'/g" -e "s/$/\'/g" | xargs mpc searchplay | sed "s/$/<br>/g" 2>&1)</p>
				<button><a href="/cgi-bin/index.cgi">HOME</a></button>
				<!-- プレイリストの一覧を表示, sedでスラッシュをawkの区切り文字に置換 -->
				$(mpc playlist | sed "s;/; - ;g" |  
					# awkで出力をボタン化,grepでデータ無しの行を削除
					awk -F" - " '{
						print "<p><button name=button value="$1">"$1"</button>",
						"<button name=button value="$2">"$2"</button></p>"
					}' |
					# sort uniq後,空白のボタンを削除
					sort | uniq | sed "s;<button name=button value=></button></p>;;g" )
				
				<!-- POSTを取得,デコードしてcutで加工後にxargsでmpcに渡す-->
				<button><a href="/cgi-bin/index.cgi">HOME</a></button>
		</form>
	</body>
</html>
EOS
