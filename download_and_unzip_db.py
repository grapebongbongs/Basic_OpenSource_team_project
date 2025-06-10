# download_and_unzip_db.py
import os
import zipfile
import urllib.request

ZIP_URL = "https://github.com/grapebongbongs/Basic_OpenSource_team_project/raw/real_main/db.zip"  # ← 실제 링크로 수정
DEST_PATH = os.path.join(os.path.dirname(__file__), 'db.sqlite3')

def download_and_unzip():
    zip_path = "db_temp.zip"
    if not os.path.exists(DEST_PATH):
        print("📥 Downloading DB zip...")
        urllib.request.urlretrieve(ZIP_URL, zip_path)

        print("📦 Unzipping...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall()

        os.remove(zip_path)
        print("✅ DB 준비 완료")