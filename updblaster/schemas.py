from datetime import datetime
from typing import Optional
# from sqlalchemy import DateTime
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
    created: datetime

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
    created: datetime
    valid_places: str
    invalid_places: str

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
