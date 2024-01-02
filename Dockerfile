FROM python:3.12-bookworm

ARG ARCH=

ENV BUILDARCH=${ARCH}
ENV GRONK_CSS_DIR=./css
ENV GRONK_JS_DIR=./js
ENV GRONK_TEMPLATES_DIR=./templates

WORKDIR /usr/src/app

RUN mkdir /notes
RUN mkdir /web

VOLUME /usr/src/app/notes
VOLUME /usr/src/app/web

RUN apt-get update \
  && wget -O ./pandoc.deb https://github.com/jgm/pandoc/releases/download/3.1.11/pandoc-3.1.11-1-${BUILDARCH}.deb \
  && apt install -y -f ./pandoc.deb \
  && rm ./pandoc.deb

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

RUN useradd -Ms /bin/nologin user
USER user

COPY . .

CMD [ "python3", "-u", "gronk.py", "--output-dir", "./web", "./notes" ]
