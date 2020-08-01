#!/usr/bin/env sh

# make sure the dependencies are install
# and run the application
pip3 install -r ./requirements.txt
cd ./CI-Host/
python3 ./main-ci-host.py