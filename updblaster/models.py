from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func

from .database import Base


class Place(Base):
    __tablename__ = 'places'

    id = Column(Integer, primary_key=True, index=True)
    place_code = Column(String(256), unique=True, nullable=False, index=True, comment='Place识别码')
    place_name = Column(String(256), nullable=False, index=True, comment='Place名称')
    description = Column(String(1024), comment='描述')
    # package_path = Column(String(512), nullable=False, default='e:\\blaster\\', comment='Customized Path')
    # 通配符的概念，例如games：游戏盘，images：镜像盘......接口以某网吧的某游戏盘为默认规则
    # 网吧服务端收到该信息后，会按照"镜像盘"的type去注册表查找数据库位置，再从SQLite中找到对应"游戏盘"的系统盘符，例如"E:\"盘
    # drive与type对应关系是通过YGX的逆向工程得出来的，记录如下：
    # type, comment  <==> drive, comment
    #    0, 未配置    <==>    67, C盘
    #    1, 游戏盘    <==>    71, G盘
    #    2, 回写盘    <==>    72, H盘
    #    3, 镜像盘    <==>    70, F盘
    #    4, 下载盘    <==>    69, E盘

    # Update: Mar 08, 2021, 取消在Place属性中设置包路径
    # package_path = Column(String(512), nullable=False, default='games', comment='Customized Path')
    created = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    # last_updated = Column(DateTime(timezone=True), onupdate=func.now(), comment="最后更新时间")


class Package(Base):
    __tablename__ = 'packages'

    id = Column(Integer, primary_key=True, index=True)
    package_name = Column(String(256), unique=True, nullable=False, index=True, comment='Package名称')
    package_version = Column(String(256), nullable=False, index=True, comment='Package版本')
    package_length = Column(String(1024), nullable=False, comment='Package大小')
    package_hash = Column(String(256), nullable=False, comment='Package哈希值')
    package_down_url = Column(String(256), nullable=False, comment='下载地址')
    package_run_cmd = Column(String(256), nullable=True, default='', comment='执行命令')
    package_del_cmd = Column(String(256), nullable=True, default='', comment='删除命令')
    created = Column(DateTime(timezone=True), server_default=func.now(), comment="创建时间")
    # last_updated = Column(DateTime(timezone=True), onupdate=func.now(), comment="最后更新时间")
    valid_places = Column(String(1024), default='', comment='白名单')
    invalid_places = Column(String(1024), default='', comment='黑名单')
    package_path = Column(String(512), nullable=False, comment='Customized Path')


class PackageList(Base):
    __tablename__ = 'packagelist'

    id = Column(Integer, primary_key=True, index=True)
    packagelist_name = Column(String(256), nullable=False, default='packagelist', comment='packagelist名称')
    packagelist_version = Column(String(256), nullable=False, comment='packagelist版本')
    created = Column(DateTime(timezone=True), server_default=func.now(), comment='创建时间')
    # last_updated = Column(DateTime(timezone=True), onupdate=func.now(), comment="最后更新时间")


class History(Base):
    __tablename__ = 'history'

    id = Column(Integer, primary_key=True, index=True)
    package_name = Column(String(256), nullable=False, index=True, comment='Package名称')
    package_version = Column(String(256), nullable=False, index=True, comment='Package版本')
    place_code = Column(String(256), nullable=False, index=True, comment='Place识别码')
    download_count = Column(String(10240), default='0', comment='同版本下载次数')
    # last_download = Column(DateTime(timezone=True), onupdate=func.now(), comment='最后下载时间')
