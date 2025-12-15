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
tmp_path="$(cd "$(dirname "${0}")/../../bin" && pwd)"
export PATH="${PATH}:${tmp_path}"

# shmpd.confの有無を確認
if [ -f ../settings/shmpd.conf ] ; then

	# 設定ファイルを読み込み
	. ../settings/shmpd.conf


else

	# デフォルトの環境変数を代入
	export MPD_HOST="127.0.0.1"
	export MPD_PORT="6600"

	stylesheet="stylesheet.css"

fi

# POSTを変数に代入
cat_post=$(cat)

# クエリを変数展開で加工,デコード,変数に代入
search_str="$(echo "${QUERY_STRING#*\=}" | urldecode)"

# 再生中の楽曲
mpc_current="$(mpc current)"
# ====== 変数の設定ここまで ======


# ===== 関数の宣言 ======
# URLからホスト名を取得
cgi_host () {

	echo "${HTTP_REFERER}" | cut -d"/" -f3

}

mpc_post () {

	# 複数の項目の削除に対応
	# POSTの"="を" "に置換,"&del"を削除
	echo "${cat_post}" | sed -e "s/=/ /g" -e "s/\&del//g" |

	xargs mpc 2>&1 |

	mpc_status2html -v mpc_current="${mpc_current}" 

	# 曲の削除の結果の表示,"cat_post"があれば真
	if [ -n "${cat_post}" ] ; then

		# 真の場合,ステータスとメッセージを表示
		mpc status 2>&1 | mpc_status2html && echo "<p>Remove selected song!</p>"

	fi

}

# キュー内の曲の検索,チェックボックス付きで表示
queued () {

	# 再生中の楽曲
	mpc_current="$(mpc current)"

	# キューされた曲をgrepで検索,idと区切り文字":"を付与
	mpc playlist | grep -F -i -n "${search_str}" |

	# キュー内の楽曲をHTMLで表示,現在再生中の楽曲は"[Now Playing]"を付与
	# "queued_song"にシェル変数"current",post_nameに"del"を渡す
	queued_song -v mpc_current="${mpc_current}" -v post_name="del" 

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
		<title>Remove Queued Song - sh-MPD:$(cgi_host) -</title>
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

			.search-form {
				display: flex;
				gap: 0.5rem;
			}

			.search-form input[type="text"] {
				flex-grow: 1;
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
			<h1>Remove Queued Song</h1>
			<p><strong>Host:</strong> ${MPD_HOST} | <strong>Port:</strong> ${MPD_PORT}</p>
		</header>

		<main>
			<div style="text-align: center; margin-bottom: 1rem;">
				<button onclick="window.scrollTo(0, document.body.scrollHeight);" style="padding: 0.5rem 1rem; background-color: #007bff; color: white; border: none; border-radius: 4px; cursor: pointer;">最下部へ移動</button>
			</div>
			<section>
				<h2>Search</h2>
				<form name="FORM" method="GET" class="search-form">
					<input type="text" placeholder="Enter search term..." name="input_string">
					<button type="submit">Search</button>
				</form>
			</section>

			<section>
				<h2>Status</h2>
				<pre>$(mpc_post)</pre>
			</section>

			<section>
				<h2>Queue</h2>
				<form name="music" method="POST">
					<input type="submit" value="Remove Selected Song">
					<pre>$(queued)</pre>
					<input type="submit" value="Remove Selected Song">
				</form>
			</section>
			<div style="text-align: center; margin-top: 1rem;">
				<button onclick="window.scrollTo(0, 0);" style="padding: 0.5rem 1rem; background-color: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer;">最上部へ移動</button>
			</div>
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
