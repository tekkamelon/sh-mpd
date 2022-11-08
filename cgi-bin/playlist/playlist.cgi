#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# 環境変数で接続先ホスト,ポート番号を設定,データがない場合は"localhost","6600"
export MPD_HOST=$(cat ../settings/hostname | grep . || echo "localhost") 
export MPD_PORT=$(cat ../settings/port_conf | grep . || echo "6600") 

echo "Content-type: text/html"
echo ""

cat << EOS
<!DOCTYPE html>
<html>
    <head>
        <meta charset="UTF-8" />
		<meta name="viewport" content="width=device-width,initial-scale=1.0">
		<link rel="stylesheet" href="/cgi-bin/stylesheet/$(cat ../settings/css_conf | grep . || echo "stylesheet.css" &)">
		<link rel="icon" ref="image/favicon_ios.ico">
		<link rel="apple-touch-icon" href="image/favicon_ios.ico">
        <title>sh-MPD</title>
    </head>
	
	<header>
		<h1>Playlist</h1>
	</header>

    <body>
		<h4>$(echo "host:$MPD_HOST<br>port:$MPD_PORT<br>" &)</h4>

		<!-- 入力欄の設定 -->
		<form name="FORM" method="GET" >

			<!-- 検索ワードの入力欄 -->
			<p>search_word:<input type="text" name="search_word"></p>

		</form>
	
		<!-- mpd.confで設定されたプレイリスト一覧を表示 --> 
		<form name="music" method="POST" >

				<!-- ステータスを表示 -->
				<p>$(# POSTをデコード,awkに渡す
				cat | urldecode | 

				# 区切り文字を"="に指定,POSTの1フィールド目が"lsplaylist"の場合
				awk -F"=" '$1=="lsplaylist"{

					# "load "と2フィールド目を出力
					print "load "$NF

				}

				# POSTの1フィールド目が"dir"の場合
				$1=="dir"{

					# "add "と2フィールド目を出力
					print "add "$NF

				}' | 

				# 出力をmpcに渡し,エラー出力ごと表示
				xargs mpc | sed "s/$/<br>/g" 2>&1
				
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

				awk '{
						
					# 1フィールド目に"lsplaylist"を指定
					print "<p><button name=lsplaylist value="$0">"$0"</button></p>"

				}' 
				
				# "listall"で全ファイルを取得,cutとawkで親ディレクトリのみを出力
				mpc listall | cut -d"/" -f1 | awk '!a[$0]++{print $0}' | grep -i "${search_var}" | 
				awk '{

					# 1フィールド目に"dir"を指定
					print "<p><button name=dir value="$0">"$0"</button></p>"

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
