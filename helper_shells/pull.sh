#!/bin/sh

# use sudo
# $1 = key path


eval $(ssh-agent -s)

ssh-add $1

git pull origin

eval $(ssh-agent -k)

