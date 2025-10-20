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
tmp_path="$(cd "$(dirname "${0}")/../bin" && pwd)"
export PATH="${PATH}:${tmp_path}"

# shmpd.confの有無を確認
if [ -f settings/shmpd.conf ] ; then

	# 設定ファイルを読み込み
	. settings/shmpd.conf

else

	# デフォルトの環境変数を代入
	export MPD_HOST="127.0.0.1"
	export MPD_PORT="6600"

	stylesheet="stylesheet.css"

fi

# POSTを変数に代入
cat_post=$(cat)

# POSTを変数展開し代入
post_check="${cat_post#*\=}"

# "foo=bar"の"foo","bar"をそれぞれ抽出
post_key="${post_check%\&*}"
post_value="${post_check#*\&*\=}"

# クエリを変数展開し代入
query_check="${QUERY_STRING#*\=}"

# URLのホスト名を取得
url_hostname="$(cgi_host)"
# ====== 変数の設定ここまで ======


# ===== 関数の宣言 ======
# 変数展開で加工したPOSTの文字列の有無を判定,あればクエリを加工しmpcへ渡す
mpc_post () {

    # POST値があればデコードしてmpcに渡す
    if [ -n "${post_value}" ]; then

        echo "${post_key}" "'${post_value}'" | urldecode

    else

        # クエリ値を加工
        echo "${query_check}" |

		sed -e "s/_\-/ \-/g" -e "s/_\%2B/ \+/g" -e "s/\%25/\%/g"

    fi |

	# mpcのエラー出力ごと渡す
	xargs mpc 2>&1 |

	mpc_status2html -v url_hostname="${url_hostname}"

}

# カバーアートの取得
coverart () {

	# 変数img_server_host,img_server_portの有無を確認
    if [ -z "${img_server_host:-}" ] || [ -z "${img_server_port:-}" ]; then

        echo ""
        return

    fi

	# 現在の曲を変数に代入
    current_song="$(mpc current -f "%file%")"

	# 曲のパスを変数に代入
    song_path="${current_song%/*}"

	# カバーアートのURLを出力
    echo "http://${img_server_host}:${img_server_port}/${song_path}/Folder.jpg"

}

# 次の曲の表示
next_song () {

	# "mpc queued"を変数に代入
	queued=$(mpc queued)

	# "queued"があれば真,なければ偽
	if [ -n "${queued}" ] ; then

		# 真の場合は"queued"を表示
		echo "${queued}"

	else

		# 偽の場合はメッセージを表示
		echo "next song not found"

	fi

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
		<link rel="icon" href="$(coverart)">
		<link rel="apple-touch-icon" href="$(coverart)">
		<title>HOME - sh-MPD:${url_hostname} -</title>
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

			.control-grid {
				display: grid;
				grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
				gap: 0.5rem;
			}

			.control-grid button {
				width: 100%;
				padding: 0.75rem;
				text-align: center;
				cursor: pointer;
			}

			.search-form {
				display: flex;
				gap: 0.5rem;
			}

			.search-form input[type="text"] {
				flex-grow: 1;
			}

			.cover-art {
				max-width: 100%;
				height: auto;
				display: block;
				margin: 1rem auto;
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
			<h1>sh-MPD</h1>
			<p>A shell script and CGI-based MPD user interface.</p>
			<p><strong>Host:</strong> ${MPD_HOST} | <strong>Port:</strong> ${MPD_PORT}</p>
		</header>

		<main>
			<section>
				<h2>Control Panel</h2>
				<form name="control_form" method="GET">
					<div class="control-grid">
						<button name="button" value="status">Status</button>
						<button name="button" value="volume_-100">Mute</button>
						<button name="button" value="volume_-5">Vol -</button>
						<button name="button" value="volume_+5">Vol +</button>
						<button name="button" value="prev">Prev</button>
						<button name="button" value="toggle">Play/Pause</button>
						<button name="button" value="stop">Stop</button>
						<button name="button" value="next">Next</button>
						<button name="button" value="repeat">Repeat</button>
						<button name="button" value="random">Random</button>
						<button name="button" value="single">Single</button>
						<button name="button" value="shuffle">Shuffle</button>
						<button name="button" value="clear">Clear</button>
						<button name="button" value="update">Update DB</button>
						<button name="button" value="seek_-5%">Seek -</button>
						<button name="button" value="seek_+5%">Seek +</button>
					</div>
				</form>
			</section>

			<section>
				<h2>Search</h2>
				<form name="search_form" method="POST" class="search-form">
					<select name="args">
						<option value="searchplay">Fuzzy</option>
						<option value="searchplay artist">Artist</option>
						<option value="searchplay album">Album</option>
						<option value="searchplay title">Title</option>
						<option value="searchplay filename">Filename</option>
					</select>
					<input type="text" placeholder="Enter search term..." name="search">
					<button type="submit">Search</button>
				</form>
			</section>

			<section>
				<h2>Now Playing</h2>
				<pre>$(mpc_post)</pre>
				<img class="cover-art" src="$(coverart)" alt="Cover Art" onerror="this.style.display='none'">
			</section>

			<section>
				<h2>Next in Queue</h2>
				<form name="next_form" method="GET">
					<p><button name="button" value="next">$(next_song)</button></p>
				</form>
			</section>
		</main>

		<aside>
			<nav>
				<h2>Menu</h2>
				<ul>
					<li><a href="queued/queued.cgi">Queued</a></li>
					<li><a href="directory/directory.cgi">Directory</a></li>
					<li><a href="playlist/playlist.cgi">Playlist</a></li>
					<li><a href="settings/settings.cgi">Settings</a></li>
				</ul>
			</nav>

			<section>
				<h3>MPD Statistics</h3>
				<p>$(mpc stats | sed "s/$/<br>/g")</p>
			</section>

			<footer>
				<h3>Links</h3>
				<p><a href="https://github.com/tekkamelon/sh-mpd">GitHub Repository</a></p>
				<p>Reference: <a href="https://github.com/ShellShoccar-jpn/misc-tools">urldecode</a>, <a href="https://github.com/andybrewer/mvp/">mvp.css</a>, <a href="https://github.com/xz/new.css">new.css</a></p>
			</footer>
		</aside>

	</body>

</html>
EOS
# ====== HTMLここまで ======

