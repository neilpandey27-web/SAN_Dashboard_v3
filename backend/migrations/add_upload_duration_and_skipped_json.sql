-- Add upload_duration_seconds and skipped_records_json columns to upload_logs table
-- Migration for v1.4.4

ALTER TABLE upload_logs ADD COLUMN IF NOT EXISTS upload_duration_seconds FLOAT;
ALTER TABLE upload_logs ADD COLUMN IF NOT EXISTS skipped_records_json TEXT;

-- Add comment
COMMENT ON COLUMN upload_logs.upload_duration_seconds IS 'Upload processing time in seconds';
COMMENT ON COLUMN upload_logs.skipped_records_json IS 'JSON array of skipped records with full row data';
