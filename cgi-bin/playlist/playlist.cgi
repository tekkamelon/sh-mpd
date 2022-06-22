#!/bin/sh

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
			<h1>playlist</h1>
				<p>$(cat | urldecode | cut -d"=" -f 2 | sed -e "s/^/\'/g" -e "s/$/\'/g" | xargs mpc searchplay | sed "s/$/<br>/g" 2>&1)</p>

				$(mpc playlist | 
					# awkで出力をボタン化,grepでデータ無しの行を削除
					awk -F" - " '{
						print "<p><button name=button value="$1">"$1"</button>",
						"<button name=button value="$2">"$2"</button></p>"
					}' |  
					grep -v 'value=></button>' | sort | uniq)
				
				<!-- POSTを取得,デコードしてcutで加工後にxargsでmpcに渡す-->
				<p><a href="/cgi-bin/index.cgi">HOME</a></p>
		</form>
	</body>
</html>
EOS
