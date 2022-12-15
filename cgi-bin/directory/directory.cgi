#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# 環境変数で接続先ホスト,ポート番号を設定,データがない場合は"localhost","6600"
export MPD_HOST=$(cat ../settings/hostname | grep . || echo "localhost") 
export MPD_PORT=$(cat ../settings/port_conf | grep . || echo "6600") 
export LANG=C

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
		<h1>Directory</h1>
	</header>

    <body>
		<h4>$(echo "host:$MPD_HOST<br>port:$MPD_PORT<br>" &)</h4>
		<form name="FORM" method="GET" >

					<!-- 検索ワードの入力欄 -->
					<p>search_word:<input type="text" name="search_word"></p>
				
		</form>
	
		<!-- ステータスを表示 --> 
		<form name="music" method="POST" >

				<p>$(# POSTで受け取った文字列を変数に代入

				cat_post=$(cat)

				# POSTを変数展開で加工,空でない場合に真,空の場合に偽
				if [ -n "${cat_post#*\=}" ] ; then

					# 真の場合,POSTを変数展開で加工,デコードしてmpcに渡しキューに追加,再生
					echo "${cat_post#*\=}" | urldecode | mpc insert && mpc next

				else

					# ステータスを表示
					mpc status

				fi | sed "s/$/<br>/g"

				)</p>

				<!-- リンク -->
				<button><a href="/cgi-bin/queued/queued.cgi">Queued</a></button>
				<button><a href="/cgi-bin/index.cgi">HOME</a></button>
				<button><a href="/cgi-bin/playlist/playlist.cgi">Playlist</a></button>

				<!-- mpc管理下のディレクトリを再帰的に表示 -->
				$(# クエリを変数展開で加工,デコード,文字列があれば変数に代入,なければ"."を代入

				search_var=$(echo "${QUERY_STRING#*\=}" |

					# awkで文字列の有無を判定,あれば真,なければ偽
					awk '{
	
						if(/./){
	
							# 真の場合は加工されたクエリを出力
							print $0
	
						}

						else{
	
							# 偽の場合は"."を出力
							print "."
	
						}
	
					# 文字列をデコード
					}' | urldecode 
	
					)
					
				# 曲の一覧をgrepで検索
				mpc listall | grep -i "${search_var}" |

				# 出力をボタン化
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
		<button><a href="/cgi-bin/playlist/playlist.cgi">Playlist</a></button>
	</footer>

</html>
EOS

