-- Migration 0008: backward-compatible schema expansion.
--
-- Safe while old and new application versions run side-by-side.
-- No existing column is removed or changed.
-- Rollback is done by deploying the previous application version.
-- No down-migration is required.

ALTER TABLE settlements
    ADD COLUMN IF NOT EXISTS processing_version TEXT;

CREATE INDEX IF NOT EXISTS idx_settlements_processing_version
    ON settlements(processing_version);