from sqlalchemy.orm import Session

from .models import Place, Package, History
from . import schemas
from .logger import logger


# Place
def create_place(db: Session, place: schemas.PlaceCreate):
    db_place = Place(**place.dict())
    db.add(db_place)
    db.commit()
    db.refresh(db_place)
    logger.info(f'A CREATE operation executed, which is `create_place`.')

    return db_place


def retrieve_places(db: Session, skip: int, limit: int):
    logger.info(f'RETRIEVE, `retrieve_places` : {skip} - {limit}.')
    return db.query(Place).offset(skip).limit(limit).all()


def retrieve_place_by_place_id(db: Session, place_id: int):
    logger.info(f'A RETRIEVE operation executed, which is `retrieve_place` by {place_id}.')
    return db.query(Place).filter(Place.id == place_id).first()


def retrieve_place_by_place_code(db: Session, place_code: str):
    logger.info(f'RETRIEVE, `retrieve_place_by_place_code`: {place_code}.')
    return db.query(Place).filter(Place.place_code == place_code).first()


def retrieve_place_by_place_name(db: Session, place_name: str):
    logger.info(f'RETRIEVE, `retrieve_place_by_place_name` : {place_name}.')
    return db.query(Place).filter(Place.place_name == place_name).first()


def retrieve_places_by_fuzzy_code(db: Session, place_code: str):
    """
    模糊查找by place_code
    :param db:
    :param place_code:
    :return: Place list
    """
    logger.info(f'RETRIEVE: `retrieve_places_by_fuzzy_code` : {place_code}.')
    return db.query(Place).filter(Place.place_code.ilike(f'{place_code}%')).all()


def retrieve_places_by_fuzzy_name(db: Session, place_name: str):
    """
    模糊查找by place_name
    :param db:
    :param place_name:
    :return: Place list
    """
    logger.info(f'RETRIEVE: `retrieve_places_by_fuzzy_name` : {place_name}.')
    return db.query(Place).filter(Place.place_name.ilike(f'{place_name}%')).all()


def update_place(db: Session, place_id: int, place: schemas.PlaceCreate):
    # [TODO]: 是否可以有更优雅的实现，例如(**place.dict())之类的，配合PATCH
    db_place: schemas.PlaceCreate = db.query(Place).filter(Place.id == place_id).first()
    db_place.place_code = place.place_code
    db_place.place_name = place.place_name
    if place.description:
        db_place.description = place.description
    db.commit()
    db.refresh(db_place)
    logger.info(f'UPDATE: `update_place` by {place_id}.')
    return db_place


def delete_place(db: Session, place_id: int):
    # [TODO]: 后期采用伪删除
    # [TODO]: 删除返回"204 NO CONTENT"，GET查询返回"410 GONE"???
    db.query(Place).filter(Place.id == place_id).delete()
    db.commit()
    logger.info(f'A DELETE operation executed, which is `delete_place` by {place_id}.')
    return {"id": f"{place_id}",
            "object": "place",
            "deleted": True}


# ==============================================================================


# Package
def create_package(db: Session, req_dict: dict):
    db_package = Package(**req_dict)
    db.add(db_package)
    db.commit()
    db.refresh(db_package)
    logger.info(f'CREATE `create_package` : {req_dict.get("package_name", None)}.')
    return db_package


def retrieve_packages_for_web(db: Session, skip: int, limit: int):
    """
    获取packages与获取places不同，获取places比较简单，只设置偏移及分页limit即可。
    而获取packages涉及到web分页获取，或后台获取全部来生成newpackagelist.json
    所以略有不同
    :param db:
    :param skip:
    :param limit:
    :return:
    """
    # if skip and
    # db.query(Package).slice()
    logger.info(f'RETRIEVE, `retrieve_packages_for_web` : {skip} - {limit}.')
    return db.query(Package).offset(skip).limit(limit).all()


def retrieve_packages_all(db: Session, start: int = None, stop: int = None):
    """
    用于后台获取全部package list
    :param db:
    :param start:
    :param stop:
    :return:
    """
    # if skip and
    # db.query(Package).slice()
    logger.info(f'RETRIEVE, `retrieve_packages_all` : {start} - {stop}.')
    return db.query(Package).slice(start, stop).all()


def retrieve_package_by_package_id(db: Session, package_id: int):
    logger.info(f'RETRIEVE: `retrieve_package_by_package_id` : {package_id}.')
    return db.query(Package).filter(Package.id == package_id).first()


def retrieve_package_by_package_name(db: Session, package_name: str):
    logger.info(f'RETRIEVE, `retrieve_packages_by_place_name` : {package_name}.')
    return db.query(Package).filter(Package.package_name == package_name).first()


def retrieve_packages_by_fuzzy_name(db: Session, package_name: str):
    logger.info(f'RETRIEVE, `retrieve_packages_by_fuzzy_name` : {package_name}.')
    return db.query(Package).filter(Package.package_name.ilike(f'{package_name}%')).all()


def update_package_to_publish(db: Session, package_id: int, valid_places: str, invalid_places: str):
    """
    Used for publish. Input valid places to enable, and input invalid places to disable.
    :param db:
    :param package_id:
    :param valid_places:
    :param invalid_places:
    :return:
    """
    db_package: schemas.PackageUpdate = db.query(Package).filter(Package.id == package_id).first()
    db_package.valid_places = valid_places
    db_package.invalid_places = invalid_places
    db.commit()
    db.refresh(db_package)
    logger.info(f'UPDATE, `update_package` : {package_id}.')
    return db_package


def delete_package(db: Session, package_id: int):
    db.query(Package).filter(Package.id == package_id).delete()
    db.commit()
    logger.info(f'DELETE, `delete_package`: {package_id}')
    return {'id': f'{package_id}',
            'object': 'package',
            'delete': True}

