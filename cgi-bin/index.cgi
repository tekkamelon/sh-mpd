#!/bin/sh -x

echo "Content-type: text/html"
echo ""

cat << EOS
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8" />
		<meta name="viewport" content="width=device-width,initial-scale=1.0">
		<link rel="stylesheet" href="stylesheet/stylesheet.css">
		<link rel="icon" ref="image/favicon_ios.ico">
		<link rel="apple-touch-icon" href="image/favicon_ios.ico">
        <title>sh-MPD</title>
    </head>

    <body>
		<h1>sh-MPD</h1>
		<h3>hostname:$(hostname) cgi_version:$(echo $GATEWAY_INTERFACE)</h3>
		<l2>used RAM:$(free -h | tr "\n" "," | sed "s/,/<br>/g" & echo '<br>')</l2>
		<br></br>
		<form name="FORM" method="GET" >
		<span style="color: rgb(0, 255, 10); ">
            select command:
		</span>
            <select name="cmd">
                <option value="status">status</option>
				
                <option value="toggle">play/pause</option>
				
                <option value="stop">stop</option>
				
                <option value="previous">prev</option>
				
                <option value="next">next</option>
				
                <option value="repeat">repeat</option>
				
                <option value="random">random</option>
				
                <option value="shuffle">shuffle</option>

                <option value="single">single</option>

                <option value="playlist">playlist</option>
				
                <option value="clear">clear</option>
            </select>
             <input type="submit" value="Enter" />
        </form>
		<form action="#" method="post">
				<p>
					<span style="color: rgb(0, 255, 10); ">
						searchplay:<input type="text" name="name">
					</span>
				</p>
			</span>
        </form>

        <pre>
<!--RESULT-->
        </pre>
		<h3>mpd status</h3>
			<p>$(echo $QUERY_STRING | cut -f 2 -d\= | xargs mpc | tr "\n" "," | sed "s/,/<br>/g")</p>

		<h3>next song</h3>
			<p>$(mpc queued)</p>

			<p>POST_STRING=$(cat | cut -f 2 -d\= | xargs -I{} mpc searchplay {})</p>
			<p>debug info:$(echo "$QUERY_STRING")</p>
			<p>debug info:$(echo "$QUERY_STRING" | cut -f 2 -d\=)</p>
    </body>
</html>
EOS
