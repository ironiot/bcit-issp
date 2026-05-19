#!/bin/bash

set -euxo pipefail

pip install -r requirements.txt
python -m test.test_db_reader
