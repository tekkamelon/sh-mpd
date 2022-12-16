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
				<p>$(# POSTをawkに渡す

				# 区切り文字を"="に指定,POSTの1フィールド目が"lsplaylist"の場合
				cat | awk -F"=" '$1 == "load"{

					# 1フィールド目と最終フィールド目を出力
					print $1 , $NF

				}

				# POSTの1フィールド目が"add"の場合
				$1 == "add"{

					# 1フィールド目と最終フィールド目を出力
					print $1 , $NF

				# 出力をデコード,mpcに渡し,改行を付与し出力
				}' | urldecode | xargs mpc | sed "s/$/<br>/g"
				
				)</p>

				<!-- リンク -->
				<button><a href="/cgi-bin/queued/queued.cgi">Queued</a></button>
				<button><a href="/cgi-bin/index.cgi">HOME</a></button>
				<button><a href="/cgi-bin/directory/directory.cgi">Directory</a></button>

				<!-- mpc管理下のプレイリストを表示 -->
				$(# 変数展開でクエリを加工,デコードし,文字列の有無を判定

				search_var=$(echo "${QUERY_STRING#*\=}" | urldecode | grep . || echo ".")

				##### コマンドのグルーピング #####
				# プレイリスト一覧を出力
				{ mpc lsplaylist ; 

				# mpd管理下ディレクトリを" -- "付きで出力,cutで親ディレクトリのみを出力
				mpc listall -f "[ -- %file%]" | cut -d"/" -f1 ; } |
				##### グルーピングの終了 #####

				# grepで検索,重複を削除
				grep -F -i "${search_var}" | awk '!a[$0]++{print $0}' |

				awk '{
					
					# 先頭に" -- "がある場合は真,なければ偽
					if(/^ -- /){

						# 真の場合は" -- "を削除,POSTの1フィールド目に"add"を指定しボタン化
						sub(" -- " , "" , $0)

						print "<p><button name=add value="$0">"$0"</button></p>"

 					}

					else{
 
						# 偽の場合はPOSTの1フィールド目に"lsplaylist"を指定しボタン化
	 					print "<p><button name=load value="$0">"$0"</button></p>"

					}
				
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

