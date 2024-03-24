#!/bin/bash

pip install --no-cache-dir -q -r /usr/src/app/requirements.txt
cd /usr/src/app/intg-sonysdcp
python driver.py