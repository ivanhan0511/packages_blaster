import hashlib


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
