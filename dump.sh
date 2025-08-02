#!/usr/bin/env bash

cd /usr/local/bcource

. .env

TEMPFILE=$(mktemp)
cat <<EOF > "${TEMPFILE}"
[client]
password="${MYSQL_ROOT_PASSWORD}"
EOF

mysqldump --defaults-extra-file=${TEMPFILE} -u root $*

rm -rf ${TEMPFILE}
