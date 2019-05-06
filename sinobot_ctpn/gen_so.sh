#!/bin/bash

currentdir=`pwd`
# check setup.py exists or not
if [ ! -f "setup.py" ]; then
    echo "setup.py does not exist, we need it to generate so lib files." 
    echo "please copy latest setup.py to the same dir as this script's."
    exit 1
fi

# need a root dir which contains sinobotocr and sinobot_ctpn
if [  $# -lt 1 ]; then
    echo "please provide a root dir which contains sinobotocr and sinobot_ctpn."
    exit 1
else
    rootdir=$1
    cd $rootdir
    rootdir=`pwd`
    if [ ! -d "$rootdir" ] || [ ! -d "sinobotocr" ] || [ ! -d "sinobot_ctpn" ]; then
       echo "please provide correct dir which includes sinobotocr or sinobot_ctpn directory."
       exit 1
    fi
fi

# check whether all the pyx files existed
echo "Checking whether all the pyx files are existing...."
for file in `find -L . -type f -name "*.py" -print | egrep -v "setup.py" | egrep -v "__init__.py"`
do
    pyxfile="${file}x"
    if [ ! -f $pyxfile ]; then
        echo "file $pyxfile does not exist,please check."
        exit 1
    fi  
done

# copy setup.py and generate so files
subdirs=`find -L . -type d -name "*" -print` 
for sub in $subdirs
do
    ls $rootdir/$sub/*.pyx > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        cp -rf $currentdir/setup.py $rootdir/$sub
        cd $rootdir/$sub
        echo "Generating so files under `pwd`"
        python3 setup.py build_ext --inplace
        if [ $? -ne 0 ]; then
            echo "FATAL: creating so files failed under `pwd`"
            exit 1
        fi
        rm -rf build/
        rm -rf *.c
        path=${sub##./*/}
        if [ -f "__init__.py" ]; then
            mv $path/*.so .
            rm -rf $path
        fi
    fi
done  

