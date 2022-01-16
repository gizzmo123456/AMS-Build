#!/usr/bin/env sh

# install Python dependices
# create the ams_path_config file
# add ams-build  alias

ROOT_DIRECTORY=$PWD

# check that python3 and pip3 are both installed
pythonInstalled=$(python3 --version|grep -oP "Python 3")  # NOTE: we could do with checking for a mim 3.x vresion

if [ "$pythonInstalled" = "Python 3" ]; then
  echo "Python 3 is installed!"
else
  echo "Python 3 is not installed. Please install python3 first then run this script again (Recommended version 3.9)"
  exit 1
fi;

pipInstalled=$(pip3 -V|grep -oP "python 3")

if [ "$pipInstalled" = "python 3" ]; then
  echo "Pip 3 is installed!"
else
  echo "Pip 3 is not installed. Please install pip3 (sudo apt install python3-pip) before continuing"
  exit 1

echo "Installing Python 3 Requirements..."
pip3 install -r ./requirements.txt

echo "Setting AMS-Build Root Directory..."
echo '{ "default_shell": "sh", "base_directory": "'$ROOT_DIRECTORY'"}' > $ROOT_DIRECTORY'/CI-Host/data/configs/ams_path_conf.json'

echo "Adding Alias..."
echo "\n" >> ~/.bashrc
echo "# Alias to launch AMS-Build" >> ~/.bashrc
echo 'alias amsbuild="cd '$ROOT_DIRECTORY'/CI-Host; sudo python3 main-ci-host.py;"' >> ~/.bashrc

. ~/.bashrc

echo "Setup Complete"
echo "Use Command 'amsbuild' to launch AMS-Build Application, (sudo rights required)"
