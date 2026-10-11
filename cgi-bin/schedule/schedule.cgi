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

# 予約機能の既定値(変数が未定義の場合のみ代入,空文字は設定値として扱う)
schedule_enabled="${schedule_enabled-yes}"

# POSTを変数に代入
cat_post=$(cat)

# URLのホスト名を取得
url_hostname=$(cgi_host)
# ====== 変数の設定ここまで ======


# ===== 関数の宣言 ======
# POST本文より項目値を抽出しURLデコード
post_field () {

	field_name="${1}"

	# 末尾へ改行を補う(最終行が改行無しだと read が拾わない)
	printf '%s\n' "${cat_post}" | tr '&' '\n' | while IFS= read -r line ; do

		case "${line}" in

			"${field_name}="*)
				printf '%s' "${line#*=}" | urldecode
				break
				;;

		esac

	done

}

# HTML特殊文字の脱出
html_escape () {

	sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g'

}

# 予約一覧より取消ボタンの生成
cancel_forms () {

	# 予約一覧の先頭欄(数字のみ)を抜き出し一件ずつボタン化
	printf '%s' "${job_list}" | sed -n 's/^\([0-9][0-9]*\)[^0-9].*/\1/p' | while IFS= read -r line_id ; do

		if [ -n "${line_id}" ] ; then

			cat <<- FORM
			<form name="cancel_form" method="POST">
				<span>job ${line_id}</span>
				<input type="hidden" name="jobid" value="${line_id}">
				<button type="submit">Cancel</button>
			</form>
			FORM

		fi

	done

}

# POSTの処理(結果文を標準出力へ返す)
post_proc () {

	# 無効時はフォームを出さず旨だけ表示
	if [ "${schedule_enabled}" != "yes" ] ; then

		echo "予約機能は無効です (schedule_enabled=no)"
		return

	fi

	# POSTが無ければ結果文は空
	if [ -z "${cat_post}" ] ; then

		echo ""
		return

	fi

	field_mode="$(post_field mode)"
	field_minutes="$(post_field minutes)"
	field_clock="$(post_field clock)"
	field_action="$(post_field action)"
	field_jobid="$(post_field jobid)"

	# 取消は jobid の有無で判定
	if [ -n "${field_jobid}" ] ; then

		schedule_mpc cancel "${field_jobid}" 2>&1 || true

	# 相対分での予約
	elif [ "${field_mode}" = "after" ] ; then

		schedule_mpc add --after "${field_minutes}" --action "${field_action}" 2>&1 || true

	# 絶対時刻での予約
	elif [ "${field_mode}" = "at" ] ; then

		schedule_mpc add --at "${field_clock}" --action "${field_action}" 2>&1 || true

	else

		echo "invalid input!"

	fi

}
# ===== 関数の宣言ここまで ======


# ====== HTML ======
# MPDへの疎通確認
check_mpd_connection "../settings/shmpd.conf"

echo "Content-type: text/html"
echo ""

# 結果文と予約一覧の取得
result_text="$(post_proc)"
job_list=""

if [ "${schedule_enabled}" = "yes" ] ; then

	job_list="$(schedule_mpc list 2>&1)" || job_list="予約一覧の取得に失敗しました: ${job_list}"

	if [ -z "${job_list}" ] ; then

		job_list="(予約はありません)"

	fi

fi

# 無効時の本文
if [ "${schedule_enabled}" != "yes" ] ; then

	schedule_body="<p>予約機能は無効です (schedule_enabled=no)</p>"

else

	schedule_body="$(cat <<- BODY
	<section>
		<h2>Reserve</h2>
		<form name="after_form" method="POST">
			<input type="hidden" name="mode" value="after">
			<label>Minutes (1-10080):
				<input type="text" placeholder="e.g. 30" name="minutes">
			</label>
			<label>Action:
				<select name="action">
					<option value="play">Play</option>
					<option value="pause">Pause</option>
					<option value="stop">Stop</option>
				</select>
			</label>
			<button type="submit">Reserve</button>
		</form>
		<form name="at_form" method="POST">
			<input type="hidden" name="mode" value="at">
			<label>Time (HH:MM):
				<input type="text" placeholder="e.g. 21:30" name="clock">
			</label>
			<label>Action:
				<select name="action">
					<option value="play">Play</option>
					<option value="pause">Pause</option>
					<option value="stop">Stop</option>
				</select>
			</label>
			<button type="submit">Reserve</button>
		</form>
		<p>Note: 過去の時刻は翌日の同時刻扱いになります (at の仕様)。</p>
	</section>

	<section>
		<h2>Reservations</h2>
		<pre>$(printf '%s' "${job_list}" | html_escape)</pre>
		$(cancel_forms)
	</section>

	<section>
		<h2>Result</h2>
		<pre>$(printf '%s' "${result_text}" | html_escape)</pre>
	</section>
	BODY
	)"

fi

cat << EOS
<!DOCTYPE html>
<html lang="ja">

	<head>

		<meta charset="UTF-8">
		<meta name="viewport" content="width=device-width, initial-scale=1.0">
		<link rel="stylesheet" href="/cgi-bin/stylesheet/${stylesheet}">
		<link rel="stylesheet" href="/cgi-bin/stylesheet/layout.css">
		<link rel="icon" href="/cgi-bin/image/favicon.ico">
		<link rel="apple-touch-icon" href="/cgi-bin/image/favicon.ico">
		<title>Schedule - sh-MPD:${url_hostname} -</title>
	</head>

	<body>

		<header>
			<h1>Schedule</h1>
			<p><strong>Host:</strong> ${MPD_HOST} | <strong>Port:</strong> ${MPD_PORT}</p>
		</header>

		<main>
		${schedule_body}
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
