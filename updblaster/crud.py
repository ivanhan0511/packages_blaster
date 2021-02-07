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
    logger.debug(f'CREATE.')

    return db_place


def retrieve_places(db: Session, skip: int, limit: int):
    logger.info(f'RETRIEVE, {skip} - {limit}.')
    return db.query(Place).offset(skip).limit(limit).all()


def retrieve_place_by_place_id(db: Session, place_id: int):
    logger.info(f'RETRIEVE, {place_id}.')
    return db.query(Place).filter(Place.id == place_id).first()


def retrieve_place_by_place_code(db: Session, place_code: str):
    logger.info(f'RETRIEVE, {place_code}.')
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
    logger.info(f'RETRIEVE, {place_code}.')
    return db.query(Place).filter(Place.place_code.ilike(f'{place_code}%')).all()


def retrieve_places_by_fuzzy_name(db: Session, place_name: str):
    """
    模糊查找by place_name
    :param db:
    :param place_name:
    :return: Place list
    """
    logger.info(f'RETRIEVE, {place_name}.')
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
    logger.info(f'UPDATE, {place_id}.')
    return db_place


def delete_place(db: Session, place_id: int):
    # [TODO]: 后期采用伪删除
    # [TODO]: 删除返回"204 NO CONTENT"，GET查询返回"410 GONE"???
    db.query(Place).filter(Place.id == place_id).delete()
    db.commit()
    logger.info(f'DELETE, {place_id}.')
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
    logger.info(f'CREATE, {req_dict}')
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
    logger.info(f'RETRIEVE, {skip} - {limit}.')
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
    logger.info(f'RETRIEVE, {start} - {stop}.')
    return db.query(Package).slice(start, stop).all()


def retrieve_package_by_package_id(db: Session, package_id: int):
    logger.info(f'RETRIEVE, {package_id}.')
    return db.query(Package).filter(Package.id == package_id).first()


def retrieve_package_by_package_name(db: Session, package_name: str):
    logger.info(f'RETRIEVE, {package_name}.')
    return db.query(Package).filter(Package.package_name == package_name).first()


def retrieve_packages_by_fuzzy_name(db: Session, package_name: str):
    logger.info(f'RETRIEVE, {package_name}.')
    return db.query(Package).filter(Package.package_name.ilike(f'{package_name}%')).all()


def update_package_to_publish(db: Session, package_id: int, package_version: str,
                              valid_places: str, invalid_places: str, package_run_cmd: str):
    db_package: schemas.PackageUpdate = db.query(Package).filter(Package.id == package_id).first()
    db_package.package_version = package_version
    db_package.valid_places = valid_places
    db_package.invalid_places = invalid_places
    if package_run_cmd:
        db_package.package_run_cmd = package_run_cmd
    db.commit()
    db.refresh(db_package)
    logger.info(f'UPDATE, {package_id}.')
    return db_package


def delete_package(db: Session, package_id: int):
    db.query(Package).filter(Package.id == package_id).delete()
    db.commit()
    logger.info(f'DELETE, {package_id}')
    return {'id': f'{package_id}',
            'object': 'package',
            'delete': True}


# ==============================================================================


def create_newpackagelist(db: Session, npl_dict: dict):
    db_package_list = PackageList(**npl_dict)
    db.add(db_package_list)
    db.commit()
    db.refresh(db_package_list)
    logger.info(f'CREATE newpackagelist, {npl_dict}.')
    return db_package_list


def retrieve_newpackagelists(db: Session, skip: int, limit: int):
    logger.info(f'RETRIEVE, {skip} - {limit}.')
    return db.query(PackageList).offset(skip).limit(limit).all()


def retrieve_newpackagelist_desc(db: Session):
    logger.info(f'RETRIEVE, desc')
    return db.query(PackageList).order_by(PackageList.id.desc()).first()
