-- Migration: add erp_company_name to contact
-- Date: 2026-03-04

ALTER TABLE qc_coversheet.contact
ADD COLUMN IF NOT EXISTS erp_company_name text;
