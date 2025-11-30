#!/bin/sh
# =============================================================================
# FLVS - Database Backup Script
# =============================================================================

BACKUP_DIR="/backup"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/flvs_backup_$DATE.sql.gz"

echo "Starting backup at $(date)"

# Create backup
pg_dump -h "$PGHOST" -U "$PGUSER" -d "$PGDATABASE" | gzip > "$BACKUP_FILE"

if [ $? -eq 0 ]; then
    echo "Backup successful: $BACKUP_FILE"
    
    # Remove old backups
    find "$BACKUP_DIR" -name "flvs_backup_*.sql.gz" -mtime +${BACKUP_RETENTION_DAYS:-30} -delete
    echo "Old backups cleaned up"
else
    echo "Backup failed!"
    exit 1
fi
