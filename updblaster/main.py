import os
import time
import json
import hashlib
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, status, File, UploadFile
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from starlette.responses import FileResponse

from updblaster.models import Place, Package, History, Base
from updblaster import schemas, crud
from updblaster.database import SessionLocal, engine
from updblaster.logger import logger

Base.metadata.create_all(bind=engine)

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
    db_place = crud.retrieve_places_by_place_code(db=db, place_code=place.place_code)
    if db_place:
        logger.debug(f'Add place failed.')
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The place code {place.place_code} is already registered.")
    logger.debug(f'Add place success.')

    return crud.create_place(db=db, place=place)


@app.get("/places/", response_model=List[schemas.Place])
def get_places(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
               place_code: Optional[str] = None,
               place_name: Optional[str] = None):
    """
    Get places. Support paginate and optional query for place_code and place_name
    :param skip:
    :param limit:
    :param db:
    :param place_code:
    :param place_name:
    :return:
    """
    if place_code and place_name:
        a_places: List[Place] = crud.retrieve_places_by_place_code(place_code=place_code, db=db)
        b_places: List[Place] = crud.retrieve_places_by_place_name(place_name=place_name, db=db)
        if a_places and b_places:
            if a_places[0].id == b_places[0].id:
                db_places = crud.retrieve_places_by_place_code(db=db, place_code=place_code)
            else:
                raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f'No place matches {place_code} and {place_name}.')
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'No place matches.')
    elif place_code:
        a_places = crud.retrieve_places_by_place_code(place_code=place_code, db=db)
        if a_places:
            db_places = a_places
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'No place matches {place_code}.')
    elif place_name:
        b_places = crud.retrieve_places_by_place_name(place_name=place_name, db=db)
        if b_places:
            db_places = b_places
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'No place matches {place_name}.')
    else:
        db_places = crud.retrieve_places(db=db, skip=skip, limit=limit)

    logger.debug('Get places, maybe with some parameters.')
    return db_places


@app.get("/places/{place_id}", response_model=schemas.Place)
def get_place(place_id: int, db: Session = Depends(get_db)):
    db_place = crud.retrieve_place(db=db, place_id=place_id)
    if db_place is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Place {place_id} not found")
    logger.debug('Get single place.')
    return db_place


# [TODO]: to be continued...
# @app.put('/places/{place_id}', response_model=schemas.Place)
# def update_place(place_id: int, place: Place, db: Session = Depends(get_db)):
#     db_place: schemas.Place = crud.retrieve_place(db, place_id=place_id)
#     if db_place is None:
#         raise HTTPException(status_code=404, detail=f"Place {place_id} not found")
#     db_place.
#     update_item_encoded = jsonable_encoder(item)
#     items[item_id] = update_item_encoded
#     return update_item_encoded


@app.delete('/places/{place_id}')
def remove_place(place_id: int, db: Session = Depends(get_db)):
    resp = crud.delete_place(db=db, place_id=place_id)
    logger.info(f'Place {place_id} successfully deleted.')
    return resp


# ==============================================================================


# @app.post('/packages/', responses=schemas.Package)
@app.post('/packages/')
async def upload_packages(package: bytes = File(...)):
    """
    创建Package的页面包含上传文件的动作，然后整体创建
    :param package:
    :return:
    """

    return {"package_length": len(package)}

# @app.post('/upload/')
# 上传多个文件，储备内容
# @app.post("/uploadfiles/")
# async def create_upload_files(files: List[UploadFile] = File(...)):
#     return {"filenames": [file.filename for file in files]}

@app.post("/file_upload")
async def file_upload(file: UploadFile = File(...)):
    start = time.time()
    try:
        res = await file.read()
        with open(file.filename, "wb") as f:
            f.write(res)
        return {"message": "success", 'time': time.time() - start, 'filename': file.filename}
    except Exception as e:
        return {"message": str(e), 'time': time.time() - start, 'filename': file.filename}

@app.get("/packages/", response_model=List[schemas.Package])
def get_packages(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    # [TODO]: 通过任意属性查询Package信息
    支持包名查询
    :param skip:
    :param limit:
    :param db:
    :return:
    """
    db_packages = crud.retrieve_packages(db, skip=skip, limit=limit)
    return db_packages


@app.get("/packages/{package_id}", response_model=schemas.Package)
def get_package(package_id: int, db: Session = Depends(get_db)):
    db_package = crud.retrieve_package(package_id=package_id, db=db)
    if not db_package:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Package {package_id} not found.')
    return db_package


# [TODO]: 发布效果
@app.put("/packages/{package_id}", response_model=schemas.Package)
def choose_ext_testing_places(package_id: int, valid_places: str, invalid_places: str, db: Session = Depends(get_db)):
    db_package: schemas.Package = crud.retrieve_package(db=db, package_id=package_id)
    if not db_package:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Package {package_id} not found.')
    db_package.valid_places = valid_places
    db_package.invalid_places = invalid_places

    return


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

    db_places = crud.retrieve_places_by_place_code(db, place_code=place_code)
    if str(db_places[0].id) not in enabled_places:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                            detail=f'This place {place_code} is forbidden to update.')
    else:
        package_path = f'{PACKAGES_FOLDER}/{package_name}.zip'
        package_size = os.path.getsize(package_path)  # [TODO]: 由上传功能实现并写库
        package_hash = get_package_hash(package_path)  # [TODO]: 由上传功能实现并写库
        package_down_url = f'{BASE_URL}/downloads/{package_name}'  # [TODO]: 由上传功能实现并写库

        # [TODO]: 使用fastapi的json...
        resp_dict = {
            "package_name": f"{db_package.package_name}",
            "package_version": f"{db_package.package_version}",
            "package_length": f'{package_size}',
            "package_hash": f'{package_hash}',
            "package_down_url": f'{package_down_url}'
        }

        return json.dumps(resp_dict)


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app=app, host='0.0.0.0', port=21080, works=1, reload=True)
