#!/bin/sh -eux

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
			<h1>Directory</h1>
				$(mkfifo mpcpipe)
				<p>$(cat | urldecode | sed "s/button\=//g" >| mpcpipe && cat mpcpipe | mpc insert ; mpc | sed "s/$/<br>/g" 2>&1)</p>
				<button><a href="/cgi-bin/index.cgi">HOME</a></button>
				<!-- "music_directory"以下の一覧を表示, sedでスラッシュをawkの区切り文字に置換 -->
				$(mpc listall | 
					# awkで出力をボタン化
					awk '{ print "<p><button name=button value="$0">"$0"</button>"}' |
					sort | uniq )
				
				<!-- POSTを取得,デコードしてcutで加工後にxargsでmpcに渡す-->
				<button><a href="/cgi-bin/index.cgi">HOME</a></button>
		</form>
	</body>
</html>
EOS
