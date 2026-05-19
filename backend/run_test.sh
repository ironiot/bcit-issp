#!/bin/bash

set -euxo pipefail

pip install setuptools
pip install virtualenv
virtualenv .venv
source .venv/bin/activate

pip install -r requirements.txt
python -m test.test_db_reader
