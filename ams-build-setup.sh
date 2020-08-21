#!/usr/bin/env sh

# install Python dependices
# create the ams_path_config file
# add ams-build  alias

ROOT_DIRECTORY=$PWD

echo "Installing Python 3 Requirements..."
pip3 install -r ./requirements.txt

echo "Setting AMS-Build Root Directory..."
echo '{ "default_shell": "sh", "base_directory": "'$ROOT_DIRECTORY'"}' > $ROOT_DIRECTORY'/CI-Host/data/test_path_conf.json'

echo "Adding Alias..."


echo "Setup Complete"
echo "Use Command 'amsbuild' to launch AMS-Build Application, (sudo rights required)"
