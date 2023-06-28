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
		<h1>Directory</h1>

	</header>

    <body>

		<h4>host:${MPD_HOST}<br>port:${MPD_PORT}<br></h4>
		<form name="FORM" method="GET" >

			<!-- 検索ワードの入力欄 -->
			<p><input type="text" placeholder="search_word" name="search_word"></p>
				
		</form>
	
		<form name="music" method="POST" >

		<!-- 最下部へのジャンプ -->
		<p><a href="#bottom">jump to bottom</a></p>

			<!-- ステータスを表示 --> 
			<p>$(# POSTの有無に応じてmpcでの処理を分岐

			# urldecodeにPATHが通っていなければ偽
			type urldecode > /dev/null 2>&1 ||

			# 偽の場合はリンクを表示
			echo '<h2><a href="https://github.com/ShellShoccar-jpn/misc-tools">please install "urldecode"</a></h2>'

			# POSTで受け取った文字列を変数として宣言
			cat_post=$(cat)

			# POSTを変数展開で加工,文字列があれば真,無ければ偽
			if [ -n "${cat_post#*\=}" ] ; then 

				# 真の場合はPOSTを変数展開で"="をスペースに置換,曲名をダブルクォートで括って出力
				echo "${cat_post%\=*} ""\"${cat_post#*\=}\"" |
	
				# デコード,mpcに渡す
				urldecode | xargs mpc &

				# "next"を出力
				echo "next"

			# 偽の場合はPOSTを変数展開,"insertresult="であれば真,それ以外で偽
			elif [ "${cat_post#\=*}" = "insertresult=" ] ; then

				# 真の場合はクエリをデコードし"search_str"に代入
				search_str=$(echo "${QUERY_STRING#*\=}" | urldecode)

				# 曲の一覧から"search_str"で検索,結果を挿入
				mpc listall | grep -F -i "${search_str}" | mpc insert &

				# "next"を出力
				echo "next"

			else

				# 偽の場合は"status"を出力
				echo "status"
			
			fi |

			# 出力をmpcに渡す
			xargs mpc 2>&1 |
			
			# 3行目の": off"に<b>タグを,": on"に<strong>タグを,各行末に改行のタグを付与
			sed -e "3 s/: off/:<b> off<\/b>/g" -e  "3 s/: on/:<strong> on<\/strong>/g" -e "s/$/<br>/g"

			# 全ての曲を追加する
			echo "<p><button name=add value=/>add all songs</button></p>"

			)</p>

		</form>

		<!-- リンク -->
		<button onclick="location.href='/cgi-bin/queued/queued.cgi'">Queued</button>
		<button onclick="location.href='/cgi-bin/index.cgi'">HOME</button>
		<button onclick="location.href='/cgi-bin/playlist/playlist.cgi'">Playlist</button>

		<form name="music" method="POST" >

			<!-- mpc管理下のディレクトリを再帰的に表示 -->
			$(# 曲の一覧をgrepで検索

			# クエリをデコードし"search_str"に代入
			search_str=$(echo "${QUERY_STRING#*\=}" | urldecode)

			# 曲の一覧から"search_str"で検索
			mpc listall | grep -F -i "${search_str}" |

			awk '{

				# 出力をボタン化
				print "<p><button name=insert value="$0">"$0"</button></p>"

			}

			END{

				# 検索結果を挿入するボタン
				print "<p><button name=insertresult value=>insert search result</button></p>"

			}'

			)

		</form>
		
	</body>

	<!-- "jump to bottom"のジャンプ先 -->
	<div id="bottom"></div>

	<footer>

		<!-- リンク -->
		<button onclick="location.href='/cgi-bin/queued/queued.cgi'">Queued</button>
		<button onclick="location.href='/cgi-bin/index.cgi'">HOME</button>
		<button onclick="location.href='/cgi-bin/playlist/playlist.cgi'">Playlist</button>

	</footer>

	<!-- 最上部へのジャンプ -->
	<p><a href="#top">jump to top</a></p>

</html>
EOS

