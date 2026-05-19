#!/bin/bash

set -euxo pipefail

python -m test.test_db_reader
