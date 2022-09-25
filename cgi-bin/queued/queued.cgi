#!/bin/sh -eux

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# 環境変数で接続先ホストを設定,ファイルがない場合はローカルホスト
export MPD_HOST=$(# hostnameを変数に代入
	hostname_var=$(cat ../settings/hostname)
	# 変数展開で加工,文字列がない場合は"localhost"を環境変数に代入
	echo ${hostname_var#export\&MPD_HOST\=} | grep . || echo "localhost"
	) 

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
		<h1>Queued</h1>
	</header>

    <body>
		<h4>hostname: $(echo $MPD_HOST)</h4>
		<!-- playlistの処理 -->
		<form name="FORM" method="GET" >
			
			<p>$(# playlistのセーブ

			echo ${QUERY_STRING#*\=} | sed "s/\&input_string\=/ /g" | urldecode | xargs mpc > /dev/null
			)</p>

			<!-- クエリの表示 -->
			<p>debug:$(echo $QUERY_STRING)</p>
				<p>
					<!-- ドロップダウンリスト -->
	             	<select name="button">
						
						<!-- 検索 -->
						<option value="match">match</option>

						<!-- 保存 -->
						<option value="save">save playlist</option>
		            </select>

					<!-- playlistの名前,検索ワードの入力欄 -->
					<span style="color: rgb(0, 255, 10); ">
						<input type="text" name="input_string">
					</span>
				</p>
		</form>

		<form name="music" method="POST" >
			
			<p>$(# 曲の再生部分

			# POSTで受け取った文字列を変数に代入
			cat_post=$(cat)

			# POSTに"http"が含まれていれば真,なければ偽
			if echo "${cat_post#*\=}" | urldecode | grep -q "http" ; then

				# 真の場合,POSTを変数展開で加工,デコードして"mpc insert"に渡して再生
				echo ${cat_post#*\=} | urldecode | mpc insert && mpc next -q | sed "s/$/<br>/g" 
			
			else

				# 偽の場合,POSTを変数展開で加工,デコードしてmpcに渡す
				echo ${cat_post#*\=} | urldecode | xargs mpc searchplay | sed "s/$/<br>/g" 2>&1 

			fi
			)</p>

			<!-- リンク -->
			<button><a href="/cgi-bin/directory/directory.cgi">Directory</a></button>
			<button><a href="/cgi-bin/index.cgi">HOME</a></button>
			<button><a href="/cgi-bin/playlist/playlist.cgi">Playlist</a></button>

			<!-- プレイリストの一覧を表示 -->
			$(# クエリ内に"match"があるかどうかを判断

			# クエリを変数展開で加工,デコードしgrepの終了ステータスで文字列があるかどうかを判断
			search_var=$(echo ${QUERY_STRING#*\=match&input_string\=} | urldecode | grep .) ||

			# 偽の場合は"."で全てにマッチングする行を表示
			search_var="."

			# キューされた曲の表示
			mpc playlist | grep -i ${search_var} |

			# "/"と" - "を区切り文字に指定,"http"にマッチしない文字列をボタン化
			awk -F'/| - ' '!/http/{
				# １番目のフィールドをボタン化
				print "<p><button name=button value="$1">"$1"</button>",
				# 最終フィールドをボタン化
				"<button name=button value="$NF">"$NF"</button></p>"
			}

			# "http"にマッチする文字列をボタン化
			/http/{
				print "<p><button name=button value="$0">"$0"</button></p>"
			}' |

			# 重複行を削除
			awk '!a[$0]++{
				print $0
			}'
			)

		</form>
	</body>

	<footer>	
		<!-- リンク -->
		<button><a href="/cgi-bin/directory/directory.cgi">Directory</a></button>
		<button><a href="/cgi-bin/index.cgi">HOME</a></button>
		<button><a href="/cgi-bin/playlist/playlist.cgi">Playlist</a></button>
	</footer>	

</html>
EOS

