#!/bin/bash
mypath=`realpath $0`
cd `dirname $mypath`
python ./src/tanto.py $@
