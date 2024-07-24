#!/bin/bash

IP=192.168.1.115
PIN=****
INTG_NAME=sonysdcp
PYTHON_VERSION=3.11.6-0.2.0

DRIVER_ID=$(sed -nE 's/^ *"driver_id": "([^"]+)".*/\1/p' driver.json)
VERSION=$(sed -nE 's/^ *"version": "([^"]+)".*/\1/p' driver.json)
FILENAME=uc-intg-$DRIVER_ID-$VERSION-aarch64

docker run --rm --name builder \
    --user=$(id -u):$(id -g) \
    -v "$PWD":/workspace \
    docker.io/unfoldedcircle/r2-pyinstaller:$PYTHON_VERSION  \
    bash -c \
      "cd /workspace && \
      python -m pip install -r requirements.txt && \
      pyinstaller --clean --onedir --name intg-$DRIVER_ID intg-$INTG_NAME/driver.py"

mkdir -p artifacts/bin
mv dist/intg-$DRIVER_ID/* artifacts/bin
mv artifacts/bin/intg-$DRIVER_ID artifacts/bin/driver
cp driver.json artifacts/
tar czvf $FILENAME.tar.gz -C artifacts .
rm -r dist build artifacts intg-$DRIVER_ID.spec

echo Upload...

curl --location "http://$IP/api/intg/install" --user "web-configurator:$PIN" --form "file=@"$FILENAME.tar.gz""