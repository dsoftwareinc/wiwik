#!/usr/bin/env bash
# Script for creating a backup of the database and sending it via email

EMAIL=wiwik@moransoftware.ca
export LC_ALL=en_US.UTF-8
export LANG=en_US.UTF-8
DATE="$(date +%Y-%m-%d__%H-%M-%S)"
BACKUP_FILENAME="backup_$DATE.sql.gz"
sudo -u postgres pg_dump devbb | gzip > "$BACKUP_FILENAME"
# send backup via email
echo "Backup for $DATE" | mutt -s "Backup for $DATE" -a "$BACKUP_FILENAME" -- $EMAIL
rm "$BACKUP_FILENAME"

# backup to s3 bucket
#S3_BUCKET="s3://wiwik-backup"
#/usr/local/bin/aws s3 cp $BACKUP_FILENAME $S3_BUCKET
#rm $BACKUP_FILENAME