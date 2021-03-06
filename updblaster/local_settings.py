from pathlib import Path

# Constants for updating the packagelist.json itself.
JSON_FILE_NAME = 'newpackagelist.json'
ZIP_FILE_NAME = 'newpackagelist.zip'

DEBUG = True
if DEBUG:
    # R&D ENV
    BASE_URL = 'http://testupd.zhzhiyu.com:21080'
    PACKAGES_FOLDER = f'{Path.cwd()}/../../data'
else:
    # Formal ENV
    BASE_URL = 'http://update.zhzhiyu.com:80'
    PACKAGES_FOLDER = '/opt/packages'  # Folder in Aliyun ECS cloud server: Ubuntu 20.04, root user.
