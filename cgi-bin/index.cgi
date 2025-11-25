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
		@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

		:root {
		  --bg-primary: linear-gradient(135deg, #0f0f23 0%, #1a1a2e 50%, #16213e 100%);
		  --card-bg: rgba(255, 255, 255, 0.05);
		  --card-border: rgba(255, 255, 255, 0.1);
		  --text-primary: #ffffff;
		  --text-secondary: #b0b3b8;
		  --accent: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
		  --accent-hover: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
		  --shadow: 0 8px 32px rgba(0, 0, 0, 0.37);
		  --shadow-hover: 0 12px 40px rgba(0, 0, 0, 0.5);
		}

		@media (prefers-color-scheme: light) {
		  :root {
		    --bg-primary: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
		    --card-bg: rgba(255, 255, 255, 0.8);
		    --card-border: rgba(0, 0, 0, 0.1);
		    --text-primary: #1a1a1a;
		    --text-secondary: #6b7280;
		  }
		}

		* {
		  box-sizing: border-box;
		}

		body {
		  font-family: 'Inter', sans-serif;
		  background: var(--bg-primary);
		  margin: 0;
		  padding: 1rem;
		  display: grid;
		  grid-template-areas:
		    "header"
		    "main"
		    "sidebar";
		  gap: 1.5rem;
		  min-height: 100vh;
		  color: var(--text-primary);
		}

		@media (min-width: 768px) {
		  body {
		    grid-template-columns: 3fr 1fr;
		    grid-template-areas:
		      "header header"
		      "main sidebar";
		    padding: 2rem;
		  }
		}

		header {
		  grid-area: header;
		  text-align: center;
		  background: var(--card-bg);
		  backdrop-filter: blur(10px);
		  border: 1px solid var(--card-border);
		  border-radius: 20px;
		  padding: 2rem;
		  box-shadow: var(--shadow);
		}

		header h1 {
		  background: var(--accent);
		  -webkit-background-clip: text;
		  -webkit-text-fill-color: transparent;
		  background-clip: text;
		  font-size: clamp(2rem, 5vw, 3.5rem);
		  font-weight: 700;
		  margin: 0;
		}

		header p {
		  color: var(--text-secondary);
		  font-weight: 400;
		}

		main { grid-area: main; }
		aside { grid-area: sidebar; display: flex; flex-direction: column; gap: 1rem; height: 100%; }

		section {
		  background: var(--card-bg);
		  backdrop-filter: blur(20px);
		  border: 1px solid var(--card-border);
		  border-radius: 20px;
		  padding: 1.5rem;
		  box-shadow: var(--shadow);
		  margin-bottom: 1.5rem;
		}
		
		.control-grid {
		  display: grid;
		  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
		  gap: 1rem;
		}
		
		.control-grid button {
		  display: flex;
		  align-items: center;
		  justify-content: center;
		  gap: 0.5em;
		  background: var(--card-bg);
		  backdrop-filter: blur(10px);
		  border: 1px solid var(--card-border);
		  border-radius: 16px;
		  padding: 1rem;
		  color: var(--text-primary);
		  font-family: inherit;
		  font-weight: 500;
		  cursor: pointer;
		  transition: all 0.3s ease;
		  position: relative;
		  overflow: hidden;
		}
		
		.control-grid button:hover {
		  transform: translateY(-2px);
		  box-shadow: var(--shadow-hover);
		  border-color: transparent;
		  background: var(--accent);
		}
		
		.control-grid button:active {
		  transform: translateY(0);
		}
		
		.search-form {
		  display: flex;
		  gap: 1rem;
		  align-items: center;
		}
		
		.search-form select,
		.search-form input[type="text"] {
		  background: var(--card-bg);
		  backdrop-filter: blur(10px);
		  border: 1px solid var(--card-border);
		  border-radius: 12px;
		  padding: 0.75rem 1rem;
		  color: var(--text-primary);
		  font-family: inherit;
		  flex: 1;
		}
		
		.search-form button {
		  background: var(--accent);
		  border: none;
		  border-radius: 12px;
		  padding: 0.75rem 1.5rem;
		  color: white;
		  font-weight: 600;
		  transition: all 0.3s ease;
		  white-space: nowrap;
		}
		
		.search-form button:hover {
		  background: var(--accent-hover);
		  transform: scale(1.05);
		}
		
		.cover-art {
		  max-width: 100%;
		  height: 300px;
		  object-fit: cover;
		  display: block;
		  margin: 1rem auto;
		  border-radius: 20px;
		  box-shadow: var(--shadow);
		  transition: transform 0.3s ease;
		}
		
		.cover-art:hover {
		  transform: scale(1.02);
		}
		
		aside nav ul {
		  list-style: none;
		  padding: 0;
		  margin: 0;
		}
		
		aside nav li a {
		  display: block;
		  padding: 1rem;
		  margin-bottom: 0.5rem;
		  text-decoration: none;
		  background: var(--card-bg);
		  backdrop-filter: blur(10px);
		  border: 1px solid var(--card-border);
		  border-radius: 12px;
		  text-align: center;
		  color: var(--text-primary);
		  transition: all 0.3s ease;
		  font-weight: 500;
		}
		
		aside nav li a:hover {
		  background: var(--accent);
		  color: white;
		  transform: translateX(5px);
		}
		
		.icon {
		  width: 1.2em;
		  height: 1.2em;
		  flex-shrink: 0;
		}
		
		pre {
		  background: rgba(0,0,0,0.2);
		  padding: 1rem;
		  border-radius: 12px;
		  white-space: pre-wrap;
		  font-family: 'Courier New', monospace;
		  font-size: 0.9rem;
		  overflow-x: auto;
		  backdrop-filter: blur(10px);
		}
		
		footer {
		  background: var(--card-bg);
		  backdrop-filter: blur(10px);
		  border: 1px solid var(--card-border);
		  border-radius: 20px;
		  padding: 1.5rem;
		  text-align: center;
		  margin-top: auto;
		  flex-shrink: 0;
		}
		
		@media (max-width: 768px) {
		  .search-form {
		    flex-direction: column;
		    align-items: stretch;
		  }
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
											<button name="button" value="status">
												<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 2v20M2 12h20"/></svg>
												Status
											</button>
											<button name="button" value="volume_-100">
												<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 5L6 9H2v6h4l5 4V5zM19.07 4.93a10 10 0 010 14.14M15.54 8.46a5 5 0 010 7.07"/></svg>
												Mute
											</button>
											<button name="button" value="volume_-5">
												<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 5L6 9H2v6h4l5 4V5zM19 12a3 3 0 11-6 0 3 3 0 016 0z"/></svg>
												Vol -
											</button>
											<button name="button" value="volume_+5">
												<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 5L6 9H2v6h4l5 4V5zM19.07 4.93a7 7 0 010 14.14M15.54 8.46a5 5 0 010 7.07"/></svg>
												Vol +
											</button>
											<button name="button" value="prev">
												<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 20H9V4m0 0l-7 7 7 7M9 4h10"/></svg>
												Prev
											</button>
											<button name="button" value="toggle">
												<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 3v14l12-7z"/></svg>
												Play/Pause
											</button>
											<button name="button" value="stop">
												<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M6 18L18 6M6 6l12 12"/></svg>
												Stop
											</button>
											<button name="button" value="next">
												<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 4v16l12-7z"/></svg>
												Next
											</button>
											<button name="button" value="repeat">
												<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 18a5 5 0 00-10 0M9 6a5 5 0 0110 0"/></svg>
												Repeat
											</button>
											<button name="button" value="random">
												<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 2l4 4-4 4M2 16l4 4 4-4M2 8l4-4 4 4M18 16a4 4 0 00-8 0"/></svg>
												Random
											</button>
											<button name="button" value="single">
												<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10a1 1 0 01-1 1H4a1 1 0 01-1-1v-3a1 1 0 011-1h16a1 1 0 011 1z"/></svg>
												Single
											</button>
											<button name="button" value="shuffle">
												<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M16 2l4 4-4 4M2 16l4 4 4-4M2 8l4-4 4 4"/></svg>
												Shuffle
											</button>
											<button name="button" value="clear">
												<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0h10"/></svg>
												Clear
											</button>
											<button name="button" value="update">
												<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M23 4v6h-6M1 20v-6h6M3.51 9a9 9 0 0114.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0020.49 15"/></svg>
												Update DB
											</button>
											<button name="button" value="seek_-5%">
												<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12.272 1.512a5.5 5.5 0 011.456 7.512l-8.512 5.01a5.5 5.5 0 11-1.456-7.512l8.512-5.01z"/></svg>
												Seek -
											</button>
											<button name="button" value="seek_+5%">
												<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M13.728 22.488a5.5 5.5 0 01-1.456-7.512l8.512-5.01a5.5 5.5 0 111.456 7.512l-8.512 5.01z"/></svg>
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
									<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 4v16l12-7z"/></svg>
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
										<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/></svg>
										Queued
									</a></li>
									<li><a href="directory/directory.cgi">
										<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z"/></svg>
										Directory
									</a></li>
									<li><a href="playlist/playlist.cgi">
										<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 19v-6a2 2 0 0 0-2-2H5a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2h2a2 2 0 0 0 2-2zm0 0V9a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v10m-6 0a2 2 0 0 0 2 2h.01M15 19v-6a2 2 0 0 1 2-2h2a2 2 0 0 1 2 2v6a2 2 0 0 1-2 2h-2a2 2 0 0 1-2-2z"/></svg>
										Playlist
									</a></li>
									<li><a href="settings/settings.cgi">
										<svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06 .06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06 .06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06 .06a1.65 1.65 0 0 0 1.82 .33H9a1.65 1.65 0 0 0 1 -1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 1 1 1.51 1.65 1.65 0 0 1 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06 .06a1.65 1.65 0 0 1-.33 1.82V9a1.65 1.65 0 0 1 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 1-1.51 1z"/></svg>
										Settings
									</a></li>
				</ul>
			</nav>

			<section>
				<h3>MPD Statistics</h3>
				<pre>$(mpc stats | sed "s/$/\n/g")</pre>
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

