#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# 環境変数で接続先ホスト,ポート番号を設定,データがない場合は"localhost","6600"
export LANG=C
export MPD_HOST=$(cat ../settings/hostname | grep . || echo "localhost") 
export MPD_PORT=$(cat ../settings/port_conf | grep . || echo "6600") 

# "SAVE_PLAYLIST","SEARCH_VAR"を設定
export $(# クエリ内の文字列をawkで判定し,処理を分け環境変数へ代入

	# クエリを変数展開で加工
	echo "${QUERY_STRING#*\=}" | 

	# プレイリストのセーブの処理,"save&input_string=(任意の1文字以上)"にマッチした場合の処理
	awk -F'[=&]' '/save&input_string=./{

		print "SAVE_PLAYLIST="$1"_"$NF
		print "SEARCH_VAR=\"\""

	}

	# 検索の処理,"search&input_string=(任意の1文字以上)"にマッチした場合の処理
	/search&input_string=./{

		print "SAVE_PLAYLIST="
		print "SEARCH_VAR="$NF
	}
	
	# "&input_string=(任意の1文字以上)"にマッチしなかった場合の処理
	!/&input_string=./{

		print "SAVE_PLAYLIST="
		print "SEARCH_VAR=\"\""
		
	# デコード,並列化し環境変数へ代入
	}' | urldecode | xargs -L 1 -P 2

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
		<h4>host:${MPD_HOST}<br>port:${MPD_PORT}<br></h4>
		<!-- playlistの処理 -->
		<form name="FORM" method="GET" >

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
			
			<!-- ステータスの表示 -->
			<p>$(# 選択された曲の再生,プレイリストの保存の処理

			# "SAVE_PLAYLIST"とデコードされたPOSTを出力
			printf "${SAVE_PLAYLIST}\n$(cat | urldecode)\n" |

			# 最初の"=","_"をスペースに置換
			sed "s/\=\|_/ /" |

			# mpcに渡し出力を改行
			xargs mpc 2>&1 | sed "s/$/<br>/g"

			# プレイリストのセーブ時のステータスの表示,"SAVE_PLAYLIST"が空ではない場合に真
			test -n "${SAVE_PLAYLIST}" &&

			# 真の場合,ステータスとメッセージを表示
			mpc status 2>&1 | sed "s/$/<br>/g" && echo "<p>saved playlist:"${SAVE_PLAYLIST#*\_}"</p>"

			)</p>

			<!-- リンク -->
			<button><a href="/cgi-bin/directory/directory.cgi">Directory</a></button>
			<button><a href="/cgi-bin/index.cgi">HOME</a></button>
			<button><a href="/cgi-bin/playlist/playlist.cgi">Playlist</a></button>

			<!-- キュー内の曲を表示 -->
			$(# キューされた曲をgrepで検索,idと区切り文字";;"を付与

			mpc playlist | grep -F -i -n "${SEARCH_VAR}" | sed "s/:/;;/" |

 			awk -F";;" '{

 				# POSTでIDのみを渡せるようボタン化
 				print "<p><button name=play value="$1">"$NF"</button></p>"

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

