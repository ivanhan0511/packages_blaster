FROM python:3.8
ENV PYTHONUNBUFFERED 1

COPY pip.conf /root/.pip/pip.conf

RUN mkdir -p /opt/packages_blaster
WORKDIR /opt/packages_blaster
COPY requirements.txt /opt/packages_blaster/
RUN pip install -r requirements.txt

COPY . /opt/packages_blaster/
RUN /usr/local/bin/python -m pip install --upgrade pip
CMD uvicorn updblster.main:app --port 21080 --reload

