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

## 独自コマンドへPATHを通す
tmp_path="$(cd "$(dirname "${0}")/../../bin" && pwd)"
export PATH="${PATH}:${tmp_path}"

# shmpd.confの有無を確認
if [ -f ./shmpd.conf ] ; then

	# 設定ファイルを読み込み
	. ./shmpd.conf


else

	# デフォルトの環境変数を代入
	export MPD_HOST="127.0.0.1"
	export MPD_PORT="6600"

	stylesheet="stylesheet.css"

fi
# ====== 変数の設定ここまで ======


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
		<link rel="stylesheet" href="/cgi-bin/stylesheet/settings.css">
		<title>Settings - sh-MPD:$(cgi_host) -</title>
	</head>

	<body>

		<header>
			<h1>Settings</h1>
			<p><strong>Host:</strong> ${MPD_HOST} | <strong>Port:</strong> ${MPD_PORT}</p>
		</header>

		<main>
			<section>
				<h2>Server Settings</h2>
				<div class="settings-grid">
					<div>
						<h4>MPD</h4>
						<p><strong>Host:</strong> ${MPD_HOST}</p>
						<p><strong>Port:</strong> ${MPD_PORT}</p>
					</div>
					<div>
						<h4>Cover Art Server</h4>
						<p><strong>Host:</strong> ${img_server_host}</p>
						<p><strong>Port:</strong> ${img_server_port}</p>
					</div>
				</div>
				<button onclick="location.href='/cgi-bin/settings/server_setting/server_setting.cgi'">Configure Servers</button>
			</section>

			<section>
				<h2>Output Devices</h2>
				<button onclick="location.href='/cgi-bin/settings/outputs/outputs.cgi'">Select Output Device</button>
			</section>

			<section>
				<h2>Appearance</h2>
				<button onclick="location.href='/cgi-bin/settings/css_select/css_select.cgi'">Select CSS</button>
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
				</ul>
			</nav>
		</aside>

	</body>

</html>
EOS
# ====== HTMLここまで ======
