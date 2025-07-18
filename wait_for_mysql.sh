#!/bin/bash


. .env

DB_HOST=${RDS_ENDPOINT}
while ! /usr/bin/mysqladmin ping -h"$DB_HOST" --silent; do
	echo "MySQL not running on ${DB_HOST}, sleep 1 second"
	/usr/bin/sleep 1
done
echo "MySQL is running on host: ${DB_HOST}"
