#!/bin/sh

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
# ====== 変数の設定ここまで ======


# ===== 関数の宣言 ======
# ヒアドキュメントで設定ファイルの変数を出力
heredocs () {

	cat <<- EOF
	export MPD_HOST="${MPD_HOST}"
	export MPD_PORT="${MPD_PORT}"
	img_server_host="${img_server_host}"
	img_server_port="${img_server_port}"
	stylesheet="${stylesheet}"
	EOF

}

# POSTの文字列に応じて処理を分岐
post_proc () {

	# POSTを変数に代入
	cat_post=$(cat)

	# サーバーの種類及びホストかポートを抽出
	post_key="${cat_post#*\=}"
	post_key="${post_key%%&*}"

	# ホスト名およびポート番号を抽出
	post_args="${cat_post#*\&*\=}"

	# "post_key"が"mpd_host"かつmpdと疎通確認できれば真,そうでなければ偽
	if [ "${post_key}" = "mpd_host" ] && mpc -q --host="${post_args}" ; then

		# 真の場合はPOSTを環境変数に代入
		export MPD_HOST="${post_args}"

		# 変数の一覧を出力,設定ファイルへリダイレクト
 		heredocs >| ../shmpd.conf

		echo "changed MPD host:${MPD_HOST}<br>"

		mpc status | mpc_status2html

	# "post_key"が"mpd_port"かつmpdと疎通確認できれば真,そうでなければ偽
	elif [ "${post_key}" = "mpd_port" ] && mpc -q --port="${post_args}" ; then

		# 真の場合はPOSTを環境変数に代入
		export MPD_PORT="${post_args}"

		# 変数の一覧を出力,設定ファイルへリダイレクト
 		heredocs >| ../shmpd.conf

		echo "changed MPD port:${MPD_PORT}<br>"
	
		mpc status | mpc_status2html

	# "post_key"が"img_server_host"であれば真,それ以外で偽
	elif [ "${post_key}" = "img_server_host" ] ; then

		# 真の場合はPOSTを環境変数に代入
		img_server_host="${post_args}"

		# 変数の一覧を出力,設定ファイルへリダイレクト
 		heredocs >| ../shmpd.conf

		echo "changed coverart server host:${img_server_host}<br>"

	# "post_key"が"img_server_port"かつPOSTが1以上かつ65535以下であれば真,それ以外で偽
	elif [ "${post_key}" = "img_server_port" ] && [ "${post_args}" -ge 1 ] && [ "${post_args}" -le 65535 ] ; then

		# 真の場合はPOSTを環境変数に代入
		img_server_port="${post_args}"

		# 変数の一覧を出力,設定ファイルへリダイレクト
 		heredocs >| ../shmpd.conf

		echo "changed coverart server port:${img_server_port}<br>"

	# 偽の場合はPOSTがあれば真
	elif [ -n "${cat_post}" ] ; then

		# 真の場合はメッセージを表示
		echo "invalid input!"
		
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
		<link rel="icon" href="/cgi-bin/image/favicon.svg">
		<title>Server Settings - sh-MPD:$(cgi_host) -</title>
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

			.settings-grid {
				display: grid;
				grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
				gap: 1rem;
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
			<h1>Server Settings</h1>
		</header>

		<main>
			<section>
				<h2>Current Settings</h2>
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
			</section>

			<section>
				<h2>Update Settings</h2>
				<form name="setting" method="POST" class="form-grid">
					<label for="args">Item:</label>
					<select name="args" id="args">
						<option value="mpd_host">MPD Host</option>
						<option value="mpd_port">MPD Port</option>
						<option value="img_server_host">Cover Art Server Host</option>
						<option value="img_server_port">Cover Art Server Port</option>
					</select>
					<label for="post_key">Value:</label>
					<input type="text" placeholder="Enter new value" name="post_key" id="post_key">
					<button type="submit">Update</button>
				</form>
			</section>

			<section>
				<h2>Result</h2>
				<pre>$(post_proc)</pre>
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
