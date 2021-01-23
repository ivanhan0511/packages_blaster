import os
import json
import hashlib
from typing import List

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from starlette.responses import FileResponse

from . import crud, models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# R&D ENV
BASE_URL = 'http://127.0.0.1:21080'
PACKAGES_FOLDER = '/Users/ivan/'

# Formal ENV
# BASE_URL = 'http://update.zhzhiyu.com:21080'
# PACKAGES_FOLDER = '/packages/'


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/places/", response_model=schemas.Place)
def create_place(place: schemas.PlaceCreate, db: Session = Depends(get_db)):
    db_place = crud.get_place_by_place_code(db, place_code=place.place_code)
    if db_place:
        # [TODO]: status_code有没有常量?
        raise HTTPException(status_code=400, detail=f"The place code {place.place_code} is already registered.")
    return crud.create_place(db=db, place=place)


# [TODO]: 0-100是分页还是全部?
@app.get("/places/", response_model=List[schemas.Place])
def retrieve_places(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_places = crud.get_places(db, skip=skip, limit=limit)
    return db_places


@app.get("/places/{place_id}", response_model=schemas.Place)
def retrieve_place(place_id: int, db: Session = Depends(get_db)):
    db_place = crud.get_place(db, place_id=place_id)
    if db_place is None:
        raise HTTPException(status_code=404, detail=f"Place {place_id} not found")
    return db_place


# @app.put('/places/{place_id}')
# def update_place(place_id: int, place: models.Place, db: Session = Depends(get_db)):
#     db_place = crud.get_place(db, place_id=place_id)
#     if db_place is None:
#         raise HTTPException(status_code=404, detail=f"Place {place_id} not found")
#     return crud.


#
# [TODO]: 上传
#


@app.get("/packages/", response_model=List[schemas.Package])
def retrieve_packages(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    db_packages = crud.get_places(db, skip=skip, limit=limit)
    return db_packages


@app.get('/downloads/{package_name}')
async def download_package(package_name: str):
    """
    An API for downloading package.
    :param package_name:
    :return: The downloaded packages are always with .zip
    """
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
    # print(f'Package {package_name} hash is: {sha256.hexdigest()}')
    print(f'Package aa.txt hash is: {sha256.hexdigest()}.')

    return sha256.hexdigest()


@app.get('/updblaster')
def resp_to_client(package_name: str, place_code: str, db: Session = Depends(get_db)):
    """
    Main API for communicating with client.
    :param package_name: Package to be updated.
    :param place_code: If this place_code is enabled to be updated.
    :param db:
    :return: A manual composed JSON response.
    """
    db_package = crud.get_package_by_package_name(db, package_name=package_name)
    if db_package:
        raise HTTPException(status_code=400, detail=f"Package {package_name} not found.")

    # [TODO]: 黑白名单，不要记录在package属性中
    # [TODO]: 黑白名单，抽出独立的方法
    # valid: str = db_package.valid_places
    valid: str = '1,2,3'
    valid_list = valid.split(',')

    # invalid: str = db_package.invalid_places
    invalid: str = '2,3'
    invalid_list = invalid.split(',')
    # [TODO]: Fake data, only update place `1`.
    enabled_places = list(set(valid_list).difference(set(invalid_list)))

    place_id = crud.get_place_by_place_code(db, place_code=place_code)
    if place_id not in enabled_places:
        raise HTTPException(status_code=400, detail=f'This place {place_code} is forbided to update.')
    else:
        # [TODO]: Fake data, MUST be 'happymj' for testing.
        package_path = f'{PACKAGES_FOLDER}/{package_name}.zip'
        package_size = os.path.getsize(package_path)  # [TODO]: 由上传功能实现并写库
        package_hash = get_package_hash(package_path)  # [TODO]: 由上传功能实现并写库
        package_down_url = f'{BASE_URL}/downloads/{package_name}'  # [TODO]: 由上传功能实现并写库
        resp_dict = {
            "package_name": f"{db_package.package_name}",
            "package_version": f"{db_package.package_version}",
            "package_length": f"{package_size}",
            "package_hash": f'{package_hash}',
            "package_down_url": f'{package_down_url}'
        }

        return json.dumps(resp_dict)
