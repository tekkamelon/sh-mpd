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

# 楽曲パスと表示名の区切り文字
sep=$(printf '\037')

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

	stylesheet="modern.css"

fi

# mpcコマンドを使用する前に疎通確認
check_mpd_connection "../settings/shmpd.conf"

# POSTを変数に代入
cat_post=$(cat)

# クエリを変数展開で加工,デコード,変数に代入
search_str="$(echo "${QUERY_STRING#*\=}" | urldecode)"

# 再生中の楽曲
mpc_current="$(mpc current)"
# ====== 変数の設定ここまで ======


# ===== 関数の宣言 ======
mpc_post () {

	# 現在のキューの楽曲パス一覧
	queue_paths=$(mpc -f '%file%' playlist)

	# 選択済み位置(同じ曲が重複していても選択数だけ別々の位置を消す)
	claimed=""

	# POSTの各"del=パス"をデコードし,現在のキュー位置へ変換
	positions=$(printf '%s\n' "${cat_post}" | tr '&' '\n' | while IFS= read -r field ; do

		case "${field}" in

			del=*)
				song_path=$(printf '%s' "${field#del=}" | urldecode)

				# 一致する位置のうち,まだ選択済みでない先頭を1つ出力
				for song_pos in $(printf '%s\n' "${queue_paths}" | grep -n -F -x -- "${song_path}" | cut -d: -f1) ; do

					case " ${claimed} " in

						*" ${song_pos} "*) ;;

						*)
							printf '%s\n' "${song_pos}"
							claimed="${claimed} ${song_pos}"
							break
							;;

					esac

				done
				;;

		esac

	done | sort -n -u)

	# 位置が得られた場合のみ削除を実行
	if [ -n "${positions}" ] ; then

		# 位置の一覧を引数へ展開
		set --
		for song_pos in ${positions} ; do

			set -- "$@" "${song_pos}"

		done

		mpc del "$@" 2>&1 || :

	fi

	# 曲の削除の結果の表示,"cat_post"があれば真
	if [ -n "${cat_post}" ] ; then

		# 真の場合,ステータスとメッセージを表示
		mpc status 2>&1 | mpc_status2html -v mpc_current="${mpc_current}"
		echo "<p>Remove selected song!</p>"

	else

		mpc status 2>&1 | mpc_status2html -v mpc_current="${mpc_current}"

	fi

}

# キュー内の曲の検索,チェックボックス付きで表示
queued () {

	# 再生中の楽曲のパス(bin/queued_song は楽曲パスで一致させる)
	mpc_current_file="$(mpc current -f '%file%')"

	# キューされた曲をgrepで検索,パスと表示名を付与
	mpc -f "%file%${sep}[[%artist% - ]%title%]" playlist | grep -F -i "${search_str}" |

	# キュー内の楽曲をHTMLで表示,現在再生中の楽曲は"[Now Playing]"を付与
	# "queued_song"にシェル変数"current",post_nameに"del"を渡す
	queued_song -v mpc_current="${mpc_current_file}" -v post_name="del"

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
	</head>

	<body>

		<header>
			<h1>Remove Queued Song</h1>
			<p><strong>Host:</strong> ${MPD_HOST} | <strong>Port:</strong> ${MPD_PORT}</p>
		</header>

		<main>
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
				<div style="text-align: center; margin-bottom: 1rem;">
					<button onclick="window.scrollTo(0, document.body.scrollHeight);">Go to Bottom</button>
				</div>
				<form name="music" method="POST">
					<input type="submit" value="Remove Selected Song">
					<pre>$(queued)</pre>
					<input type="submit" value="Remove Selected Song">
				</form>
				<div style="text-align: center; margin-bottom: 1rem;">
					<button onclick="window.scrollTo(0, 0);">Go to Top</button>
				</div>
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
					<li><a href="/cgi-bin/schedule/schedule.cgi">Schedule</a></li>
				</ul>
			</nav>
		</aside>

	</body>

</html>
EOS
# ====== HTMLここまで ======
