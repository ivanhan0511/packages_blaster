import os
import time
import zipfile
import json
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, status, File, UploadFile, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse
from sqlalchemy.orm import Session

from . import settings
from .models import Base
from . import schemas, crud
from .database import SessionLocal, engine
from .logger import logger
from .simple_tools import get_package_hash

Base.metadata.create_all(bind=engine)

app = FastAPI()


# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# [TODO]: For login.
# def get_cookie_or_token(
#     websocket: WebSocket,
#     session: Optional[str] = Cookie(None),
#     token: Optional[str] = Query(None),
# ):
#     if session is None and token is None:
#         await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
#     return session or token


@app.post("/places/", response_model=schemas.Place)
def add_place(place: schemas.PlaceCreate, db: Session = Depends(get_db)):
    db_place = crud.retrieve_place_by_place_code(db=db, place_code=place.place_code)

    if db_place:
        logger.debug(f'Add place failed for existed place_code {place.place_code}.')
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"The place code {place.place_code} is already existed.")

    logger.debug(f'Add place success.')
    return crud.create_place(db=db, place=place)


@app.get('/places/', response_model=List[schemas.Place])
def get_fuzzy_places(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                     q: Optional[str] = None):
    if q:
        fuzzy_c_places = crud.retrieve_places_by_fuzzy_code(db=db, place_code=q)
        fuzzy_n_places = crud.retrieve_places_by_fuzzy_name(db=db, place_name=q)

        if not fuzzy_c_places:
            if not fuzzy_n_places:
                logger.info(f'No place matches {q}.')
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                    detail=f'No place matchs {q}.')

        # 求两次模糊查询的并集，并去重
        fuzzy_db_places = list(set(fuzzy_c_places).union(set(fuzzy_n_places)))
        logger.info(f'Get places done, with optional place code or place name {q}.')
        return fuzzy_db_places

    else:
        db_places: List[schemas.Place] = crud.retrieve_places(db=db, skip=skip, limit=limit)

        if db_places:
            logger.info('Get places done, without any query parameters.')
            return db_places

        else:
            logger.info('No place found.')
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'No place found.')


@app.get("/places/{place_id}", response_model=schemas.Place)
def get_place(place_id: int, db: Session = Depends(get_db)):
    db_place = crud.retrieve_place_by_place_id(db=db, place_id=place_id)

    if db_place is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f"Place {place_id} not found")

    logger.debug(f'Get single place {place_id}.')
    return db_place


@app.put('/places/{place_id}', response_model=schemas.Place)
def update_place(place_id: int, place: schemas.PlaceCreate, db: Session = Depends(get_db)):

    if not crud.retrieve_place_by_place_id(db, place_id=place_id):
        raise HTTPException(status_code=404, detail=f"Place {place_id} not found")

    db_places = crud.update_place(place_id=place_id, place=place, db=db)
    logger.debug(f'Place {place_id} successfully updated.')
    return db_places


@app.delete('/places/{place_id}')
def remove_place(place_id: int, db: Session = Depends(get_db)):
    # [TODO]: 将Package中的valid_places与invalid_places的相关place.id删除
    db_place = crud.retrieve_place_by_place_id(place_id=place_id, db=db)

    if not db_place:
        logger.info(f'The place {place_id} you want to remove does not exist.')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'The place {place_id} you want to remove does not exist.')

    else:
        resp = crud.delete_place(db=db, place_id=place_id)
        logger.info(f'Place {place_id} successfully deleted.')
        return JSONResponse(content=jsonable_encoder(resp))


# ======================================================================================================================


# @app.post('/upload/')
# 上传多个文件，储备内容
# @app.post("/uploadfiles/")
# async def create_upload_files(files: List[UploadFile] = File(...)):
#     return {"filenames": [file.filename for file in files]}

@app.post('/packages/', response_model=schemas.Package)
async def add_package(package_name: str, package_version: str,
                      file: UploadFile = File(...),
                      db: Session = Depends(get_db)):
    """
    用于上传Package，指定包名、版本，其余参数为将上传的文件计算而得来
    - :param package_name: 包名，约定好的、唯一的字符串，e.g.: "happymj"，没有.zip后缀
    - :param package_version: 暂时人为设定，纯粹以自然数转换为字符串，使用时转换为int比较大小
    - :param file: 包文件，暂时以'<package_name>.zip'组合
    - :param db:
    - :return:
    """

    # Checkout whether this package is existed.
    db_package = crud.retrieve_package_by_package_name(package_name=package_name, db=db)
    if db_package:
        logger.info(f'The place code {package_name} is already existed.')
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f'The place code {package_name} is already existed.')

    # [TODO]: 优化该上传前、上传中、上传中、上传效率等，参考相关文章
    start = time.time()
    try:
        data = await file.read()
        with open(f'{settings.PACKAGES_FOLDER}/{file.filename}', "wb") as f:
            f.write(data)
        logger.debug(f'Spending time for uploading: {time.time() - start}, file name: {file.filename}')
    except Exception as e:
        logger.error(f'Upload file error, detail: {e}.')
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f'Upload file error, detail: {e}.')

    # Prepare for creating package instance.
    file_path = f'{settings.PACKAGES_FOLDER}/{file.filename}'
    package_length = os.path.getsize(filename=file_path)
    logger.debug(f'length: {package_length}')
    package_hash = get_package_hash(file_path)
    logger.debug(f'hash: {package_hash}')

    # e.g.: http://127.0.0.1:21080/packages/downloads/happymj.zip
    package_down_url = f'{settings.BASE_URL}/packages/downloads/{file.filename}'

    req_dict = {'package_name': package_name,
                'package_version': package_version,
                'package_length': package_length,
                'package_hash': package_hash,
                'package_down_url': package_down_url}

    # crud.
    return crud.create_package(db=db, req_dict=req_dict)


@app.get("/packages/", response_model=List[schemas.Package])
def get_fuzzy_packages(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                       q: Optional[str] = None):
    if q:
        fuzzy_db_packages = crud.retrieve_packages_by_fuzzy_name(db=db, package_name=q)
        if fuzzy_db_packages:
            logger.info(f'Get fuzzy packages by {q}.')
            return fuzzy_db_packages
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'No packages found by {q}.')
    else:
        db_packages = crud.retrieve_packages_for_web(db, skip=skip, limit=limit)
        if db_packages:
            logger.debug(f'Get packages done.')
            return db_packages
        else:
            logger.debug(f'No package found by {skip} - {limit}')
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'No package found.')


@app.get("/packages/{package_id}", response_model=schemas.Package)
def get_package(package_id: int, db: Session = Depends(get_db)):
    db_package = crud.retrieve_package_by_package_id(package_id=package_id, db=db)
    if not db_package:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Package {package_id} not found.')
    return db_package


@app.put('/packages/{package_id}', response_model=schemas.Package, summary='Publish')
def publish_package(package_id: int, valid_places: str, invalid_places: str, db: Session = Depends(get_db)):
    db_package = crud.update_package_to_publish(db=db, package_id=package_id,
                                                valid_places=valid_places, invalid_places=invalid_places)

    return db_package


@app.delete('/packages/{package_id}')
def remove_package(package_id: int, db: Session = Depends(get_db)):
    db_package = crud.retrieve_package_by_package_id(db=db, package_id=package_id)
    if db_package:
        resp = crud.delete_package(db=db, package_id=package_id)
        logger.info(f'Remove package {package_id} done.')
        return JSONResponse(jsonable_encoder(resp))
    else:
        logger.info(f'The package {package_id} to be deleted does not exist.')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'The package {package_id} to be deleted does not exist.')


@app.get("/packages/downloads/{zip_file_name}")
async def download_package(zip_file_name: str):
    """
    An API for downloading package.
    :param zip_file_name:
    :return: The downloaded packages are always with .zip
    """
    # [TODO]: 真实数据和假数据的路径及文件名称要确认
    file_path = f'{settings.PACKAGES_FOLDER}/{zip_file_name}'
    if os.path.exists(file_path):
        logger.debug(f'The request package {zip_file_name} exists, to be downloaded.')
        return FileResponse(file_path, filename=f'{zip_file_name}')
    else:
        logger.info(f'The request package {zip_file_name} not found.')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'The request package {zip_file_name} not found.')


@app.get("/updblaster/", summary='Main API')
def resp_to_client(package_name: str, place_code: str, db: Session = Depends(get_db)):
    """
    Main API for communicating with client.
    可更新self_service, packagelist.json, <normal_package>
    - :param package_name: Package to be updated.
    - :param place_code: If this place_code is enabled to be updated.
    - :param db: DB session.
    - :return: A manual composed JSON response.
    """
    if package_name == 'packagelist':
        """
        如果是此字符串，则查询数据库的最新数据并更新`newpackagelist.json`，
        将json文件压缩成zip包，生成下载URL，返回
        """
        packagelist_version = '1'  # [TODO]: 增加新表记录packagelist的版本号
        db_packages = crud.retrieve_packages_all(db=db)
        if not db_packages:
            logger.info(f'No package found.')
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'No package found.')

        packages_list = []
        for package in db_packages:
            # [TODO]: 该字典被2次调用组装了，后续抽象出来
            data_dict = {"package_name": package.package_name,
                         "package_version": package.package_version,
                         "package_length": package.package_length,
                         "package_hash": package.package_hash,
                         "package_down_url": package.package_down_url,
                         "package_path": f'e:\\blaster\\{package_name}\\'}
            packages_list.append(data_dict)

        newpackagelist_dict = {
            "packagelist_version": packagelist_version,
            "packagelist_name": "packagelist",
            "packagelist_info_url": f"{settings.BASE_URL}/updblaster/",
            "packages_list": packages_list
        }

        json_file_path = f'{settings.PACKAGES_FOLDER}/{settings.JSON_FILE_NAME}'
        try:
            # Create the json file.
            with open(json_file_path, 'w') as f:
                f.write(json.dumps(newpackagelist_dict, indent=4))  # 注意indent=4

        except FileNotFoundError as e:
            logger.error(f'Write {json_file_path} failed.')
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f'Internal operation failed.')

        zip_file_path = f'{settings.PACKAGES_FOLDER}/{settings.ZIP_FILE_NAME}'
        try:
            # Create the zip file.
            with zipfile.ZipFile(zip_file_path, 'w') as zf:
                zf.write(json_file_path, f'{settings.JSON_FILE_NAME}')

            # Concatenate the download URL.
            package_list_down_url = f'{settings.BASE_URL}/packages/downloads/{settings.ZIP_FILE_NAME}'  #newpackagelist.zip
            package_length = os.path.getsize(zip_file_path)
            package_hash = get_package_hash(zip_file_path)
            resp_dict = {
                "package_name": f"{package_name}",
                "package_version": f"1",  # [TODO]: 新表
                "package_length": f'{package_length}',
                "package_hash": f'{package_hash}',
                "package_down_url": f'{package_list_down_url}',
                "package_path": f'./blaster/'  # This is only for packagelist.json
            }

            return JSONResponse(content=jsonable_encoder(resp_dict))

        except FileNotFoundError as e:
            logger.error(f'Write {zip_file_path} failed.')
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f'Internal operation failed.')

    else:
        """
        请求为非package_name="packagelist"
        """
        # 检查package是否可用
        db_package: schemas.Package = crud.retrieve_package_by_package_name(db, package_name=package_name)
        if not db_package:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f"Package {package_name} not found.")

        # 检查place是否可用
        # [TODO]: 黑白名单，不要记录在package属性中
        vp_str: str = db_package.valid_places  # e.g.: '1,2,3'
        valid_list = vp_str.split(',')  # e.g.: ['1', '2', '3']

        invp_str: str = db_package.invalid_places  # e.g.: '2,3'
        invalid_list = invp_str.split(',')  # e.g.: ['2', '3']
        # set去重，并取在白名单中但不在黑名单中的值
        enabled_places = list(set(valid_list).difference(set(invalid_list)))  # e.g.: ['1']

        db_place = crud.retrieve_place_by_place_code(db, place_code=place_code)
        if not db_place:
            logger.info(f'Place {place_code} not found.')
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'Place {place_code} not found.')

        if str(db_place.id) not in enabled_places:
            logger.info(f'This Place {place_code} is forbidden to update.')
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f'This place {place_code} is forbidden to update.')
        else:
            resp_dict = {
                "package_name": f"{db_package.package_name}",
                "package_version": f"{db_package.package_version}",
                "package_length": f'{db_package.package_length}',
                "package_hash": f'{db_package.package_hash}',
                "package_down_url": f'{db_package.package_down_url}',
                "package_path": f'e:\\blaster\\{package_name}\\'
            }

            return JSONResponse(content=jsonable_encoder(resp_dict))


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app=app, host='0.0.0.0', port=21080, works=1, reload=True)
