#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# 環境変数の設定
# ホスト名,ポート番号を設定,データがない場合は"localhost","6600"
export LANG=C
export MPD_HOST=$(cat ../settings/hostname | grep . || echo "localhost") 
export MPD_PORT=$(cat ../settings/port_conf | grep . || echo "6600") 

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
			
			# クエリを変数展開で加工,awkでの処理結果を変数に代入
			save_playlist=$(

			echo "${QUERY_STRING#*\=}" | 

			# "=","&"を区切り文字に指定,1フィールド目の"save"の有無を判定
			awk -F'[=&]' '$1 == "save"{

					# 1フィールド目と最終フィールドを出力
					print $1,$NF

			# 出力をデコード
			}' | urldecode

			)

			# コマンドをグルーピングし"save_playlist"を出力,POSTをデコードし出力
			{ echo "${save_playlist}" & cat | sed "s/=/ /" ; } |

			# mpcに渡し出力を改行
			xargs mpc 2>&1 | sed "s/$/<br>/g"

			# プレイリストのセーブ時のステータスの表示,"save_playlist"が空ではない場合に真
			test -n "${save_playlist}" &&

			# 真の場合,ステータスとメッセージを表示
			mpc status 2>&1 | sed "s/$/<br>/g" && echo "<p>saved playlist:"${save_playlist#* }"</p>"

			)</p>

			<!-- リンク -->
			<button><a href="/cgi-bin/directory/directory.cgi">Directory</a></button>
			<button><a href="/cgi-bin/index.cgi">HOME</a></button>
			<button><a href="/cgi-bin/playlist/playlist.cgi">Playlist</a></button>

			<!-- キュー内の曲を表示 -->
			$(# キューされた曲をgrepで検索,idと区切り文字":"を付与

			# クエリを変数展開で加工,デコード,変数に代入
			search_str=$(echo "${QUERY_STRING#*\=*&*\=}" | urldecode)

			mpc playlist | grep -F -i -n "${search_str}" | 

			# ":"を">"に置換,標準入力をタグ付きで出力
			awk '{

				sub(":" , ">")

				print "<p><button name=play value="$0"</button></p>"

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

