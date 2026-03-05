-- ==============================================================================
-- PostgreSQL initialization script for Nemo platform
-- Creates schemas needed by various services
-- ==============================================================================

-- Keycloak IAM schema
CREATE SCHEMA IF NOT EXISTS keycloak;

-- Temporal schema (if needed in future)
CREATE SCHEMA IF NOT EXISTS temporal;
CREATE SCHEMA IF NOT EXISTS temporal_visibility;
