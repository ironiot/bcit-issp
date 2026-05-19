#!/bin/bash

set -euxo pipefail

pip install virtualenv
virtualenv .venv
source .venv/bin/activate
pip install "setuptools<81" wheel
pip install -r test/requirements.txt

python -m test.test_db_reader
