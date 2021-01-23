import datetime
from sqlalchemy import Column, Integer, String, DateTime

from .database import Base


class Place(Base):
    __tablename__ = 'places'

    id = Column(Integer, primary_key=True, index=True)
    place_code = Column(String(256), unique=True, nullable=False, index=True, comment='Place识别码')
    place_name = Column(String(256), nullable=False, index=True, comment='Place名称')
    description = Column(String(1024), comment='描述')
    created = Column(DateTime, default=datetime.datetime.utcnow, comment="创建时间")


class Package(Base):
    __tablename__ = 'packages'

    id = Column(Integer, primary_key=True, index=True)
    package_name = Column(String(256), unique=True, nullable=False, index=True, comment='Package名称')
    package_version = Column(String(256), nullable=False, index=True, comment='Package版本')
    package_length = Column(String(1024), nullable=False, comment='Package大小')
    package_hash = Column(String(256), nullable=False, comment='Package哈希值')
    package_down_url = Column(String(256), nullable=False, comment='下载地址')
    created = Column(DateTime, default=datetime.datetime.utcnow, comment="创建时间")
    valid_places = Column(String(1024), comment='白名单')
    invalid_places = Column(String(1024), comment='黑名单')


class History(Base):
    __tablename__ = 'history'

    id = Column(Integer, primary_key=True, index=True)
    package_name = Column(String(256), nullable=False, index=True, comment='Package名称')
    package_version = Column(String(256), nullable=False, index=True, comment='Package版本')
    place_code = Column(String(256), nullable=False, index=True, comment='Place识别码')
    download_count = Column(String(10240), default='0', comment='同版本下载次数')
    last_download = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow, comment='最后下载时间')
