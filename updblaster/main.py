import os
import json
import hashlib
from typing import List

import uvicorn
from fastapi import Depends, FastAPI, HTTPException, status
from sqlalchemy.orm import Session
from starlette.responses import FileResponse

from . import crud, models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

DEBUG = True
if DEBUG:
    # R&D ENV
    BASE_URL = 'http://testupd.zhzhiyu.com:21080'
    PACKAGES_FOLDER = '/Users/ivan'
else:
    # Formal ENV
    BASE_URL = 'https://update.zhzhiyu.com:21080'
    PACKAGES_FOLDER = '/packages/'  # Folder in ESC cloud server


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/places/", response_model=schemas.Place)
def add_place(place: schemas.PlaceCreate, db: Session = Depends(get_db)):
    db_place = crud.retrieve_place_by_place_code(db=db, place_code=place.place_code)
    if db_place:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The place code {place.place_code} is already registered.")
    return crud.create_place(db=db, place=place)


@app.get("/places/", response_model=List[schemas.Place])
def get_places(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    分页查询
    [TODO]:
    :param skip:
    :param limit:
    :param db:
    :return:
    """
    db_places = crud.retrieve_places(db=db, skip=skip, limit=limit)
    return db_places


@app.get("/places/{place_id}", response_model=schemas.Place)
def get_place(place_id: int, db: Session = Depends(get_db)):
    db_place = crud.retrieve_place(db=db, place_id=place_id)
    if db_place is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Place {place_id} not found")
    return db_place


# [TODO]: 通过任意属性查询Place信息
# @app.get("/places/", response_model=schemas.Place)
# def get_place_by_place_code(place_code: str, db: Session = Depends(get_db)):
#     db_place = crud.retrieve_place_by_place_code(db=db, place_code=place_code)
#     if db_place is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
#                         detail=f"Place {place_code} not found")
#
#     return db_place


# def get_place_by_any_attribute():
#     pass


# [TODO]: to be continued...
# @app.put('/places/{place_id}')
# def update_place(place_id: int, place: models.Place, db: Session = Depends(get_db)):
#     db_place = crud.get_place(db, place_id=place_id)
#     if db_place is None:
#         raise HTTPException(status_code=404, detail=f"Place {place_id} not found")
#     return crud.


#
# [TODO]: 上传
# @app.post('/packages/', responses=schemas.Package)
# def upload_packages(package: File())


@app.get("/packages/", response_model=List[schemas.Package])
def get_packages(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_packages = crud.retrieve_packages(db, skip=skip, limit=limit)
    return db_packages


# [TODO]: Publish
@app.get("/packages/{package_id}", response_model=schemas.Package)
def get_package(package_id: int, db: Session = Depends(get_db)):
    db_package = crud.retrieve_package(package_id=package_id, db=db)
    if db_package:
        return db_package

# [TODO]: 通过任意属性查询Package信息
@app.get('/packages/', response_model=schemas.Package)
def get_package_by_package_name(package_name: str, db: Session = Depends(get_db)):
    pass


# [TODO]: Publish
@app.put("/packages/{package_name}", response_model=schemas.Package)
def choose_ext_testing_places(package_name: str, valid_places: str, invalid_places: str, db: Session = Depends(get_db)):
    pass


# Temp
@app.get("/downloads/{package_name}")
async def download_package(package_name: str):
    """
    An API for downloading package.
    :param package_name:
    :return: The downloaded packages are always with .zip
    """
    # [TODO]: Fake data.
    package_path = f'{PACKAGES_FOLDER}/{package_name}.zip'

    return FileResponse(package_path, filename=f'{package_name}.zip')


def get_package_hash(package_path: str):
    """
    Single function.
    :param package_path:
    :return: Hash value by hexdigest.
    """
    sha256 = hashlib.sha256()
    with open(package_path, 'rb') as f:
        while True:
            data = f.read(1024)
            if not data:
                break
            sha256.update(data)
    print(f'Package {package_path} hash is: {sha256.hexdigest()}')

    return sha256.hexdigest()


@app.get("/updblaster/")
def resp_to_client(package_name: str, place_code: str, db: Session = Depends(get_db)):
    """
    Main API for communicating with client.
    :param package_name: Package to be updated.
    :param place_code: If this place_code is enabled to be updated.
    :param db:
    :return: A manual composed JSON response.
    """
    db_package = crud.retrieve_package_by_package_name(db, package_name=package_name)
    if not db_package:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Package {package_name} not found.")

    # [TODO]: 黑白名单，不要记录在package属性中
    # [TODO]: 黑白名单，抽出独立的方法
    vp_str: str = db_package.valid_places  # e.g.: '1,2,3'
    valid_list = vp_str.split(',')  # e.g.: ['1', '2', '3']

    invp_str: str = db_package.invalid_places  # e.g.: '2,3'
    invalid_list = invp_str.split(',')  # e.g.: ['2', '3']
    enabled_places = list(set(valid_list).difference(set(invalid_list)))  # e.g.: ['1']

    db_place = crud.retrieve_place_by_place_code(db, place_code=place_code)
    if str(db_place.id) not in enabled_places:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f'This place {place_code} is forbidden to update.')
    else:
        package_path = f'{PACKAGES_FOLDER}/{package_name}.zip'
        package_size = os.path.getsize(package_path)  # [TODO]: 由上传功能实现并写库
        package_hash = get_package_hash(package_path)  # [TODO]: 由上传功能实现并写库
        package_down_url = f'{BASE_URL}/downloads/{package_name}'  # [TODO]: 由上传功能实现并写库

        resp_dict = {
            "package_name": f"{db_package.package_name}",
            "package_version": f"{db_package.package_version}",
            "package_length": f'{package_size}',
            "package_hash": f'{package_hash}',
            "package_down_url": f'{package_down_url}'
        }

        return json.dumps(resp_dict)
