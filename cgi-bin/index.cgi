#!/bin/sh

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
		<pre> 
         __          __  _______  ____ 
   _____/ /_        /  |/  / __ \\/ __ \\
  / ___/ __ \______/ /|_/ / /_/ / / / /
 (__  ) / / /_____/ /  / / ____/ /_/ / 
/____/_/ /_/     /_/  /_/_/   /_____/  

MPD UI using shellscript and CGI
	    </pre>
		<h3>hostname: $(hostname) cgi_version: $(echo $GATEWAY_INTERFACE)</h3>
		<l2>used RAM: $(free -h | sed -n 2p | awk -F" " '{print $3}')</l2>
		<br></br>

		<form name="FORM" method="GET" >
			<!-- 音楽の操作ボタンをtableでレイアウト -->
			<table>
				<!-- 1行目 -->
				<tr>
					<td>
				 		<button name="button" value="status">status</button>
					</td>
				</tr>	

				<!-- 2行目 -->
				<tr>
					<td>
						<button name="button" value="previous">previous</button>
					</td>
					<td>
				 		<button name="button" value="toggle">play/pause</button>
					</td>
					<td>
				 		<button name="button" value="stop">stop</button>
					</td>
					<td>
				 		<button name="button" value="next">next</button>
					</td>
				</tr>
				 
				<!-- 3行目 -->
				<tr>
					<td>
				 		<button name="button" value="repeat">repeat</button>
					</td>
					<td>
				 		<button name="button" value="random">random</button>
					</td>
					<td>
				 		<button name="button" value="single">single</button>
					</td>
					<td>
				 		<button name="button" value="clear">clear</button>
					</td>
				</tr>
			</table>				 
				
			<p>$(echo $QUERY_STRING | cut -f 2 -d\= | xargs mpc | tr "\n" "," | sed "s/,/<br>/g" > /dev/null)</p>
        </form>

		<form name="sp_and_vol" method="POST" >
			<span style="color: rgb(0, 255, 10); ">
	            select command_and word_or_volume:
			</span>
	            <select name="args">
	
	                <option value="searchplay">searchplay</option>
	
	                <option value="search">search "format" "keywords"</option>

	                <option value="volume">volume</option>
							
					</form>
					<form method="POST">
						<p>
							<span style="color: rgb(0, 255, 10); ">
								<input type="text" name="search">
							</span>
						</p>
						<p>$(cat | awk -F'[=&]' '{print $2,$4}' | tr "\+" " " | xargs mpc -q | tr "\n" "," | sed "s/,/<br>/g")</p>
				    </form>
	            </select>

		<h3>mpd status</h3>
			<p>$(mpc | tr "\n" "," | sed "s/,/<br>/g")

	<details>
		<summary>playlist</summary>
		<p>$(mpc playlist | sed -e "s;^;<summary><h4>;g" -e "s; - ;</h4></summary>\n<p>;g" -e "s;$;</p>;g" | awk  '!a[$0]++')</p>
	</details>

		<h3>next song</h3>
			<p>$(mpc queued)</p>

		<h4>debug info</h4>
			<p>QUERY_STRING: $(echo "$QUERY_STRING")</p>
    </body>
</html>
EOS
