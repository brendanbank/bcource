#!/usr/bin/env bash

cd /usr/local/bcource

. .env

TEMPFILE=$(mktemp)
cat <<EOF > "${TEMPFILE}"
[client]
password="${MYSQL_PWD}"
EOF

mysqldump --defaults-extra-file=${TEMPFILE} -u ${RDS_USER} -h ${RDS_ENDPOINT} $*

rm -rf ${TEMPFILE}
