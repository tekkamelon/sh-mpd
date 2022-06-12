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
		<p>$(mpc playlist | sed -e "s;^;<summary><h4>;g" -e "s; - ;</h4></summary>\n<p>;g" -e "s;$;</p>;g" | awk  '!a[$0]++')</p>
	</body>
</html>
EOS
