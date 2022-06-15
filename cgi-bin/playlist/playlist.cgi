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
		<h1>playlist</h1>
		$(mpc playlist |  sed -e "s;^;<tr>\n<td>;g" -e "s; - ;</td>\n<td>;g" -e "s;$;</td>\n</tr>;g" -e "1i <DOCTYPE html>\n<html>\n<table border="1">" -e '$ a <\/table>\n<\/html>' )
		<button type="button" onclick="history.back()">back</button>
	</body>
</html>
EOS
