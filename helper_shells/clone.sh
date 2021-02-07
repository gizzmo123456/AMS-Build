#!/bin/sh

# use sudo
# $1 = key path
# $2 = repo address

eval $(ssh-agent -s)

ssh-add $1

git clone $2

eval $(ssh-agent -k)
