import hashlib

from .logger import logger
from . import schemas


def get_package_hash(file_path: str):
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

    return sha256.hexdigest()


# def get_packagelist_dict():

def prepare_resp_dict(package: schemas.Package):
    standard_resp_list = ["package_name",
                          "package_version",
                          "package_length",
                          "package_hash",
                          "package_down_url",
                          "package_path"]
    resp_dict = {}
    for item in standard_resp_list:
        logger.debug(f'{package.dict().items()}')
        for k, v in package.dict().items():
            if item == k:
                resp_dict[item] = v
                pass
        pass
