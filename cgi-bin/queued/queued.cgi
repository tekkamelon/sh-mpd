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

# "foo=bar"の"foo","bar"をそれぞれ抽出
post_key="${cat_post%\=*}"
post_value="${cat_post#"${post_key}"\=}"

# クエリを変数展開し代入
query_check="${QUERY_STRING#*\=}"

# "search"か"save"を抽出
search_or_save="${query_check%%&*}"

# テキストエリアからの入力を抽出,デコード
str_name=$(echo "${query_check#"${search_or_save}"\&input_string\=}" | urldecode)

# POSTがあれば真,無ければ偽
if [ -n "${cat_post}" ] ; then
	
	# POSTがあれば選択された楽曲を再生
	mpc_result=$(mpc "${post_key}" "${post_value}")
	
	# プレイリストの保存後に楽曲が選択された場合
	str_name=""

# 偽の場合は"search_or_save"が"save"であれば真
elif [ "${search_or_save}" = "save" ] ; then

	# 標準エラー出力も変数に代入するために一時的に"set -e"を解除
	set +e
	mpc_result=$(mpc "${search_or_save}" "${str_name}" 2>&1)
	set -e

else

	mpc_result=$(mpc status)

fi

# 再生中の楽曲
mpc_current="$(mpc current)"
# ====== 変数の設定ここまで ======


# ===== 関数の宣言 ======
# URLからホスト名を取得
cgi_host () {

	echo "${HTTP_REFERER}" | cut -d"/" -f3

}

mpc_status () {

	# プレイリスト名が入力されかつ重複がない場合に真
	if [ -n "${str_name}" ] && [ "${search_or_save}" = "save" ] && [ "${mpc_result%:*}" != "MPD error" ] ; then

		# ステータスとメッセージを出力
		mpc status

		echo "saved playlist:${str_name}"

	else

		echo "${mpc_result}"

	fi |

	# 出力をhtmlに加工
	mpc_status2html -v mpc_current="${mpc_current}" 

}

# キュー内の曲の検索
queued () {

	# プレイリストの保存時には"str_name"に空文字を代入
	test "${search_or_save}" = "save" && str_name=""

	# キューされた曲をgrepで検索,idと区切り文字":"を付与
	mpc playlist | grep -F -i -n "${str_name}" |

	# キュー内の楽曲をHTMLで表示,現在再生中の楽曲は"[Now Playing]"を付与
	# "queued_song"にシェル変数"current",post_nameに"play"を渡す
	queued_song -v mpc_current="${mpc_current}" -v post_name="play"

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
		<title>Queued - sh-MPD:$(cgi_host) -</title>
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

			.form-grid {
				display: grid;
				grid-template-columns: auto 1fr;
				gap: 0.5rem;
				align-items: center;
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
			<h1>Queued</h1>
			<p><strong>Host:</strong> ${MPD_HOST} | <strong>Port:</strong> ${MPD_PORT}</p>
		</header>

		<main>
			<section>
				<h2>Playlist Operations</h2>
				<form name="FORM" method="GET" class="form-grid">
					<select name="button">
						<option value="search">Search</option>
						<option value="save">Save Playlist</option>
					</select>
					<input type="text" placeholder="Search word or playlist name" name="input_string">
					<button type="submit">Go</button>
				</form>
			</section>

			<section>
				<h2>Status</h2>
				<pre>$(mpc_status)</pre>
			</section>

			<section>
				<h2>Queue</h2>
				<form name="music" method="POST">
					<pre>$(queued)</pre>
				</form>
			</section>
		</main>

		<aside>
			<nav>
				<h2>Menu</h2>
				<ul>
					<li><a href="/cgi-bin/index.cgi">Home</a></li>
					<li><a href="/cgi-bin/directory/directory.cgi">Directory</a></li>
					<li><a href="/cgi-bin/playlist/playlist.cgi">Playlist</a></li>
					<li><a href="/cgi-bin/settings/settings.cgi">Settings</a></li>
					<li><a href="/cgi-bin/queued/remove.cgi">Remove</a></li>
				</ul>
			</nav>
		</aside>

	</body>

</html>
EOS
# ====== HTMLここまで ======
