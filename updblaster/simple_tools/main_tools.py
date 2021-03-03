from updblaster import schemas
from updblaster.logger import logger
from updblaster import local_settings

import hashlib
import json
import os
import zipfile
from typing import Optional, List


def get_package_hash(file_path: str) -> str:
    """
    :param file_path:
    :return: Hash value by hexdigest.
    """
    sha256 = hashlib.sha256()
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(1024)
            if not data:
                break
            sha256.update(data)

    # returned a string.
    return sha256.hexdigest()


def check_update_enabled(package: schemas.Package, place: schemas.Place) -> bool:
    """
    Check out whether this package could be updated to the place.
    :param package:
    :param place:
    :return: Boolean
    """
    vp_str: str = package.valid_places  # e.g.: '1,2,3'
    valid_list = vp_str.split(',')  # e.g.: ['1', '2', '3']

    invp_str: str = package.invalid_places  # e.g.: '2,3'
    # package.invalid_places是可选参数，数据库中是可以为NULL的
    if not invp_str:
        logger.debug(f'Invalid places are: {invp_str}')
        invalid_list = []  # e.g.: ['2', '3'] or None
    else:
        invalid_list = invp_str.split(',')  # e.g.: ['2', '3']

    # set去重，并取在白名单中但不在黑名单中的值
    enabled_places = list(set(valid_list).difference(set(invalid_list)))  # e.g.: ['1']
    logger.debug(f'Enabled places are: {enabled_places}.')

    if str(place.id) in enabled_places:
        return True

    else:
        return False


def assemble_package_dict(pname: str,
                          pversion: str,
                          plength: str,
                          phash: str,
                          pdownurl: str,
                          pcmd: str,
                          pdel: str,
                          ppath: Optional[str] = None, ) -> dict:

    if ppath:
        resp_dict = {"package_name": pname,
                     "package_version": pversion,
                     "package_length": plength,
                     "package_hash": phash,
                     "package_down_url": pdownurl,
                     "package_path": ppath,
                     "package_run_cmd": pcmd,
                     "package_del_cmd": pdel}

        return resp_dict

    else:
        resp_dict = {"package_name": pname,
                     "package_version": pversion,
                     "package_length": plength,
                     "package_hash": phash,
                     "package_down_url": pdownurl,
                     "package_run_cmd": pcmd,
                     "package_del_cmd": pdel}

        return resp_dict


def assemble_newpackagelist_dict(newpackagelist: schemas.PackagesList,
                                 packages: List[schemas.Package],
                                 place: schemas.Place) -> dict:
    data_list = []
    for package in packages:
        # 嵌套循环获取各个package的数据
        # data_dict = assemble_resp_dict(package=package, place=place)
        data_dict = assemble_package_dict(pname=package.package_name,
                                          pversion=package.package_version,
                                          plength=package.package_length,
                                          phash=package.package_hash,
                                          pdownurl=package.package_down_url,
                                          ppath=f'{place.package_path}{package.package_name}\\',
                                          pcmd=package.package_run_cmd,
                                          pdel=package.package_del_cmd)

        data_list.append(data_dict)

    newpackagelist_dict = {"packagelist_version": newpackagelist.packagelist_version,
                           "packagelist_name": newpackagelist.packagelist_name,
                           "packagelist_info_url": f"{local_settings.BASE_URL}/updblaster/",
                           "packages_list": data_list}

    logger.info(f'Packagelist json dict has been assembled.')
    return newpackagelist_dict


def generate_zipped_json_file_then_resp(newpackagelist_dict: dict):
    json_file_path = f'{local_settings.PACKAGES_FOLDER}/{local_settings.JSON_FILE_NAME}'
    try:
        # Create the json file.
        with open(json_file_path, 'w') as f:
            f.write(json.dumps(newpackagelist_dict, indent=4))  # 注意indent=4

    except IOError as e:
        logger.error(f'Write {json_file_path} failed. Error message: {e}')
        return None

    zip_file_path = f'{local_settings.PACKAGES_FOLDER}/{local_settings.ZIP_FILE_NAME}'
    try:
        # Create the zip file.
        with zipfile.ZipFile(zip_file_path, 'w') as zf:
            zf.write(json_file_path, f'{local_settings.JSON_FILE_NAME}')

    except IOError as e:
        logger.error(f'Write {zip_file_path} failed. Error message: {e}')
        return None

    # Assemble the special newpackagelist_dict
    # 以下2行代码不涉及性能问题，因为只计算newpackagelist.zip文件的size和hash，文件很小，所以几乎无性能问题
    packagelist_length = os.path.getsize(zip_file_path)  # returned a integer.
    packagelist_hash = get_package_hash(zip_file_path)  # returned a string.

    packagelist_down_url = f'{local_settings.BASE_URL}/packages/downloads/{local_settings.ZIP_FILE_NAME}'

    # resp_dict = {"package_name": newpackagelist_dict.get("packagelist_name"),
    #              "package_version": newpackagelist_dict.get("packagelist_version"),
    #              "package_length": packagelist_length,
    #              "package_hash": packagelist_hash,
    #              "package_down_url": packagelist_down_url,
    #              "package_path": f'./blaster/',  # This is only for packagelist.json
    #              "package_run_cmd": ''}  # This is only for packagelist.json
    resp_dict = assemble_package_dict(pname=newpackagelist_dict.get('packagelist_name'),
                                      pversion=newpackagelist_dict.get('packagelist_version'),
                                      plength=str(packagelist_length),
                                      phash=packagelist_hash,
                                      pdownurl=packagelist_down_url,
                                      ppath=f'./blaster/',
                                      pcmd='',
                                      pdel='')

    return resp_dict

