#!/bin/sh

# shellcheck disable=SC1091,SC2154

# e 返り値が0以外で停止
# u 未定義の変数参照で停止
set -eu

# ====== 変数の設定 ======
# ロケールの設定
export LC_ALL=C
export LANG=C

# GNU coreutilsの挙動をPOSIXに準拠
export POSIXLY_CORRECT=1

# 独自コマンドへPATHを通す
tmp_path="$(cd "$(dirname "${0}")/../../../bin" && pwd)"
export PATH="${PATH}:${tmp_path}"

# shmpd.confの有無を確認
if [ -f ../shmpd.conf ] ; then

	# 設定ファイルを読み込み
	. ../shmpd.conf


else

	# デフォルトの環境変数を代入
	export MPD_HOST="127.0.0.1"
	export MPD_PORT="6600"

	stylesheet="stylesheet.css"

fi

# クエリを変数展開し代入
query_check="${QUERY_STRING#*\=}"

# クエリを変数展開で加工,文字列があれば真,なければ偽
if [ -n "${query_check}" ] ; then

	# 真の場合は変数の一覧を出力,設定ファイルへリダイレクト
	cat <<- EOF >| ../shmpd.conf &
	export MPD_HOST="${MPD_HOST}"
	export MPD_PORT="${MPD_PORT}"
	img_server_host="${img_server_host}"
	img_server_port="${img_server_port}"
	stylesheet="${query_check}"
	EOF

	# "stylesheet"に"query_check"を代入
	stylesheet="${query_check}"

	# メッセージを代入
	export ECHO_MESSAGE="<p>changed css:${stylesheet}</p>"

else

	# 空文字を代入
	export ECHO_MESSAGE=""

fi
# ====== 変数の設定ここまで ======


# ===== 関数の宣言 ======
css_list () {

	find ../../stylesheet -name "*.css" |

	awk -F"/" '{

		# 最終フィールドにタグを付与し出力
		print "<p><button name=css value="$NF">"$NF"</button></p>"

	}'

}
# ===== 関数の宣言ここまで ======


# ====== HTML ======
echo "Content-type: text/html"
echo ""

cat << EOS
<!DOCTYPE html>
<html lang="ja">

	<head>

		<meta charset="UTF-8">
		<meta name="viewport" content="width=device-width, initial-scale=1.0">
		<link rel="stylesheet" href="/cgi-bin/stylesheet/${stylesheet}">
		<link rel="icon" href="/cgi-bin/image/favicon.ico">
		<link rel="apple-touch-icon" href="/cgi-bin/image/favicon.ico">
		<title>CSS Select - sh-MPD:$(cgi_host) -</title>
		<style>
			body {
				display: grid;
				grid-template-areas:
					"header"
					"main"
					"sidebar";
				gap: 1rem;
				padding: 1rem;
			}

			@media (min-width: 768px) {
				body {
					grid-template-columns: 3fr 1fr;
					grid-template-areas:
						"header header"
						"main   sidebar";
				}
			}

			header { grid-area: header; text-align: center; }
			main { grid-area: main; }
			aside { grid-area: sidebar; }

			section {
				margin-bottom: 2rem;
				padding: 1rem;
				border: 1px solid #ccc;
				border-radius: 8px;
			}

			aside nav ul {
				list-style: none;
				padding: 0;
			}

			aside nav li a {
				display: block;
				padding: 0.75rem;
				margin-bottom: 0.5rem;
				text-decoration: none;
				text-align: center;
				border: 1px solid;
				border-radius: 4px;
			}
		</style>
	</head>

	<body>

		<header>
			<h1>CSS Settings</h1>
		</header>

		<main>
			<section>
				<h2>Select CSS</h2>
				<form name="setting" method="GET">
					${ECHO_MESSAGE}
					<pre>$(css_list)</pre>
				</form>
			</section>
		</main>

		<aside>
			<nav>
				<h2>Menu</h2>
				<ul>
					<li><a href="/cgi-bin/index.cgi">Home</a></li>
					<li><a href="/cgi-bin/queued/queued.cgi">Queued</a></li>
					<li><a href="/cgi-bin/directory/directory.cgi">Directory</a></li>
					<li><a href="/cgi-bin/playlist/playlist.cgi">Playlist</a></li>
					<li><a href="/cgi-bin/settings/settings.cgi">Settings</a></li>
				</ul>
			</nav>
		</aside>

	</body>

</html>
EOS
# ====== HTMLここまで ======
