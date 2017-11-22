python setup_dev.py build_py --inplace
PYTHONPATH=$(dirname $0):$PYTHONPATH
PYTHONPATH=${PWD}:$PYTHONPATH
echo $PYTHONPATH
echo $1
python scripts/Lava.py $1
