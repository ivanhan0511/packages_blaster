# from


# def add_1_
# 在删除package成功之后，更新newpackagelist的版本
# version = crud.retrieve_newpackagelist_desc(db=db)
# if version:
#     new_version = f'{version.id + 1}'
#     d = {'packagelist_version': new_version}
#     crud.create_newpackagelist(db=db, npl_dict=d)
#     logger.info(f'After delete a package {package_id}, updated the newpackagelist {new_version}.')
# else:
#     d = {'packagelist_version': '1'}
#     crud.create_newpackagelist(db=db, npl_dict=d)
#     logger.info(f'After delete a package {package_id}, updated the newpackagelist 1.')
