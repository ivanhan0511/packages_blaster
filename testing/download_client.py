import requests


url1 = 'http://127.0.0.1:21080/packages/file'
resp = requests.get(url1)
resp.raise_for_status()

# [TODO]: `raise_for_status()`与`status_code == 200`如何去重？
if resp.status_code == 200:
    with open('downloaded_file', 'wb') as f:
        f.write(resp.content)


# -----------------------------------------------

url2 = 'http://127.0.0.1:21080/packages/happymj'
resp = requests.get(url2)

if resp.status_code == 200:
    with open('large_file', 'wb') as f:
        for chunk in resp.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

# -----------------------------------------------

url3 = 'http://127.0.0.1:21080/packages/text.txt'
resp = requests.get(url3)

if resp.status_code == 200:
    with open('text_file.txt', 'wb') as f:
        for chunk in resp.iter_lines():
            f.write(chunk)
