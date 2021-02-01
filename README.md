# packages_blaster


A packages management platform.

## 发布

- Package与Place不建立外键关系
- Package具有属性`valid_places`,`invalid_place`来做黑白名单，而Place没有该属性
- Package上传(`POST`)时不允许设置黑白名单参数，必须通过手动修改的方式(`PUT`)来设定可更新的Place

### Package
So far, 可以上传的包，即视为可用的包。

### Place
通过黑白名单达到控制具体可更新的Place


## Deployment

### Installations

```python
# pip install fastapi uvicorn starlette pydantic sqlalchemy mysqlclient aiofiles python-multipart
```

### Configurations
- database.py:
  - `SQLALCHEMY_DATABASE_URL`
- logger.py:
  - `logger = logging.getLogger("Blaster")`
  - `file_handler = logging.FileHandler('/Users/ivan/logs/default.log')`
- main.py:
  - `DEBUG`
  - `BASE_URL`
  - `PACKAGES_FOLDER`
