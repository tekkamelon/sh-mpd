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

# URLのホスト名を取得
url_hostname="$(cd "$(dirname "${0}")/../bin" && ./cgi_host)"

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
		<link rel="icon" href="/cgi-bin/image/favicon.svg">
		<link rel="apple-touch-icon" href="/cgi-bin/image/favicon.svg">
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
				<form name="control_form" method="GET" action="/cgi-bin/index_process.cgi">
					<div class="control-grid">
						<button name="button" value="status">
							<img src="/cgi-bin/icons/status.svg" class="icon" alt="Status">
							Status
						</button>
						<button name="button" value="volume_-100">
							<img src="/cgi-bin/icons/mute.svg" class="icon" alt="Mute">
							Mute
						</button>
						<button name="button" value="volume_-5">
							<img src="/cgi-bin/icons/vol-down.svg" class="icon" alt="Vol -">
							Vol -
						</button>
						<button name="button" value="volume_+5">
							<img src="/cgi-bin/icons/vol-up.svg" class="icon" alt="Vol +">
							Vol +
						</button>
						<button name="button" value="prev">
							<img src="/cgi-bin/icons/prev.svg" class="icon" alt="Previous">
							Prev
						</button>
						<button name="button" value="toggle">
							<img src="/cgi-bin/icons/toggle.svg" class="icon" alt="Play/Pause">
							Play/Pause
						</button>
						<button name="button" value="stop">
							<img src="/cgi-bin/icons/stop.svg" class="icon" alt="Stop">
							Stop
						</button>
						<button name="button" value="next">
							<img src="/cgi-bin/icons/next.svg" class="icon" alt="Next">
							Next
						</button>
						<button name="button" value="repeat">
							<img src="/cgi-bin/icons/repeat.svg" class="icon" alt="Repeat">
							Repeat
						</button>
						<button name="button" value="random">
							<img src="/cgi-bin/icons/random.svg" class="icon" alt="Random">
							Random
						</button>
						<button name="button" value="single">
							<img src="/cgi-bin/icons/single.svg" class="icon" alt="Single">
							Single
						</button>
						<button name="button" value="shuffle">
							<img src="/cgi-bin/icons/shuffle.svg" class="icon" alt="Shuffle">
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
				<form name="search_form" method="POST" class="search-form" action="/cgi-bin/index_process.cgi">
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
				<pre>$(mpc status 2>&1 | sed "s/$/\n/g")</pre>
			</section>

			<section>
				<h2>Next in Queue</h2>
				<pre>$(mpc queued 2>/dev/null || echo "next song not found")</pre>
			</section>
		</main>

		<aside>
			<nav>
				<h2>Menu</h2>
				<ul>
					<li><a href="/cgi-bin/queued/queued.cgi">
						<img src="/cgi-bin/icons/queued.svg" class="icon" alt="Queued">
						Queued
					</a></li>
					<li><a href="/cgi-bin/directory/directory.cgi">
						<img src="/cgi-bin/icons/directory.svg" class="icon" alt="Directory">
						Directory
					</a></li>
					<li><a href="/cgi-bin/playlist/playlist.cgi">
						<img src="/cgi-bin/icons/playlist.svg" class="icon" alt="Playlist">
						Playlist
					</a></li>
					<li><a href="/cgi-bin/settings/settings.cgi">
						<img src="/cgi-bin/icons/settings.svg" class="icon" alt="Settings">
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
				<p>Reference: <a href="https://github.com/ShellShoccar-jpn/misc-tools">urldecode</a></p>
			</footer>
		</aside>

	</body>

</html>
EOS
