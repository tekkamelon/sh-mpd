#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# 環境変数で接続先ホスト,ポート番号を設定,データがない場合は"localhost","6600"
export MPD_HOST=$(cat ../settings/hostname | grep . || echo "localhost") 
export MPD_PORT=$(cat ../settings/port_conf | grep . || echo "6600") 

# 変数展開でクエリを加工,デコードし,文字列の有無を判定
# export SEARCH_VAR=$(echo "${QUERY_STRING#*\=}" | urldecode | grep . || echo ".")

echo "Content-type: text/html"
echo ""

cat << EOS
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8" />
		<meta name="viewport" content="width=device-width,initial-scale=1.0">
		<link rel="stylesheet" href="/cgi-bin/stylesheet/$(cat ../settings/css_conf | grep . || echo "stylesheet.css")">
		<link rel="icon" ref="image/favicon_ios.ico">
		<link rel="apple-touch-icon" href="image/favicon_ios.ico">
        <title>sh-MPD</title>
    </head>
	
	<header>
		<h1>Playlist</h1>
	</header>

    <body>
		<h4>$(echo "host:$MPD_HOST<br>port:$MPD_PORT<br>")</h4>

		<!-- 入力欄の設定 -->
		<form name="FORM" method="GET" >

			<!-- 検索ワードの入力欄 -->
			<p>search_word:<input type="text" name="search_word"></p>

			
		</form>
	
		<!-- mpd.confで設定されたプレイリスト一覧を表示 --> 
		<form name="music" method="POST" >

				<!-- ステータスを表示 -->
				<p>$(# POSTをデコード,cutで加工しmpcに渡す
				cat | urldecode | cut -d"=" -f2- |

				mpc load | sed "s/$/<br>/g" 2>&1
				
				)</p>

				<!-- リンク -->
				<button><a href="/cgi-bin/queued/queued.cgi">Queued</a></button>
				<button><a href="/cgi-bin/index.cgi">HOME</a></button>
				<button><a href="/cgi-bin/directory/directory.cgi">Directory</a></button>

				<!-- mpc管理下のプレイリストを表示 -->
				$(# 変数展開でクエリを加工,デコードし,文字列の有無を判定
				search_var=$(echo "${QUERY_STRING#*\=}" | urldecode | grep . || echo ".")

				# プレイリストをgrepで検索
				mpc lsplaylist | grep -i "${search_var}" | 

				# ボタン化
				awk '{
						
					print "<p><button name=button value="$0">"$0"</button></p>"

				}'
				)
		</form>
	</body>

	<footer>
		<!-- リンク -->
		<button><a href="/cgi-bin/queued/queued.cgi">Queued</a></button>
		<button><a href="/cgi-bin/index.cgi">HOME</a></button>
		<button><a href="/cgi-bin/directory/directory.cgi">Directory</a></button>
	</footer>

</html>
EOS
