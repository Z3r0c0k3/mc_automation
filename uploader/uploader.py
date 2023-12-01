import os
import subprocess
import zipfile
from mcrcon import MCRcon
import time
import asyncio
import telegram
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# 구글 드라이브 API 접근 권한 설정
SCOPES = ['https://www.googleapis.com/auth/drive']

def authenticate_google_drive():
    creds = None
    # 이미 생성된 토큰 파일이 있는지 확인
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # 필요한 경우 로그인을 위한 인증 흐름을 실행
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # 다음 실행을 위한 토큰 저장
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)

def upload_file_to_drive(service, filename, folder_id):
    file_metadata = {
        'name': filename,
        'parents': [folder_id]
    }
    media = MediaFileUpload(filename, mimetype='application/zip')
    file = service.files().create(body=file_metadata,
                                  media_body=media,
                                  fields='id').execute()
    print(f'File ID: {file.get("id")}')

def backup_minecraft_maps():
    # 경로 설정
    server_path = 'your_server_path'
    folders_to_backup = ['desired_file_name']
    global zip_filename

    # 폴더 압축
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for folder in folders_to_backup:
            folder_path = os.path.join(server_path, folder)
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    zipf.write(os.path.join(root, file), 
                               os.path.relpath(os.path.join(root, file), 
                                               os.path.join(server_path, '..')))

# RCON 설정
RCON_HOST = "localhost"  # 서버의 주소, 로컬 환경에서 서버 구동의 경우 'localhost'
RCON_PORT = 25575        # 변경한 RCON 포트 번호
RCON_PASSWORD = "your_rcon_password"  # RCON 비밀번호

def stop_minecraft_server():
    with MCRcon(RCON_HOST, RCON_PASSWORD, RCON_PORT) as mcr:
        resp = mcr.command("stop")
        print("서버 종료 응답:", resp)

def restart_windows():
    global zip_filename
    # 로컬에서 생성된 ZIP 파일 삭제
    os.remove(zip_filename)

    # 윈도우 재시작 명령어
    subprocess.call(["shutdown", "/r", "/t", "0"])

async def send_tg_message(token, chat_id, text):
    bot = telegram.Bot(token)
    await bot.sendMessage(chat_id, text)

# 전역 변수
now = datetime.now()
backup_folder_name = now.strftime('%Y%m%d %H:%M') + '_BACKUP'
zip_filename = backup_folder_name + '.zip'
service = authenticate_google_drive()
folder_id = 'your_drive_folder_id'  # '내 드라이브/GB MAP' 폴더의 ID
TOKEN = 'your_telegram_token'
CHAT_ID = 'your_telegram_chat_id'
MESSAGE = f"[{now.strftime('%m/%d %H:%M')}] GB 서버 드라이브 자동 백업 실행 성공. 정상 업로드 확인 요망."

if __name__ == '__main__':
    print("서버를 종료합니다.")
    stop_minecraft_server()

    print("서버가 종료될 때까지 대기 중...")
    time.sleep(15)  # 서버가 완전히 종료될 때까지 충분한 시간을 주어야 합니다.

    print("백업을 시작합니다.")
    backup_minecraft_maps()

    print("업로드를 시작합니다.")
    upload_file_to_drive(service, zip_filename, folder_id)

    print("텔레그램 메시지를 송신합니다.")
    asyncio.run(send_tg_message(TOKEN, CHAT_ID, MESSAGE))

    print("윈도우를 재시작합니다.")
    time.sleep(2)
    restart_windows()
