#!/bin/sh

# shellcheck disable=SC1090,SC1091,SC2154

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

	stylesheet="modern.css"

fi

# X API設定ファイルの読み込み(環境変数 x_api_conf で差し替え可能)
x_api_conf="${x_api_conf:-settings/x_api.conf}"

if [ -f "${x_api_conf}" ] ; then

	. "${x_api_conf}"

fi

# X共有設定のデフォルト値(変数が未定義の場合のみ代入,空文字は設定値として扱う)
x_share_enabled="${x_share_enabled-yes}"
x_share_hashtags="${x_share_hashtags-NowPlaying}"

# API投稿の可否(client_idとclient_secretが揃っていれば利用可能)
x_api_ready="no"

if [ -n "${x_oauth2_client_id:-}" ] && [ -n "${x_oauth2_client_secret:-}" ] ; then

	x_api_ready="yes"

fi

# 本文テンプレートは bin/x_share_text 側の既定値を使うため,設定時にのみ渡す
if [ -n "${x_share_template:-}" ] ; then

	export x_share_template

fi

# bin/coverart_url は別プロセスのため配信元設定をexportして渡す
if [ -n "${img_server_host:-}" ] && [ -n "${img_server_port:-}" ] ; then

	export img_server_host img_server_port

fi

# POSTボディの読み捨て
cat > /dev/null

# クエリを変数展開し代入
query_check="${QUERY_STRING#*\=}"

# URLのホスト名を取得
url_hostname="$(cgi_host)"
# ====== 変数の設定ここまで ======


# ===== 関数の宣言 ======
mpc_post () {

	# クエリ値を加工
	echo "${query_check}" |

	sed -e "s/_\-/ \-/g" -e "s/_\%2B/ \+/g" -e "s/\%25/\%/g" |

	# mpcのエラー出力ごと渡す
	xargs mpc 2>&1 |

	mpc_status2html -v url_hostname="${url_hostname}"

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
# MPDへの疎通確認
check_mpd_connection "settings/shmpd.conf"

echo "Content-type: text/html"
echo ""

# X共有本文の生成(停止中は空)
share_text="$(x_share_text)"

# カバーアートURLの生成(停止中,配信元未設定時は空)
cover_url="$(coverart_url)"

# X共有部分のHTML組み立て(停止中,無効時は空)
share_link=""

if [ "${x_share_enabled}" = "yes" ] && [ -n "${share_text}" ] ; then

	if [ "${x_api_ready}" = "yes" ] ; then

		# API設定済み: x_post.cgi へのフォームボタン(投稿はトークンのアカウントから行う)
		share_link="<form name=\"x_post_form\" method=\"POST\" action=\"x_post.cgi\"><p><button name=\"button\" value=\"post\"><span class=\"icon\">&#x1f4e4;&#xfe0e;</span> Post to X</button></p></form>"

	else

		# 未設定: 従来のIntentリンク
		share_intent_url="https://twitter.com/intent/tweet?text=$(printf '%s' "${share_text}" | urlencode)"

		# ハッシュタグの付与
		if [ -n "${x_share_hashtags}" ] ; then

			share_intent_url="${share_intent_url}&hashtags=$(printf '%s' "${x_share_hashtags}" | urlencode)"

		fi

		# HTML属性用に"&"をエスケープ
		share_intent_url_html="$(printf '%s' "${share_intent_url}" | sed -e 's/&/\&amp;/g')"

		share_link="<p><a href=\"${share_intent_url_html}\" target=\"_blank\" rel=\"noopener noreferrer\"><span class=\"icon\">&#x1f4e4;&#xfe0e;</span> Share on X</a></p>"

	fi

fi

cat << EOS
<!DOCTYPE html>
<html lang="ja">

	<head>

		<meta charset="UTF-8">
		<meta name="viewport" content="width=device-width, initial-scale=1.0">
		<link rel="stylesheet" href="/cgi-bin/stylesheet/${stylesheet}">
		<link rel="icon" href="${cover_url}">
		<link rel="apple-touch-icon" href="${cover_url}">
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
							<span class="icon">📊&#xfe0e;</span>
							Status
						</button>
						<button name="button" value="volume_-100">
							<span class="icon">🔇&#xfe0e;</span>
							Mute
						</button>
						<button name="button" value="volume_-5">
							<span class="icon">🔉&#xfe0e;</span>
							Vol -
						</button>
						<button name="button" value="volume_+5">
							<span class="icon">🔊&#xfe0e;</span>
							Vol +
						</button>
						<button name="button" value="prev">
							<span class="icon">⏮️&#xfe0e;</span>
							Prev
						</button>
						<button name="button" value="toggle">
							<span class="icon">⏯️&#xfe0e;</span>
							Play/Pause
						</button>
						<button name="button" value="stop">
							<span class="icon">⏹️&#xfe0e;</span>
							Stop
						</button>
						<button name="button" value="next">
							<span class="icon">⏭️&#xfe0e;</span>
							Next
						</button>
						<button name="button" value="repeat">
							<span class="icon">🔁&#xfe0e;</span>
							Repeat
						</button>
						<button name="button" value="random">
							<span class="icon">🎲&#xfe0e;</span>
							Random
						</button>
						<button name="button" value="single">
							<span class="icon">&#xfe0e;1️⃣</span>
							Single
						</button>
						<button name="button" value="shuffle">
							<span class="icon">🔀&#xfe0e;</span>
							Shuffle
						</button>
						<button name="button" value="clear">
							<span class="icon">🗑️&#xfe0e;</span>
							Clear
						</button>
						<button name="button" value="update">
							<span class="icon">🔄&#xfe0e;</span>
							Update DB
						</button>
						<button name="button" value="seek_-5%">
							<span class="icon">⏪&#xfe0e;</span>
							Seek -
						</button>
						<button name="button" value="seek_+5%">
							<span class="icon">⏩&#xfe0e;</span>
							Seek +
						</button>
					</div>
				</form>
			</section>

			<section>
				<h2>Now Playing</h2>
				<pre>$(mpc_post)</pre>
${share_link}
				<img class="cover-art" src="${cover_url}" alt="Cover Art" onerror="this.style.display='none'">
			</section>

			<section>
				<h2>Next in Queue</h2>
				<form name="next_form" method="GET">
								<button name="button" value="next">
									<span class="icon">⏭️&#xfe0e;</span>
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
										<span class="icon">📋&#xfe0e;</span>
										Queued
									</a></li>
									<li><a href="directory/directory.cgi">
										<span class="icon">📁&#xfe0e;</span>
										Directory
									</a></li>
									<li><a href="playlist/playlist.cgi">
										<span class="icon">📝&#xfe0e;</span>
										Playlist
									</a></li>
									<li><a href="settings/settings.cgi">
										<span class="icon">⚙️&#xfe0e;</span>
										Settings
									</a></li>
									<li><a href="schedule/schedule.cgi">
										<span class="icon">⏰&#xfe0e;</span>
										Schedule
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
# ====== HTMLここまで ======

