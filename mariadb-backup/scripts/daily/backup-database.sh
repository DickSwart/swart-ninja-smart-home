
#!/bin/sh

BACKUP_FOLDER=/opt/mysql/backup
NOW=$(date '+%Y%m%d%T')

GZIP=$(which gzip)
MYSQLDUMP=$(which mysqldump)

### MySQL Server Login info ###
MDB=$MYSQL_DATABASE
MHOST=$MYSQL_CONTAINER_NAME
MPASS=$MYSQL_ROOT_PASSWORD
MUSER=root

[ ! -d "$BACKUP_FOLDER" ] && mkdir --parents $BACKUP_FOLDER

FILE=${BACKUP_FOLDER}/${MDB}_${NOW}.sql.gz
$MYSQLDUMP -h $MHOST -u $MUSER -p${MPASS} --databases $MDB | $GZIP -9 > $FILE