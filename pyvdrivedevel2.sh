python setup.py build_py --inplace
PYTHONPATH=${PWD}/build/lib.linux-x86_64-2.7/:$PYTHONPATH
python scripts/Lava
