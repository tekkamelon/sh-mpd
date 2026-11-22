#!/bin/sh

# shellcheck disable=SC1090,SC1091,SC2154

# X API v2 への投稿フォームの受付と結果ページ
# index.cgi の "Post to X" ボタン(method=POST)より呼ばれる

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

# POSTボディの読み捨て
cat > /dev/null

# URLのホスト名を取得
url_hostname="$(cgi_host)"

# 結果の記録用一時ファイル(終了時に掃除)
response_file="$(mktemp)"
error_file="$(mktemp)"

cleanup () {

	rm -f "${response_file}" "${error_file}"

}

trap cleanup EXIT
trap 'exit 1' INT TERM
# ====== 変数の設定ここまで ======


# ===== 関数の宣言 =====
# 結果ページの本文(HTML断片)を組み立てて出力へ渡す
# 引数: 結果のHTML断片
render_page () {

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
		<title>Post Result - sh-MPD:${url_hostname} -</title>

	</head>

	<body>

		<header>
			<h1>Post Result</h1>
			<p><strong>Host:</strong> ${MPD_HOST} | <strong>Port:</strong> ${MPD_PORT}</p>
		</header>

		<main>
			<section>
${1}
			</section>
		</main>

	</body>

</html>
EOS
	# ====== HTMLここまで ======

}

# HTMLへの差し込み用に&<>をエスケープ(標準入力より読み込み)
html_escape () {

	sed -e 's/&/\&amp;/g' -e 's/</\&lt;/g' -e 's/>/\&gt;/g'

}
# ===== 関数の宣言ここまで ======


# ====== 本体 ======
# フォームはmethod=POSTで受ける(外部への副作用を伴うためGETでは実行しない)
if [ "${REQUEST_METHOD:-GET}" != "POST" ] ; then

	render_page "				<p>このページはフォーム(method=POST)からのみ利用できます。</p>
				<p><a href=\"/cgi-bin/index.cgi\">ホームへ戻る</a></p>"

	exit 0

fi

# X共有が無効なら投稿しない
if [ "${x_share_enabled}" != "yes" ] ; then

	render_page "				<p>X共有は無効です(x_share_enabled)。</p>
				<p><a href=\"/cgi-bin/index.cgi\">ホームへ戻る</a></p>"

	exit 0

fi

# API資格が未設定なら投稿しない(設定画面からの直接アクセス等)
if [ -z "${x_oauth2_client_id:-}" ] || [ -z "${x_oauth2_client_secret:-}" ] ; then

	render_page "				<p>X APIの設定が未完了です(cgi-bin/settings/x_api.conf)。</p>
				<p>設定方法はREADMEを参照してください。</p>
				<p><a href=\"/cgi-bin/index.cgi\">ホームへ戻る</a></p>"

	exit 0

fi

# MPDへの疎通確認
check_mpd_connection "settings/shmpd.conf"

# 本文テンプレートは bin/x_share_text 側の既定値を使うため,設定時にのみ渡す
if [ -n "${x_share_template:-}" ] ; then

	export x_share_template

fi

# 共有本文の生成(停止中は空)
share_text="$(x_share_text)"

# 停止中は投稿を行わない
if [ -z "${share_text}" ] ; then

	render_page "				<p>再生中の曲がないため投稿しませんでした。</p>
				<p><a href=\"/cgi-bin/index.cgi\">ホームへ戻る</a></p>"

	exit 0

fi

# ハッシュタグの追記(カンマ区切りを空白区切りの#付きへ変換)
if [ -n "${x_share_hashtags}" ] ; then

	share_tags=""

	# shellcheck disable=SC2086
	for tag in $(printf '%s' "${x_share_hashtags}" | tr ',' ' ' | tr -s ' ' ' ') ; do

		case "${tag}" in

			\#*)

				share_tags="${share_tags} ${tag}"

				;;

			*)

				share_tags="${share_tags} #${tag}"

				;;

		esac

	done

	share_text="${share_text}${share_tags}"

fi

# カバー画像URLの生成(bin/coverart_url へ配信元設定を渡す)
if [ -n "${img_server_host:-}" ] && [ -n "${img_server_port:-}" ] ; then

	export img_server_host img_server_port

fi

cover_url="$(coverart_url)"

# bin/x_post は別プロセスのため資格情報をexportして渡す
export x_oauth2_client_id x_oauth2_client_secret

# 投稿の実行(カバーURLがあれば添付する)
if [ -n "${cover_url}" ] ; then

	set -- x_post -t "${share_text}" -i "${cover_url}"

else

	set -- x_post -t "${share_text}"

fi

post_status=0
"${@}" > "${response_file}" 2> "${error_file}" || post_status=1

response_body="$(cat "${response_file}")"
error_body="$(cat "${error_file}")"

# 投稿IDの抽出とHTMLエスケープ
tweet_id="$(printf '%s' "${response_body}" | sed -n 's/.*"id"[[:space:]]*:[[:space:]]*"\([^"]*\)".*/\1/p')"
response_html="$(printf '%s' "${response_body}" | html_escape)"
error_html="$(printf '%s' "${error_body}" | html_escape)"

# 成功時の結果ページ(投稿IDへのリンクとホームへ戻るリンク)
if [ "${post_status}" -eq 0 ] && [ -n "${tweet_id}" ] ; then

	result_html="				<p>投稿しました。</p>
				<p><a href=\"https://x.com/i/web/status/${tweet_id}\" target=\"_blank\" rel=\"noopener noreferrer\">Xで投稿を開く</a></p>
				<p><a href=\"/cgi-bin/index.cgi\">ホームへ戻る</a></p>"

	# カバー取得の注意など,標準エラーの出力があれば添える
	if [ -n "${error_html}" ] ; then

		result_html="${result_html}
				<p>${error_html}</p>"

	fi

	render_page "${result_html}"

	exit 0

fi

# 失敗時の結果ページ(API応答を生で表示し,原因を隠さない)
if [ "${post_status}" -eq 0 ] ; then

	# 投稿は成功したが応答からIDが取れない場合
	result_html="				<p>投稿しましたが,応答から投稿IDを取り出せませんでした。</p>"

else

	result_html="				<p>投稿に失敗しました。</p>"

fi

result_html="${result_html}
				<pre>${response_html}${error_html}</pre>
				<p>トークンの期限切れの場合は bin/x_oauth2 setup で再認可してください。</p>
				<p><a href=\"/cgi-bin/index.cgi\">ホームへ戻る</a></p>"

render_page "${result_html}"
# ====== 本体ここまで ======
