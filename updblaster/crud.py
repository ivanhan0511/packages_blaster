from sqlalchemy.orm import Session

from . import models, schemas


# Place
def create_place(db: Session, place: schemas.PlaceCreate):
    db_place = models.Place(place_name=place.place_name, place_code=place.place_code)
    db.add(db_place)
    db.commit()
    db.refresh(db_place)

    return db_place


def get_places(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Place).offset(skip).limit(limit).all()


def get_place(db: Session, place_id: int):
    return db.query(models.Place).filter(models.Place.id == place_id).first()


def get_place_by_place_code(db: Session, place_code: str):
    return db.query(models.Place).filter(models.Place.place_code == place_code).first()


# [TODO]: Finish UPDATE
# def update_place(db: Session, place_id: int, place: models.Place):
#     return db.


# Package
def create_package(db: Session, package: schemas.PackageCreate):
    db_package = models.Package(package_name=package.package_name,
                                package_length=package.package_length,
                                package_version=package.package_version,
                                package_hash=package.package_hash,
                                package_down_url=package.package_down_url)
    db.add(db_package)
    db.commit()
    db.refresh(db_package)

    return db_package


def get_packages(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Package).offset(skip).limit(limit).all()


def get_package(db: Session, package_id: int):
    return db.query(models.Package).filter(models.Package.id == package_id).first()


def get_package_by_package_name(db: Session, package_name: str):
    return db.query(models.Package).filter(models.Package.package_name == package_name).first()


# [TODO]: Finish UPDATE
# def update_package(db: Session, package_id: int, package: models.Package):
#     return db.
