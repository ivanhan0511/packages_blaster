from sqlalchemy.orm import Session

from .models import Place, Package, PackageList, History
from . import schemas
from .logger import logger


# Place
def create_place(db: Session, place: schemas.PlaceCreate):
    db_place = Place(**place.dict())
    db.add(db_place)
    db.commit()
    db.refresh(db_place)
    logger.debug(f'CREATE a place with {place.dict()}.')

    return db_place


def retrieve_places(db: Session, skip: int, limit: int):
    logger.debug(f'RETRIEVE paginated places, {skip} - {limit}.')
    return db.query(Place).offset(skip).limit(limit).all()


def retrieve_place_by_place_id(db: Session, place_id: int):
    logger.debug(f'RETRIEVE a place by `place_id` {place_id}.')
    return db.query(Place).filter(Place.id == place_id).first()


def retrieve_place_by_place_code(db: Session, place_code: str):
    logger.debug(f'RETRIEVE a place by `place_code` {place_code}.')
    return db.query(Place).filter(Place.place_code == place_code).first()


def retrieve_place_by_place_name(db: Session, place_name: str):
    logger.debug(f'RETRIEVE a place by `place_name` : {place_name}.')
    return db.query(Place).filter(Place.place_name == place_name).first()


def retrieve_places_by_fuzzy_code(db: Session, place_code: str):
    """
    模糊查找by place_code
    :param db:
    :param place_code:
    :return: Place list
    """
    logger.debug(f'RETRIEVE places by fuzzy `place_code` {place_code}.')
    return db.query(Place).filter(Place.place_code.ilike(f'{place_code}%')).all()


def retrieve_places_by_fuzzy_name(db: Session, place_name: str):
    """
    模糊查找by place_name
    :param db:
    :param place_name:
    :return: Place list
    """
    logger.debug(f'RETRIEVE places by fuzzy `place_name` {place_name}.')
    return db.query(Place).filter(Place.place_name.ilike(f'{place_name}%')).all()


def update_place(db: Session, place_id: int, place: schemas.PlaceCreate):
    # [TODO]: 是否可以有更优雅的实现，例如(**place.dict())之类的，配合PATCH
    db_place: schemas.PlaceCreate = db.query(Place).filter(Place.id == place_id).first()
    db_place.place_code = place.place_code
    db_place.place_name = place.place_name
    if place.description:
        db_place.description = place.description
    if place.package_path:
        db_place.package_path = place.package_path
    db.commit()
    db.refresh(db_place)
    logger.debug(f'UPDATE a place {place_id}.')
    return db_place


def delete_place(db: Session, place_id: int):
    # [TODO]: 后期采用伪删除
    # [TODO]: 删除返回"204 NO CONTENT"，GET查询返回"410 GONE"???
    db.query(Place).filter(Place.id == place_id).delete()
    db.commit()
    logger.debug(f'DELETE a place {place_id}.')
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
    logger.debug(f'CREATE a package with {req_dict}.')
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
    logger.debug(f'RETRIEVE paginated packages {skip} - {limit}.')
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
    logger.debug(f'RETRIEVE all packages for backend usage: {start} - {stop}.')
    return db.query(Package).slice(start, stop).all()


def retrieve_package_by_package_id(db: Session, package_id: int):
    logger.debug(f'RETRIEVE a package by `package_id` {package_id}.')
    return db.query(Package).filter(Package.id == package_id).first()


def retrieve_package_by_package_name(db: Session, package_name: str):
    logger.debug(f'RETRIEVE a package by `package_name` {package_name}.')
    return db.query(Package).filter(Package.package_name == package_name).first()


def retrieve_packages_by_fuzzy_name(db: Session, package_name: str):
    logger.debug(f'RETRIEVE packages by fuzzy `package_name` {package_name}.')
    return db.query(Package).filter(Package.package_name.ilike(f'{package_name}%')).all()


def update_package_to_publish(package_id: int,
                              package_version: str,
                              valid_places: str,
                              invalid_places: str,
                              package_run_cmd: str,
                              db: Session):
    db_package: schemas.PackageUpdate = db.query(Package).filter(Package.id == package_id).first()
    db_package.package_version = package_version
    db_package.valid_places = valid_places
    db_package.invalid_places = invalid_places
    if package_run_cmd:
        db_package.package_run_cmd = package_run_cmd
    db.commit()
    db.refresh(db_package)
    logger.debug(f'UPDATE a package {package_id}.')
    return db_package


def delete_package(db: Session, package_id: int):
    db.query(Package).filter(Package.id == package_id).delete()
    db.commit()
    logger.debug(f'DELETE a package {package_id}')
    return {'id': f'{package_id}',
            'object': 'package',
            'delete': True}


# ==============================================================================


def create_newpackagelist(db: Session, npl_dict: dict):
    db_package_list = PackageList(**npl_dict)
    db.add(db_package_list)
    db.commit()
    db.refresh(db_package_list)
    logger.debug(f'CREATE newpackagelist with {npl_dict}.')
    return db_package_list


def retrieve_newpackagelists(db: Session, skip: int, limit: int):
    logger.debug(f'RETRIEVE paginated newpackagelist {skip} - {limit}.')
    return db.query(PackageList).offset(skip).limit(limit).all()


def retrieve_newpackagelist_desc(db: Session):
    logger.debug(f'RETRIEVE a latest newpackagelist by desc')
    return db.query(PackageList).order_by(PackageList.id.desc()).first()
