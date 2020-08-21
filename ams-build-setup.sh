#!/usr/bin/env sh

# install Python dependices
# create the ams_path_config file
# add ams-build  alias

ROOT_DIRECTORY=$PWD

echo "Installing Python 3 Requirements..."
pip3 install -r ./requirements.txt

echo "Setting AMS-Build Root Directory..."
echo '{ "default_shell": "sh", "base_directory": "'$ROOT_DIRECTORY'"}' > $ROOT_DIRECTORY'/CI-Host/data/ams_path_conf.json'

echo "Adding Alias..."
echo "\n\n" >> ~/.bashrc
echo "# Alias to launch AMS-Build" >> ~/.bashrc
echo 'alias amsbuild="cd '$ROOT_DIRECTORY'/CI-Host; sudo python3 main-ci-host.py;"' >> ~/.bashrc

echo "Setup Complete"
echo "Use Command 'amsbuild' to launch AMS-Build Application, (sudo rights required)"
