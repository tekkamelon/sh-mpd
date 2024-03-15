#!/bin/sh -eu

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
# x 実行されたコマンドの出力
# v 変数の表示

# ====== 変数の設定 ======
# ロケールの設定
export LC_ALL=C
export LANG=C

# GNU coreutilsの挙動をPOSIXに準拠
export POSIXLY_CORRECT=1

# 独自コマンドへPATHを通す
export PATH="$PATH:../../bin"

# ". (ドット)"コマンドで設定ファイルの読み込み
. ../settings/shmpd.conf
# ====== 変数の設定ここまで ======


# ===== 関数の宣言 ======
# POSTの処理,POSTが無い場合はステータスの表示
mpc_post () {

	# POSTを変数に代入
	cat_post=$(cat)

	# 変数展開でPOSTの"="をスペースに置換,デコードしmpcに渡す
	echo "${cat_post%=*} ${cat_post#*\=}"| urldecode | xargs mpc 2>&1 |

	# ": off"に<b>タグを,": on"に<strong>タグを,各行末に改行のタグを付与
	mpc_status2html

}

# プレイリスト及びディレクトリの検索,表示
playlist_and_directory () {

	# クエリを変数展開で加工,デコード,変数に代入
	search_str="$(echo "${QUERY_STRING#*\=}" | urldecode)"
	
	# プレイリスト一覧を出力,名前付きパイプにリダイレクト
	mpc lsplaylist >| lsplaylist.fifo &
	
	# ディレクトリを再帰的に出力,1フィールド目と"/"を出力,名前付きパイプにリダイレクト
	mpc listall | awk -F"/" '{print $1"/"}' >| listall.fifo &

	# 名前付きパイプ内のデータを出力,grepで固定文字列を大文字,小文字を区別せずに検索
	cat lsplaylist.fifo listall.fifo | grep -F -i "${search_str}" |

	# 区切り文字を"/"に指定
	awk -F"/" '{
		
		# ディレクトリの場合は真,プレイリストの場合は偽
		if(/.\/$/){

			# 真の場合はPOSTのvalueに"add"を指定し,1フィールド目をボタン化
			print "<p><button name=add value="$1">"$1"</button></p>"

		}else{

			# 偽の場合はPOSTの1フィールド目に"lsplaylist"を指定しボタン化
			print "<p><button name=load value="$0">"$0"</button>"
			print "<a href=#top>"
			print "<button name=playlist value="$0">...</button></a></p>"

		}
	
	}' |

	# 重複を削除
	awk '!a[$0]++{print $0}' &

}
# ===== 関数の宣言ここまで ======


# 名前付きパイプが無ければ作成
if [ ! -e "listall.fifo" ] && [ ! -e "lsplaylist.fifo" ] ; then

	mkfifo listall.fifo lsplaylist.fifo

fi


# ====== HTML ======
echo "Content-type: text/html"
echo ""

cat << EOS
<!DOCTYPE html>
<html>

    <head>

        <meta charset="UTF-8" />
		<meta name="viewport" content="width=device-width,initial-scale=1.0">
		<link rel="stylesheet" href="/cgi-bin/stylesheet/${stylesheet}">
		<link rel="icon" ref="/cgi-bin/image/favicon.ico">
		<link rel="apple-touch-icon" href="/cgi-bin/image/favicon.ico">
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
			<p>$(mpc_post)</p>

			<!-- # 全ての曲を追加する -->
			<p><button name=add value=/>add all songs</button></p>
			
		</form>

		<!-- リンク -->
		<button onclick="location.href='/cgi-bin/playlist/remove.cgi'">Remove</button>
		<button onclick="location.href='/cgi-bin/queued/queued.cgi'">Queued</button>
		<button onclick="location.href='/cgi-bin/index.cgi'">HOME</button>
		<button onclick="location.href='/cgi-bin/directory/directory.cgi'">Directory</button>

		<form name="music" method="POST" >

			<!-- mpc管理下のプレイリスト,ディレクトリを表示 -->
			$(playlist_and_directory)

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
# ====== HTMLここまで ======


# 名前付きパイプがあれば削除
if [ -e "listall.fifo" ] && [ -e "lsplaylist.fifo" ] ; then

	rm listall.fifo lsplaylist.fifo

fi
