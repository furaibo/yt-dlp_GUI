import time
import platform
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlunparse

import flet as ft
from yt_dlp import YoutubeDL


#
# 各種ヘルパー関数
#

def get_default_save_path():
    # デフォルトパスの設定
    home_path = Path.home()
    folder_name = "yt-dlp_downloads"
    folder_path = home_path.joinpath(folder_name)
    
    # OS情報に応じて保存先の設定
    pf = platform.system()
    if pf in ("Windows", "Linux"):
        folder_path = home_path.joinpath("Videos", folder_name)
    elif pf == "Darwin":
        folder_path = home_path.joinpath("Movies", folder_name)
    
    # フォルダの作成
    if not folder_path.exists():
        folder_path.mkdir(parents=True)

    return folder_path


def get_formatted_youtube_url(url: str):
    # URLの解析
    result = urlparse(url)

    # URL文字列の不要なクエリパラメータを削除する
    params = parse_qs(result.query)
    video_id = params["v"][0]
    
    # 整形後のURLを取得
    query = f"v={video_id}"
    formatted_url = urlunparse((result.scheme, result.netloc, result.path, "", query, ""))

    return formatted_url


#
# main関数
#

def main(page: ft.Page):
 
    # タイトル設定
    page.title = "yt-dlp GUI"
    
    # サイズ指定
    page.window.width = 1000
    page.window.height = 800
    page.window.min_width = 500
    page.window.min_height = 400

    # デフォルトパス
    save_dir_path = get_default_save_path()

    # yt-dlpオプション設定
    ytdlp_option = {
        "format": "best",   # 保存時の拡張子設定
    }

    #
    # イベント定義
    #

    def event_get_directory_result(e: ft.FilePickerResultEvent):
        if e.path:
            text_field_save_path.value = e.path
            text_field_save_path.update()
        else:
            print("canceled!")

    def event_click_button_select_directory():
        get_directory_dialog.get_directory_path(
            initial_directory=str(save_dir_path))

    def event_remove_input_url(e):
        target_key = e.control.data

        # 該当データテーブル行の削除
        for i, row in enumerate(data_table_url_input.rows):
            if target_key in row.data:
                data_table_url_input.rows.pop(i)
                data_table_url_input.update()

    def event_add_input_url():
        url = text_field_add_url.value

        # 整形されたURLを取得
        formatted_url = get_formatted_youtube_url(url)

        # チェック中表記を有効にする
        text_now_info_loading.visible = True
        text_now_info_loading.update()

        # ページ情報の取得とURLのチェック
        with YoutubeDL(ytdlp_option) as ydl:
            try:
                resp = ydl.extract_info(formatted_url, download=False)
            
                # データテーブルへの行追加
                row = ft.DataRow(
                    data=formatted_url,
                    cells=[
                        ft.DataCell(ft.Text(resp["title"])),
                        ft.DataCell(ft.Text(resp["webpage_url_domain"])),
                        ft.DataCell(ft.Text(resp["uploader"])),
                        ft.DataCell(ft.Text(resp["upload_date"])),
                        ft.DataCell(ft.OutlinedButton(
                            text="削除",
                            data=formatted_url,
                            on_click=lambda e: event_remove_input_url(e)))
                    ]
                )
                data_table_url_input.rows.append(row)
                data_table_url_input.update()

                # 入力テキスト消去
                text_field_add_url.value = ""
                text_field_add_url.update()

            except:
                print("Download error!")

            finally:
                text_now_info_loading.visible = False
                text_now_info_loading.update()

    def event_download_files():
        # 保存先パスの指定
        save_dir_path = text_field_save_path.value
        outtmpl_str = f"{save_dir_path}/%(title)s.%(ext)s"
        ytdlp_option["outtmpl"] = outtmpl_str

        # 保存対象の確認オプション値の再設定
        save_type = radio_group_save_type.value
        if save_type == "1":
            ytdlp_option["format"] = "best"
        elif save_type == "2":
            ytdlp_option["format"] = "bestaudio"
        elif save_type == "3":
            ytdlp_option["format"] = "bestaudio/best"

        # URLリストの取得
        url_list = []
        for row in data_table_url_input.rows:
            url_list.append(row.data)

        # プログレスバーとテキストの初期化
        progress_count = 0
        progress_limit = len(url_list)
        progress_bar_download_status.value = 0
        progress_bar_download_status.visible = True
        text_download_status.value = f"現在のダウンロード状況 ... 0/{progress_limit} 進行中"
        text_download_status.visible = True
        page.update()

        # ダウンロード処理の実行
        with YoutubeDL(ytdlp_option) as ydl:
            for url in url_list:
                ydl.extract_info(url)
                progress_count += 1
                progress_bar_download_status.value = (progress_count / progress_limit)
                text_download_status.value = f"現在のダウンロード状況 ... {progress_count}/{progress_limit} 進行中"
                page.update()

            time.sleep(1)
        
        # プログレスバーとテキストを不可視として変更
        progress_bar_download_status.visible = False
        progress_bar_download_status.update()
        text_download_status.visible = False
        text_download_status.update()

        # 入力済みURL情報のクリア
        data_table_url_input.rows.clear()
        data_table_url_input.update()


    #
    # 入力・表示制御が必要なUI群の定義
    #

    # FilePicker定義
    # Note: appendによるpage追加がないとエラー発生
    get_directory_dialog = ft.FilePicker(on_result=event_get_directory_result)
    page.overlay.append(get_directory_dialog)

    # 拡張子選択用チェックボックス
    radio_group_save_type = ft.RadioGroup(
        value="1",    # デフォルトで"動画のみ"を選択済みの状態にする
        content=ft.Row([
            ft.Radio(value="1", label="動画のみ"),
            ft.Radio(value="2", label="音源のみ"),
            ft.Radio(value="3", label="動画+音源")
        ])
    )

    # テキストフィールド定義
    text_field_save_path = ft.TextField(
        label="フォルダ",
        width=600,
        read_only=True,
        value=str(save_dir_path)
    )
    text_field_add_url = ft.TextField(
        label="ダウンロード対象URLを入力",
        width=700
    )

    # テキスト定義
    text_now_info_loading = ft.Text(
        value="URLチェック中です",
        visible=False
    )
    text_download_status = ft.Text(visible=False)

    # ボタン定義
    button_select_save_path = ft.FilledButton(
        text="選択",
        disabled=page.web,
        on_click=lambda _: event_click_button_select_directory()
    )
    button_add_url = ft.Button(
        text="追加",
        on_click=lambda _: event_add_input_url()
    )
    button_download_start = ft.CupertinoFilledButton(
        text="ダウンロード開始",
        width=800,
        on_click=lambda _: event_download_files())

    # DataTable/View定義
    data_table_url_input = ft.DataTable(
        width=850,
        divider_thickness=1,
        columns = [
            ft.DataColumn(ft.Text("タイトル")),
            ft.DataColumn(ft.Text("サイト")),
            ft.DataColumn(ft.Text("投稿者")),
            ft.DataColumn(ft.Text("投稿日時")),
            ft.DataColumn(ft.Text("削除")),
        ]
    )
    list_view_url_input = ft.ListView(
        controls=[data_table_url_input],
        expand=1, spacing=10, padding=20)

    # プログレスバー定義
    progress_bar_download_status = ft.ProgressBar(
        width=800, value=0, visible=False)

    #
    # ページ内UIレイアウト定義
    #

    row_spacer_large = ft.Row(controls=[ft.Divider(height=20)])
    row_spacer_small = ft.Row(controls=[ft.Divider(height=10)])
    row_save_path = ft.Row(
        controls=[
            ft.Text("保存パス指定"),
            text_field_save_path,
            button_select_save_path
        ]
    )
    row_file_ext = ft.Row(
        controls=[
            ft.Text("保存対象選択"),
            radio_group_save_type
        ]
    )
    row_add_url = ft.Row(
        controls=[
            ft.Text("URL:"),
            text_field_add_url,
            button_add_url,
            text_now_info_loading
        ]
    )
    row_list_view_url_input = ft.Row(
        controls=[
            ft.Container(
                content=list_view_url_input,
                height=360,
                width=900
            ),
        ],
    )
    row_button_download_start = ft.Row(
        controls=[button_download_start],
        alignment=ft.MainAxisAlignment.CENTER,
    )
    row_progress_bar_download_status = ft.Row(
        controls=[progress_bar_download_status],
        alignment=ft.MainAxisAlignment.CENTER,
    )
    row_text_download_status = ft.Row(
        controls=[text_download_status],
        alignment=ft.MainAxisAlignment.CENTER,
    )

    page.add(
        row_spacer_large,
        row_save_path,
        row_file_ext,
        row_spacer_small,
        row_add_url,
        row_list_view_url_input,
        row_spacer_small,
        row_button_download_start,
        row_progress_bar_download_status,
        row_text_download_status
    )


if __name__ == "__main__":
    ft.app(target=main)
