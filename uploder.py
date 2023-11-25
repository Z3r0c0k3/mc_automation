import os
import datetime
import zipfile
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
    server_path = 'C:\\Users\\ZEROCOKE\\Desktop\\GB'
    folders_to_backup = ['world', 'world_nether', 'world_the_end']
    backup_folder_name = datetime.datetime.now().strftime('%Y%m%d%H%M%S') + '_BACKUP'
    zip_filename = backup_folder_name + '.zip'

    # 폴더 압축
    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for folder in folders_to_backup:
            folder_path = os.path.join(server_path, folder)
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    zipf.write(os.path.join(root, file), 
                               os.path.relpath(os.path.join(root, file), 
                                               os.path.join(server_path, '..')))

    # 구글 드라이브 업로드
    service = authenticate_google_drive()
    folder_id = 'YOUR_GOOGLE_DRIVE_FOLDER_ID'  # '내 드라이브/GB MAP' 폴더의 ID
    upload_file_to_drive(service, zip_filename, folder_id)

    # 로컬에서 생성된 ZIP 파일 삭제
    os.remove(zip_filename)

if __name__ == '__main__':
    backup_minecraft_maps()
