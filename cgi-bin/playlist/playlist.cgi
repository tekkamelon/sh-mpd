#!/bin/sh -euxv

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
		<h1>Playlist</h1>
	</header>

    <body>
		<p>$(mpc queued)</p>
		<!-- mpc nextボタン -->
		<form name="FORM" method="GET" >

			<button name="button" value="next">next</button>
			<!-- クエリを取得,cutで"="以降を切り出し,xargsでmpcに渡す -->	
			$(echo $QUERY_STRING | sed "s/button\=//g" | xargs mpc -q > /dev/null)
		</form>
	
		<!-- mpd.confで設定されたプレイリスト一覧を表示 --> 
		<form name="music" method="POST" >

				<!-- POSTを取得,sedで一部を切り出しデコード,sedで行頭,行末にシングルクォートをつけてmpcに渡す-->
				<p>$(cat | sed "s/button\=//g" | urldecode | 
					mpc load | sed "s/$/<br>/g" 2>&1)</p>

				<button><a href="/cgi-bin/index.cgi">HOME</a></button>
				<button><a href="/cgi-bin/queued/queued.cgi">Queued</a></button>
				<button><a href="/cgi-bin/directory/directory.cgi">Directory</a></button>

				<!-- "music_directory"以下の一覧を表示, sedでスラッシュをawkの区切り文字に置換 -->
				$(mpc lsplaylist |  
					# awkで出力をボタン化
					awk '{ print "<p><button name=button value="$0">"$0"</button>"}' |
					sort | uniq )
		</form>
	</body>

	<footer>
		<button><a href="/cgi-bin/index.cgi">HOME</a></button>
		<button><a href="/cgi-bin/queued/queued.cgi">Queued</a></button>
		<button><a href="/cgi-bin/directory/directory.cgi">Directory</a></button>
	</footer>

</html>
EOS
