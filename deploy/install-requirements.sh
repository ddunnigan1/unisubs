#!/bin/sh

set -ex

echo "installing requirements"
pip install --src /opt/src/amara/ -r requirements.txt
if [ ! -z "$DEV_INSTALL" ]; then
    echo 'installing dev requirements'
    pip install -r dev-requirements.txt
fi
echo "cleaning up /tmp/deploy"
cd /
rm -fr /tmp/deploy
