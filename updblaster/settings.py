

# Constants for updating the packagelist.json itself.
JSON_FILE_NAME = 'newpackagelist.json'
ZIP_FILE_NAME = 'newpackagelist.zip'

DEBUG = True
if DEBUG:
    # R&D ENV
    BASE_URL = 'http://testupd.zhzhiyu.com:21080'
    PACKAGES_FOLDER = '/Users/ivan'
else:
    # Formal ENV
    BASE_URL = 'https://update.zhzhiyu.com:21080'
    PACKAGES_FOLDER = '/packages'  # Folder in Aliyun ECS cloud server
