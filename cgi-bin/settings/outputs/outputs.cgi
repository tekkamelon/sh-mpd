#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# 環境変数の設定
export LANG=C

# ホスト名,ポート番号を設定,データがない場合は"localhost","6600"
host="$(cat ../hostname)"
port="$(cat ../port_conf)"

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
		<link rel="stylesheet" href="/cgi-bin/stylesheet/$(cat ../css_conf)">
		<link rel="icon" ref="image/favicon.svg">
		<!-- <link rel="apple-touch-icon" href="image/favicon.svg"> -->
        <title>sh-MPD</title>
    </head>

	<header>
		<h1>settings</h1>
	</header>

    <body>
		<form name="setting" method="POST" >
			
			<h4>host:${MPD_HOST}<br>port:${MPD_PORT}<br></h4>

			<!-- 出力先デバイスの設定 -->
			<h3>ountput devices list</h3>
			$(# POSTを変数に代入

			cat_post=$(cat)

			# POSTの有無を確認,あれば真,無ければ偽
			if [ -n "${cat_post}" ] ; then
			
				# 真の場合はPOSTを変数展開で"="をスペースに置換
				echo "${cat_post%%\=*}" "${cat_post#*\=}" 
				
			else

				# 偽の場合は"outputs"を出力
				echo "outputs"

			fi | 

			# 出力をmpcに渡す
			xargs mpc |

			# スペースを区切り文字に設定,1フィールド目が"Output"の行をボタン化
			awk -F" " '$1 == "Output"{

				print "<p><button name=toggleoutput value="$2">"$0"</button></p>"

 			}'

			)

			<p>$(# ステータスを表示
			
			# mpcのエラー出力ごとsedに渡す
			mpc status 2>&1 |

			# 3行目の": off"に<b>タグを,": on"に<strong>タグを,各行末に改行のタグを付与
			sed -e "3 s/: off/:<b> off<\/b>/g" -e  "3 s/: on/:<strong> on<\/strong>/g" -e "s/$/<br>/g"

			)</p>

		</form>
    </body>

	<footer>	
		<!-- リンク -->
		<button><a href="/cgi-bin/queued/queued.cgi">Queued</a></button>
		<button><a href="/cgi-bin/directory/directory.cgi">Directory</a></button>
		<button><a href="/cgi-bin/index.cgi">HOME</a></button>
		<button><a href="/cgi-bin/playlist/playlist.cgi">Playlist</a></button>
		<button><a href="/cgi-bin/settings/settings.cgi">Settings</a></button>
	</footer>	

</html>
EOS

