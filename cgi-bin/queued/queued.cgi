#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# 環境変数の設定
# 接続先ホスト,ポート番号を設定,データがない場合は"localhost","6600"
export MPD_HOST=$(cat ../settings/hostname | grep . || echo "localhost") 
export MPD_PORT=$(cat ../settings/port_conf | grep . || echo "6600") 
export LANG=C

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

			# POSTで受け取った文字列をデコード
			cat | urldecode | 

			# idにマッチする場合のみ"play"と最終フィールドを出力
			awk -F"=" '/[0-9]{1}/{print "play",$NF}' | 

			# mpcに渡し,出力を改行
			xargs mpc | sed "s/$/<br>/g" 2>&1
			)</p>

			<!-- リンク -->
			<button><a href="/cgi-bin/directory/directory.cgi">Directory</a></button>
			<button><a href="/cgi-bin/index.cgi">HOME</a></button>
			<button><a href="/cgi-bin/playlist/playlist.cgi">Playlist</a></button>

			<!-- キュー内の曲を表示 -->
			$(# キュー内の曲をプレイリストに保存

			# "SAVE_PLAYLIST"が"-q"でない場合に真
			echo "${SAVE_PLAYLIST}" | grep -q -v "\-q" &&

			# 真の場合,キュー内の曲をプレイリストに保存
			mpc $(echo "${SAVE_PLAYLIST}" | sed "s/_/ /" ) &&

			# メッセージを表示
			echo "<p>saved playlist</p>"

			# キュー内の曲を表示

			# キューされた曲を表示,検索しnlでidと区切り文字" ---::--- "を付与	
			mpc playlist | nl -n rz -s " ---::--- " | grep -i "${SEARCH_VAR}" |

 			awk -F" ---::--- " '{

 				# POSTでIDのみを渡せるようボタン化
 				print "<p><button name=button value="$1">"$NF"</button></p>"

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

