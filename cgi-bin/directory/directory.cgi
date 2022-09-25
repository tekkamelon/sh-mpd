#!/bin/sh -euxv

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# 環境変数で接続先ホストを設定,ファイルがない場合はローカルホスト
export MPD_HOST=$(# hostnameを変数に代入
	hostname_var=$(cat ../settings/hostname)
	# 変数展開で加工
	echo ${hostname_var#export\&MPD_HOST\=} | grep -q . || echo "localhost"
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
		<h1>Directory</h1>
	</header>

    <body>
		<h4>hostname: $(echo $MPD_HOST)</h4>
		<!-- ステータスの表示 -->
		<p>$(mpc status | sed "s/$/<br>/g")</p>
		<form name="FORM" method="GET" >

			debug_info:$(echo ${QUERY_STRING} | urldecode)
				
					<!-- 検索ワードの入力欄 -->
						<p>search_word:<input type="text" name="search_word"></p>
				
		</form>
	
		<!-- mpd.confで設定されたディレクトリ配下を表示 --> 
		<form name="music" method="POST" >

				<p>$(# POSTで受け取った文字列を変数に代入
				cat_post=$(cat)

				# POSTを変数展開で加工,デコードしxargsでmpcに渡す
				# xargsを使用しないと文字列が空の場合,全ての曲がキューに追加されるため
				echo ${cat_post#*\=} | urldecode | xargs mpc insert &&

				# 上記コマンドの正常終了時のみ,POSTが空かどうかを判定
				echo ${cat_post#*\=} | grep -q . && 

					# 空でないの場合,次の曲を再生
					mpc next | sed "s/$/<br>/g" 2>&1

					# 空の場合は何もしない
					:
				)</p>

				<!-- リンク -->
				<button><a href="/cgi-bin/queued/queued.cgi">Queued</a></button>
				<button><a href="/cgi-bin/index.cgi">HOME</a></button>
				<button><a href="/cgi-bin/playlist/playlist.cgi">Playlist</a></button>

				<!-- mpc管理下のディレクトリを再帰的に表示,awkで出力をボタン化 -->
				$(# クエリを変数展開で加工,空でない場合に真,空の場合に偽
				test -n "${QUERY_STRING#*\=}" &&

					# 真の場合はクエリを変数展開で加工,デコード
					search_var=$(echo ${QUERY_STRING#*\=} | urldecode) ||
					
					# 偽の場合は"."で全てにマッチングする行を表示
					search_var="." 

				mpc listall | grep -i ${search_var} |
				awk '{print "<p><button name=button value="$0">"$0"</button></p>"}'
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
