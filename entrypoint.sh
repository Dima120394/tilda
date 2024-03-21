#!/usr/bin/env sh
set -eu
set -x

gunicorn 'webhook_api:create_app()'
