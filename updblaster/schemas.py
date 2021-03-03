from datetime import datetime
from typing import Optional
from pydantic import BaseModel


# Place
class PlaceBase(BaseModel):
    place_code: str
    place_name: str
    description: Optional[str]
    package_path: Optional[str]


class PlaceCreate(PlaceBase):
    pass


class Place(PlaceBase):
    id: int
    created: datetime

    class Config:
        orm_mode = True


# Package
# 不同的schemas等级，在业务流中调用时，会有不同的权限
# 例如package_name, package_version如果在PackageCreate中，则在package: schemas.Package中是无法获取name和version的
class PackageBase(BaseModel):
    package_name: str
    package_version: str
    package_length: str
    package_hash: str
    package_down_url: str
    valid_places: Optional[str]
    invalid_places: Optional[str]
    package_run_cmd: Optional[str]
    package_del_cmd: Optional[str]


class PackageCreate(PackageBase):
    pass


class PackageUpdate(PackageBase):
    pass


class Package(PackageBase):
    id: int
    created: datetime

    class Config:
        orm_mode = True


# Controller
class PackagesListBase(BaseModel):
    """
    用于newpackagelist.json的管理，以及包的发布，选择可升级的place
    """
    packagelist_name: str
    packagelist_version: str


class PackagesListCreate(PackagesListBase):
    pass


class PackagesList(PackagesListBase):
    id: int
    created: datetime

    class Config:
        orm_mode = True


# History
class HistoryBase(BaseModel):
    package_name: str
    package_version: str
    place_code: str


class HistoryCreate(HistoryBase):
    pass


class History(HistoryBase):
    id: int
    download_count: str
    last_download: datetime

    class Config:
        orm_mode = True
