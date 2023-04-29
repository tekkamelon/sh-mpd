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
			<p>search_word:<input type="text" name="search_word"></p>

		</form>
	
		<!-- 最下部へのジャンプ -->
		<p><a href="#bottom">jump to bottom</a></p>

		<!-- mpd.confで設定されたプレイリスト一覧を表示 -->
		<form name="music" method="POST" >

			<!-- ステータスを表示 -->
			<p>$(# POSTの"="をスペースに置換,デコードしmpcに渡す

			cat | sed "s/=/ /" | urldecode | xargs mpc 2>&1 | 

			# 3行目の": off"に<b>タグを,": on"に<strong>タグを,各行末に改行のタグを付与
			sed -e "3 s/: off/:<b> off<\/b>/g" -e  "3 s/: on/:<strong> on<\/strong>/g" -e "s/$/<br>/g"

			# 全ての曲を追加する
			echo "<p><button name=add value=/>add all songs</button></p>"
			
			)</p>

			<!-- リンク -->
			<button><a href="/cgi-bin/queued/queued.cgi">Queued</a></button>
			<button><a href="/cgi-bin/index.cgi">HOME</a></button>
			<button><a href="/cgi-bin/directory/directory.cgi">Directory</a></button>

			<!-- mpc管理下のプレイリスト,ディレクトリを表示 -->
			$(# プレイリスト及びディレクトリの検索などの処理

 			# 空文字を変数に代入
			search_str=""

			# クエリがある場合はデコード,変数に代入
			test -n "${QUERY_STRING#*\=}" && search_str=$(echo "${QUERY_STRING#*\=}" | urldecode)
			
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
		<button><a href="/cgi-bin/queued/queued.cgi">Queued</a></button>
		<button><a href="/cgi-bin/index.cgi">HOME</a></button>
		<button><a href="/cgi-bin/directory/directory.cgi">Directory</a></button>
	</footer>

	<!-- 最上部へのジャンプ -->
	<p><a href="#top">jump to top</a></p>

</html>
EOS

