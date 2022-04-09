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

		<!-- 引数を必要としない操作 --!>
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
	
	                <option value="clear">clear</option>
	            </select>
	             <input type="submit" value="Enter" />
			<p>$(echo $QUERY_STRING | cut -f 2 -d\= | xargs mpc | tr "\n" "," | sed "s/,/<br>/g" > /dev/null)</p>
        </form>

		<!-- <form action="#" method="post">
				<p>
					<span style="color: rgb(0, 255, 10); ">
						searchplay:<input type="text" name="name">
					</span>
				</p>
			</span>
        </form> --!>
		
		<! -- 引数を必要とする操作 --!>
		<form name="FORM" method="GET" >
		<span style="color: rgb(0, 255, 10); ">
            select command:
		</span>
            <select name="args">
                <!-- <option value="search">search</option> --!>

                <option value="searchplay">searchplay</option>

                <option value="volume">volume</option>
				
			<form action="$" method="post">
					<p>
						<span style="color: rgb(0, 255, 10); ">
							<input type="text" name="name">
						</span>
					</p>
				</span>
	        </form>
            </select>
			 $(echo $QUERY_STRING | awk -F'[=&]' '{print $2,$4}' | xargs mpc | tr "\n" "," | sed "s/,/<br>/g" > /dev/null)
			 
        </form>

		<form action="#" method="post">

	<details>
		<summary>playlist</summary>
		<p>$(mpc playlist | cut -f 2 -d\= | tr "\n" "," | sed "s/,/<br>/g")</p>
	</details>

		<h3>mpd status</h3>
			<p>$(mpc | tr "\n" "," | sed "s/,/<br>/g")

		<h3>next song</h3>
			<p>$(mpc queued)</p>

		<h4>debug info</h4>
			<p>POST_STRING: $(cat | cut -f 2 -d\= | xargs -I{} mpc searchplay {})</p>
			<p>QUERY_STRING: $(echo "$QUERY_STRING")</p>
			<p>QUERY_STRING_cut: $(echo "$QUERY_STRING" | cut -f 2 -d\=)</p>
    </body>
</html>
EOS
