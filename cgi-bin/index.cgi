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
											<button name="button" value="status">
																				<svg class="icon h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M11 6.25a.75.75 0 01.75.75v3.5a.75.75 0 01-1.5 0v-3.5a.75.75 0 01.75-.75zm.75 8.25a.75.75 0 01-1.5 0v-3.5a.75.75 0 011.5 0v3.5z M12 17.25a.75.75 0 11-1.5 0 .75.75 0 011.5 0z M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
												Status
											</button>
											<button name="button" value="volume_-100">
																				<svg class="icon h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M17.25 6.75L18.75 8.25M6.75 17.25L8.25 18.75M12 12l1.5 1.5m0 0L15 15m-3 3l3-3M9 9l2 2m0 0l2 2m-2-2l-2 2m2-2l2-2M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"/></svg>
												Mute
											</button>
											<button name="button" value="volume_-5">
																				<svg class="icon h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6.25V12m0 0v6.25M4.25 12H15.75m0 0H21M8.75 9.75l1.5 1.5L8.75 15m1.5-1.5l-1.5-1.5"/></svg>
												Vol -
											</button>
											<button name="button" value="volume_+5">
																				<svg class="icon h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6.25V12m0 0v6.25M4.25 12H15.75m0 0H21M12.75 9.75l1.5 1.5L12.75 15m1.5-1.5l-1.5-1.5"/></svg>
												Vol +
											</button>
											<button name="button" value="prev">
												<svg class="icon h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M6.27 3l6.913 5.43a2 2 0 010 2.14L6.27 21M18 3l-6.913 5.43a2 2 0 000 2.14L18 21"/></svg>
												Prev
											</button>
											<button name="button" value="toggle">
																				<svg class="icon h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-4.5 0v-10.5a2.25 2.25 0 014.5 0zm-6 9a2.25 2.25 0 01-4.5 0v-9.75a2.25 2.25 0 014.5 0v9.75z"/></svg>
												Play/Pause
											</button>
											<button name="button" value="stop">
												<svg class="icon h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z M9 9.75a1.25 1.25 0 11-2.5 0v4.5a1.25 1.25 0 112.5 0v-4.5z M13.25 9.75a1.25 1.25 0 11-2.5 0v4.5a1.25 1.25 0 112.5 0v-4.5z"/></svg>
												Stop
											</button>
											<button name="button" value="next">
												<svg class="icon h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M4.27 3l6.913 5.43a2 2 0 010 2.14L4.27 21M18 3l-6.913 5.43a2 2 0 000 2.14L18 21"/></svg>
												Next
											</button>
											<button name="button" value="repeat">
												<svg class="icon h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M5.25 8.25h15m-16.5 7.5h15a2.25 2.25 0 002.25-2.25v-6a2.25 2.25 0 00-2.25-2.25H9.75A2.25 2.25 0 007.5 6v.75M5.25 8.25L3 6m0 0l2.25-2.25M3 6l2.25 2.25M13.5 15.75V21A2.25 2.25 0 0111.25 23.25h-3A2.25 2.25 0 016 20.25V15.75"/></svg>
												Repeat
											</button>
											<button name="button" value="random">
												<svg class="icon h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M6.115 5.19a7.125 7.125 0 01-3.7 3.315 1.125 1.125 0 01-1.491-.928c-.007-.103-.005-.216.009-.324a7.125 7.125 0 0116.95-3.292 1.125 1.125 0 01-.59.942l-.04.024a7.125 7.125 0 01-3.83 2.7L6.115 5.19z M20.885 18.81a7.125 7.125 0 00-3.7-3.315 1.125 1.125 0 00-1.491.928c.007.103.005.216-.009.324a7.125 7.125 0 00-16.95 3.292 1.125 1.125 0 00.59-.942l.04-.024a7.125 7.125 0 013.83-2.7L20.885 18.81z"/></svg>
												Random
											</button>
											<button name="button" value="single">
												<svg class="icon h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 15.75a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z M4.501 20.118a7.5 7.5 0 0114.214-3.975m0 0a7.5 7.5 0 01-14.214 3.975M4.501 20.118l2.433-2.433m9.371 9.371l2.433-2.433M11.025 11.025a3 3 0 11-6 0 3 3 0 016 0z M12.975 12.975a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
												Single
											</button>
											<button name="button" value="shuffle">
												<svg class="icon h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5" stroke="currentColor" aria-hidden="true"><path stroke-linecap="round" stroke-linejoin="round" d="M6.115 5.19a7.125 7.125 0 01-3.7 3.315 1.125 1.125 0 01-1.491-.928c-.007-.103-.005-.216.009-.324a7.125 7.125 0 0116.95-3.292 1.125 1.125 0 01-.59.942l-.04.024a7.125 7.125 0 01-3.83 2.7L6.115 5.19z M20.885 18.81a7.125 7.125 0 00-3.7-3.315 1.125 1.125 0 00-1.491.928c.007.103.005.216-.009.324a7.125 7.125 0 00-16.95 3.292 1.125 1.125 0 00.59-.942l.04-.024a7.125 7.125 0 013.83-2.7L20.885 18.81z"/></svg>
												Shuffle
											</button>
											<button name="button" value="clear">
												<img src="/cgi-bin/icons/clear.svg" class="icon" alt="Clear">
												Clear
											</button>
											<button name="button" value="update">
												<img src="/cgi-bin/icons/update.svg" class="icon" alt="Update DB">
												Update DB
											</button>
											<button name="button" value="seek_-5%">
												<img src="/cgi-bin/icons/seek-back.svg" class="icon" alt="Seek -">
												Seek -
											</button>
											<button name="button" value="seek_+5%">
												<img src="/cgi-bin/icons/seek-forward.svg" class="icon" alt="Seek +">
												Seek +
											</button>
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
								<button name="button" value="next">
									<img src="/cgi-bin/icons/next.svg" class="icon" alt="Next">
									$(next_song)
								</button>
				</form>
			</section>
		</main>

		<aside>
			<nav>
				<h2>Menu</h2>
				<ul>
									<li><a href="queued/queued.cgi">
										<img src="/cgi-bin/icons/queued.svg" class="icon" alt="Queued">
										Queued
									</a></li>
									<li><a href="directory/directory.cgi">
										<img src="/cgi-bin/icons/directory.svg" class="icon" alt="Directory">
										Directory
									</a></li>
									<li><a href="playlist/playlist.cgi">
										<img src="/cgi-bin/icons/playlist.svg" class="icon" alt="Playlist">
										Playlist
									</a></li>
									<li><a href="settings/settings.cgi">
										<img src="/cgi-bin/icons/settings.svg" class="icon" alt="Settings">
										Settings
									</a></li>
				</ul>
			</nav>

			<section>
				<h3>MPD Statistics</h3>
				<pre>$(mpc stats | sed "s/$//g")</pre>
			</section>

			<footer>
				<h3>Links</h3>
				<p><a href="https://github.com/tekkamelon/sh-mpd">GitHub Repository</a></p>
				<p>Reference: <a href="https://github.com/ShellShoccar-jpn/misc-tools">urldecode</a></p>
			</footer>
		</aside>

	</body>

</html>
EOS
# ====== HTMLここまで ======

