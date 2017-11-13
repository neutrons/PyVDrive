python setup_dev.py build_py --inplace
PYTHONPATH=$(dirname $0):$PYTHONPATH
PYTHONPATH=${PWD}:$PYTHONPATH
echo $PYTHONPATH
python scripts/Lava.py --live
