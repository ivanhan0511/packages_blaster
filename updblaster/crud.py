from typing import Optional, List

from sqlalchemy.orm import Session
from fastapi import Query

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


def retrieve_places(db: Session, skip: int = 0, limit: int = 100):
    logger.info(f'A RETRIEVE operation executed, which is `retrieve_places` by {skip} - {limit}.')

    return db.query(Place).offset(skip).limit(limit).all()


def retrieve_place(db: Session, place_id: int):
    logger.info(f'A RETRIEVE operation executed, which is `retrieve_place` by {place_id}.')

    return db.query(Place).filter(Place.id == place_id).first()


def retrieve_places_by_place_code(db: Session, place_code: str):
    logger.info(f'A RETRIEVE operation executed, which is `retrieve_places_by_place_code` by {place_code}.')

    # 不能在这里做模糊查找，否则比对place_code与place_name的id的时候就会出现错误，因为List是无序的
    # return db.query(Place).filter(Place.place_code.ilike(f'{place_code}%')).all()
    return db.query(Place).filter(Place.place_code == place_code).all()


def retrieve_places_by_place_name(db: Session, place_name: str):
    logger.info(f'A RETRIEVE operation executed, which is `retrieve_places_by_place_name` by {place_name}.')

    # 不能在这里做模糊查找，否则比对place_code与place_name的id的时候就会出现错误，因为List是无序的
    # return db.query(Place).filter(Place.place_name.like(f'{place_name}%')).all()
    return db.query(Place).filter(Place.place_name == place_name).all()


def update_place(db: Session, place_id: int, place: schemas.PlaceCreate):
    # [TODO]: 是否可以有更优雅的实现，例如(**place.dict())之类的
    db_place: schemas.PlaceCreate = db.query(Place).filter(Place.id == place_id).first()
    db_place.place_code = place.place_code
    db_place.place_name = place.place_name
    if place.description:
        db_place.description = place.description
    db.commit()
    db.refresh(db_place)
    logger.info(f'A UPDATE operation executed, which is `update_place` by {place_id}.')

    return db_place


def delete_place(db: Session, place_id: int):
    db.query(Place).filter(Place.id == place_id).delete()
    db.commit()
    logger.info(f'A DELETE operation executed, which is `delete_place` by {place_id}.')

    return {'message': f'Place {place_id} successfully deleted.'}


# ==============================================================================


# Package
def create_package(db: Session, package: schemas.PackageCreate):
    # db_package = Package(package_name=package.package_name,
    #                      package_length=package.package_length,
    #                      package_version=package.package_version,
    #                      package_hash=package.package_hash,
    #                      package_down_url=package.package_down_url)
    db_package = Package(**package.dict())
    db.add(db_package)
    db.commit()
    db.refresh(db_package)
    logger.info(f'A CREATE operation executed, which is `create_package` by {package}.')

    return db_package


def retrieve_packages(db: Session, skip: int = 0, limit: int = 100):
    logger.info(f'A RETRIEVE operation executed, which is `retrieve_packages` by {skip} - {limit}.')

    return db.query(Package).offset(skip).limit(limit).all()


def retrieve_package(db: Session, package_id: int):
    logger.info(f'A RETRIEVE operation executed, which is `retrieve_package` by {package_id}.')

    return db.query(Package).filter(Package.id == package_id).first()


def retrieve_packages_by_package_name(db: Session, package_name: str):
    logger.info(f'A RETRIEVE operation executed, which is `retrieve_packages_by_place_name` by {package_name}.')

    return db.query(Package).filter(Package.package_name == package_name).first()


# [TODO]: Finish UPDATE
# def update_package(db: Session, package_id: int, package: models.Package):
#     return db.
