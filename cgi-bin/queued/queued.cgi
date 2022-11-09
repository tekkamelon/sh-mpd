#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# 環境変数の設定
# 接続先ホスト,ポート番号を設定,データがない場合は"localhost","6600"
export MPD_HOST=$(cat ../settings/hostname | grep . || echo "localhost") 
export MPD_PORT=$(cat ../settings/port_conf | grep . || echo "6600") 

# "SAVE_PLAYLIST","SEARCH_VAR"を設定
export $(# クエリ内の文字列をawkで判定し,処理を分け環境変数へ代入

	# クエリを変数展開で加工,デコード
	echo "${QUERY_STRING#*\=}" | urldecode | 

	# プレイリストのセーブの処理,"save&input_string=(任意の1文字以上)"にマッチした場合の処理
	awk -F'[=&]' '/save&input_string=./{

		print "SAVE_PLAYLIST="$1"_"$NF
		print "SEARCH_VAR=."

	}

	# 検索の処理,"search&input_string=(任意の1文字以上)"にマッチした場合の処理
	/search&input_string=./{

		print "SAVE_PLAYLIST=-q"
		print "SEARCH_VAR="$NF

	}
	
	# "&input_string=(任意の1文字以上)"にマッチしなかった場合の処理
	!/&input_string=./{

		print "SAVE_PLAYLIST=-q"
		print "SEARCH_VAR=."

	}' |
	
	# 並列化し環境変数へ代入
	xargs -L 1 -P 2
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
		<h4>$(echo "host:$MPD_HOST<br>port:$MPD_PORT<br>" &)</h4>
		<!-- playlistの処理 -->
		<form name="FORM" method="GET" >

			<!-- クエリの表示 -->
			<p>debug:$(echo "${QUERY_STRING}")</p>
				<p>
					<!-- ドロップダウンリスト -->
	             	<select name="button">
						
						<!-- 検索 -->
						<option value="search">search</option>

						<!-- 保存 -->
						<option value="save">save playlist</option>
		            </select>

					<!-- playlistの名前,検索ワードの入力欄 -->
					<span>
						<input type="text" name="input_string">
					</span>
				</p>
		</form>

		<form name="music" method="POST" >
			
			<p>$(# 曲の再生部分

			# POSTで受け取った文字列をデコード,変数に代入
			cat_post=$(cat | urldecode)
			
			# POSTにIDが含まれていれば真,なければ偽
			if echo "${cat_post#*\=}" | grep -q ^[0-9] ; then

				# 真の場合,POSTを変数展開で加工しmpcに渡す
				echo "${cat_post#*\=}" | xargs mpc play 

			# 偽の場合は文字列があれば真
			# elif echo "${cat_post#*\=}" | grep -q . ; then
			elif [ "${cat_post#*\=}" ]; then

				#真の場合,次の曲に追加し再生
				echo "${cat_post#*\=}" | mpc insert && mpc next

			fi | sed "s/$/<br>/g" 2>&1

			)</p>

			<!-- リンク -->
			<button><a href="/cgi-bin/directory/directory.cgi">Directory</a></button>
			<button><a href="/cgi-bin/index.cgi">HOME</a></button>
			<button><a href="/cgi-bin/playlist/playlist.cgi">Playlist</a></button>

			<!-- キュー内の曲を表示 -->
			$(# キュー内の曲をプレイリストに保存
			mpc $(echo "${SAVE_PLAYLIST}" | sed "s/_/ /" &)

			# ------ コマンドのグルーピング ------

			# キューされた曲を出力
			{ mpc playlist | 

			# nlでIDを付与し区切り文字を" seperate "に指定,空白行を削除
			nl -n rz -s " ---seperate--- " | grep -v '^\s*$' ;

			# URLを抽出	
			mpc playlist | grep -e "^http://" -e "^https://" ; } | 

			# ------ グルーピングの終了 ------

			grep -i "${SEARCH_VAR}" | 

 			awk '{
 				
				# 区切り文字を" ---seperate--- "に指定
				FS = " ---seperate--- "

 				# POSTでIDのみを渡せるようボタン化
 				print "<p><button name=button value="$1">"$NF"</button></p>"

			 }
 
 			# URLのみボタン化
    		/^http:/ || /^https:/{
    
    			print "<p><button name=button value="$0">"$0"</button></p>"
   
   			}' | 

			# 重複行を削除
			awk '!a[$0]++{print $0}'
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

