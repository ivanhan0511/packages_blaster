from typing import Optional
from sqlalchemy import DateTime
from pydantic import BaseModel


# Place
class PlaceBase(BaseModel):
    place_code: str
    place_name: str
    description: Optional[str] = None


class PlaceCreate(PlaceBase):
    pass


class Place(PlaceBase):
    id: int
    created: DateTime

    class Config:
        orm_mode = True


# Package
class PackageBase(BaseModel):
    package_name: str
    package_version: str
    package_length: str
    package_hash: str
    package_down_url: str


class PackageCreate(PackageBase):
    pass


class Package(PackageBase):
    id: int
    created: DateTime
    valid_places: str
    invalid_places: str

    class Config:
        orm_mode = True


# History
class HistoryBase(BaseModel):
    pass


class HistoryCreate(HistoryBase):
    package_name: str
    package_versio: str
    place_code: str


class History(HistoryBase):
    id: int
    download_coun: str
    last_download: DateTime
