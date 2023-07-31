#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# 環境変数の設定
export LANG=C

# ホスト名,ポート番号を設定,データがない場合は"localhost","6600"
host="$(cat ../settings/hostname)"
port="$(cat ../settings/port_conf)"

export MPD_HOST="${host}"
export MPD_PORT="${port}"

echo "Content-type: text/html"
echo ""

cat << EOS
<!DOCTYPE html>
<html>

    <head>

        <meta charset="UTF-8" />
		<meta name="viewport" content="width=device-width,initial-scale=1.0">
		<link rel="stylesheet" href="/cgi-bin/stylesheet/$(cat ../settings/css_conf)">
		<link rel="icon" ref="image/favicon_ios.ico">
		<link rel="apple-touch-icon" href="image/favicon_ios.ico">
        <title>sh-MPD</title>

    </head>
	
	<!-- "jump to top"のジャンプ先 -->
	<div id="top"></div>

	<header>
	
		<h1>Playlist</h1>
		
	</header>

    <body>
	
		<h4>${MPD_HOST}<br>port:${MPD_PORT}<br></h4>

		<!-- 入力欄の設定 -->
		<form name="FORM" method="GET" >

			<!-- 検索ワードの入力欄 -->
			<p><input type="text" placeholder="search word" name="search_word"></p>

		</form>
	
		<!-- 最下部へのジャンプ -->
		<p><a href="#bottom">jump to bottom</a></p>

		<!-- mpd.confで設定されたプレイリスト一覧を表示 -->
		<form name="music" method="POST" >

			<!-- ステータスを表示 -->
			<p>$(# POSTの処理,POSTが無い場合はステータスの表示

			# urldecodeにPATHが通っていなければ偽
			type urldecode > /dev/null 2>&1 ||

			# 偽の場合はリンクを表示
			echo '<h2><a href="https://github.com/ShellShoccar-jpn/misc-tools">please install "urldecode"</a></h2>'
			
			# POSTの"="をスペースに置換,デコードしmpcに渡す
			cat | sed "s/=/ /" | urldecode | xargs mpc 2>&1 | 

			# 3行目の": off"に<b>タグを,": on"に<strong>タグを,各行末に改行のタグを付与
			sed -e "3 s/: off/:<b> off<\/b>/g" -e  "3 s/: on/:<strong> on<\/strong>/g" -e "s/$/<br>/g"

			# 全ての曲を追加する
			echo "<p><button name=add value=/>add all songs</button></p>"
			
			)</p>

		</form>

		<!-- リンク -->
		<button onclick="location.href='/cgi-bin/playlist/remove.cgi'">Remove</button>
		<button onclick="location.href='/cgi-bin/queued/queued.cgi'">Queued</button>
		<button onclick="location.href='/cgi-bin/index.cgi'">HOME</button>
		<button onclick="location.href='/cgi-bin/directory/directory.cgi'">Directory</button>

		<form name="music" method="POST" >

			<!-- mpc管理下のプレイリスト,ディレクトリを表示 -->
			$(# プレイリスト及びディレクトリの検索などの処理

			# クエリを変数展開で加工,デコード,変数に代入
			search_str="$(echo "${QUERY_STRING#*\=}" | urldecode)"
			
			# プレイリスト一覧を出力,名前付きパイプにリダイレクト
			mpc lsplaylist >| fifo_lsplaylist &
			
			# ディレクトリを再帰的に出力,1フィールド目と"/"を出力,名前付きパイプにリダイレクト
			mpc listall | awk -F"/" '{print $1"/"}' >| fifo_listall &

			# 名前付きパイプ内のデータを出力,grepで固定文字列を大文字,小文字を区別せずに検索
			cat fifo_lsplaylist fifo_listall | grep -F -i "${search_str}" |

			# 区切り文字を"/"に指定
			awk -F"/" '{
				
				# 行末に"/"がある場合は真,なければ偽
				if(/.\/$/){

					# 真の場合はPOSTのvalueに"add"を指定し,1フィールド目をボタン化
					print "<p><button name=add value="$1">"$1"</button></p>"

 				}

				else{
 
					# 偽の場合はPOSTの1フィールド目に"lsplaylist"を指定しボタン化
	 				print "<p><button name=load value="$0">"$0"</button></p>"

				}
			
			}' |

			# 重複を削除
			awk '!a[$0]++{print $0}' &

			)

		</form>

	</body>

	<!-- "jump to bottom"のジャンプ先 -->
	<div id="bottom"></div>

	<footer>
	
		<!-- リンク -->
		<button onclick="location.href='/cgi-bin/playlist/remove.cgi'">Remove</button>
		<button onclick="location.href='/cgi-bin/queued/queued.cgi'">Queued</button>
		<button onclick="location.href='/cgi-bin/index.cgi'">HOME</button>
		<button onclick="location.href='/cgi-bin/directory/directory.cgi'">Directory</button>
		
	</footer>

	<!-- 最上部へのジャンプ -->
	<p><a href="#top">jump to top</a></p>

</html>
EOS

