import os
import time
import json
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, status, File, UploadFile, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from updblaster import local_settings
from updblaster.database import SessionLocal, engine
from updblaster.models import Base
from updblaster import schemas, crud
from updblaster.logger import logger
from updblaster.simple_tools import main_tools

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.mount('/static', StaticFiles(directory=f'{local_settings.PACKAGES_FOLDER}/static'), name='static')


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

    logger.debug(f'Add a new place successfully.')
    return crud.create_place(db=db, place=place)


@app.get('/places/', response_model=List[schemas.Place])
def get_fuzzy_places(skip: int = 0, limit: int = 100, db: Session = Depends(get_db),
                     q: Optional[str] = None):
    if q:
        fuzzy_c_places = crud.retrieve_places_by_fuzzy_code(db=db, place_code=q)
        fuzzy_n_places = crud.retrieve_places_by_fuzzy_name(db=db, place_name=q)

        if not fuzzy_c_places and not fuzzy_n_places:
            # [TODO]: WTF logic
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
async def add_package(package_name: str = Query(..., min_length=2, max_length=32),
                      package_version: str = Query(..., min_length=1, max_length=16),
                      package_run_cmd: Optional[str] = Query(None, min_length=2, max_length=512),
                      package_del_cmd: Optional[str] = Query(None, min_length=2, max_length=512),
                      package_path: str = Query(..., min_length=5),
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
    if crud.retrieve_package_by_package_name(package_name=package_name, db=db):
        logger.info(f'The place code {package_name} is already existed.')
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f'The place code {package_name} is already existed.')

    # [TODO]: 优化该上传前、上传中、上传中、上传效率等，参考相关文章
    start = time.time()
    file_path = f'{local_settings.PACKAGES_FOLDER}/{file.filename}'
    try:
        # 以下1行代码可能涉及性能问题，因为此处为web端上传的package文件，可能是以GB为单位的包
        data = await file.read()
        with open(file_path, "wb") as f:
            f.write(data)
        logger.debug(f'Spending time for uploading: {time.time() - start}, file name: {file.filename}')
    except Exception as e:
        logger.error(f'Upload file error, detail: {e}.')
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f'Upload file error, detail: {e}.')

    # Prepare for creating package instance.
    # file_path = f'{local_settings.PACKAGES_FOLDER}/{file.filename}'

    # 以下2行代码可能涉及性能问题，因为此处为web端上传的package文件，可能是以GB为单位的包
    package_length = os.path.getsize(filename=file_path)
    package_hash = main_tools.get_package_hash(file_path)

    # e.g.: http://127.0.0.1:21080/packages/downloads/happymj.zip
    package_down_url = f'{local_settings.BASE_URL}/packages/downloads/{file.filename}'

    req_dict = main_tools.assemble_package_dict(pname=package_name,
                                                pversion=package_version,
                                                plength=str(package_length),
                                                phash=package_hash,
                                                pdownurl=package_down_url,
                                                pcmd=package_run_cmd,
                                                pdel=package_del_cmd,
                                                ppath=package_path)
    db_package = crud.create_package(db=db, req_dict=req_dict)

    if db_package:
        # 在创建package成功之后，更新newpackagelist的版本
        version = crud.retrieve_newpackagelist_desc(db=db)
        if version:
            new_version = f'{version.id + 1}'
            npl_dict = {'packagelist_version': new_version}
            crud.create_newpackagelist(db=db, npl_dict=npl_dict)
            logger.info(f'After create a package, update the newpackagelist {new_version}.')
        else:
            npl_dict = {'packagelist_version': '1'}
            crud.create_newpackagelist(db=db, npl_dict=npl_dict)
            logger.info(f'After create a package, update the newpackagelist 1.')

    return db_package


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
def publish_package(package_id: int,
                    package_version: str,
                    valid_places: str,
                    invalid_places: Optional[str] = Query(None),
                    package_run_cmd: Optional[str] = Query(None),
                    package_del_cmd: Optional[str] = Query(None),
                    package_path: str = Query(...),
                    db: Session = Depends(get_db)):
    if not crud.retrieve_package_by_package_id(package_id=package_id, db=db):
        logger.error(f'Package {package_id} not found.')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'Package {package_id} not found.')

    logger.debug(f'==== run_cmd: {package_run_cmd} ====')
    logger.debug(f'==== del_cmd: {package_del_cmd} ====')
    db_package = crud.update_package_to_publish(package_id=package_id,
                                                package_version=package_version,
                                                valid_places=valid_places,
                                                invalid_places=invalid_places,
                                                package_run_cmd=package_run_cmd,
                                                package_del_cmd=package_del_cmd,
                                                package_path=package_path,
                                                db=db)
    return db_package


@app.delete('/packages/{package_id}')
def remove_package(package_id: int, db: Session = Depends(get_db)) -> json:
    db_package = crud.retrieve_package_by_package_id(db=db, package_id=package_id)

    if db_package:
        resp = crud.delete_package(db=db, package_id=package_id)
        # [TODO]: Delete physical package.
        logger.info(f'Remove package {package_id} done.')

        # 在删除package成功之后，更新newpackagelist的版本，此后再返回
        # [TODO]: 抽象方法
        version = crud.retrieve_newpackagelist_desc(db=db)
        if version:
            new_version = f'{version.id + 1}'
            npl_dict = {'packagelist_version': new_version}
            crud.create_newpackagelist(db=db, npl_dict=npl_dict)
            logger.info(f'After delete a package {package_id}, updated the newpackagelist {new_version}.')
        else:
            npl_dict = {'packagelist_version': '1'}
            crud.create_newpackagelist(db=db, npl_dict=npl_dict)
            logger.info(f'After delete a package {package_id}, updated the newpackagelist 1.')

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
    file_path = f'{local_settings.PACKAGES_FOLDER}/{zip_file_name}'
    if os.path.exists(file_path):
        logger.debug(f'The request package {zip_file_name} is ready for downloading.')

        return FileResponse(file_path, filename=f'{zip_file_name}')

    else:
        logger.info(f'The request package {zip_file_name} not found.')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'The request package {zip_file_name} not found.')


@app.get('/npl/', response_model=List[schemas.PackagesList])
def get_newpackagelists(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)) -> list:
    db_newpackagelists = crud.retrieve_newpackagelists(db=db, skip=skip, limit=limit)

    if not db_newpackagelists:
        logger.error(f'No newpackagelist found.')
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail=f'No newpackagelist found.')

    logger.info(f'Get new package list.')
    return db_newpackagelists


@app.get("/updblaster/", summary='Main API')
def resp_to_client(package_name: str, place_code: str, db: Session = Depends(get_db)) -> json:
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
        db_packages = crud.retrieve_packages_all(db=db)  # 不分页，获取所有packages
        # [TODO]: 如果一个包都没有，部署器端无法识别，需要增加冗余方法
        if not db_packages:
            logger.error(f'No package found.')
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'No package found.')

        db_place = crud.retrieve_place_by_place_code(db=db, place_code=place_code)
        if not db_place:
            logger.error(f'No place found.')
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'No place found.')

        # 倒序获取最新id的行数据，也可以达到判断是否为空表的功能
        newpackagelist: schemas.PackagesList = crud.retrieve_newpackagelist_desc(db=db)
        if not newpackagelist:
            logger.error(f'No newpackagelist found.')
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'No packagelist found.')

        # 组装外层newpackagelist的数据
        newpackagelist_dict = main_tools.assemble_newpackagelist_dict(newpackagelist=newpackagelist,
                                                                      packages=db_packages)

        # 生成json文件并压缩成zip包
        resp_dict = main_tools.generate_zipped_json_file_then_resp(newpackagelist_dict=newpackagelist_dict)
        if not resp_dict:
            logger.error(f'Internal error occurred when dealing with newpackagelist, json, zip, and resp_dict.')
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                                detail=f'Internal error occurred.')

        return JSONResponse(content=jsonable_encoder(resp_dict))

    else:
        """
        请求: package_name != "packagelist"，则正常处理包请求
        """
        db_package: schemas.Package = crud.retrieve_package_by_package_name(db, package_name=package_name)
        if not db_package:
            logger.info(f'Package {package_name} not found.')
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'Package {package_name} not found.')

        db_place: schemas.Place = crud.retrieve_place_by_place_code(db, place_code=place_code)
        if not db_place:
            logger.info(f'Place {place_code} not found.')
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                                detail=f'Place {place_code} not found.')

        # 检查package是否在可更新范围内
        if not main_tools.check_update_enabled(package=db_package, place=db_place):
            logger.info(f'The place {db_place.place_name} is forbidden to be updated.')
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                detail=f"This package {package_name} are not enabled to be updated.")

        # 组装返回数据
        resp_dict = main_tools.assemble_package_dict(pname=db_package.package_name,
                                                     pversion=db_package.package_version,
                                                     plength=db_package.package_length,
                                                     phash=db_package.package_hash,
                                                     pdownurl=db_package.package_down_url,
                                                     ppath=db_package.package_path,  # [games]:\\blaster\\happymj\\
                                                     pcmd=db_package.package_run_cmd,
                                                     pdel=db_package.package_del_cmd)

        return JSONResponse(content=jsonable_encoder(resp_dict))


if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app='main:app', host='0.0.0.0', port=21080, workers=2, reload=True)
