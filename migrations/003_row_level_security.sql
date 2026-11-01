-- ============================================================================
-- 003_row_level_security.sql
-- Legislative Intelligence & Market Impact Platform
-- Canonical PostgreSQL Migration: Multi-Tenant Row Level Security (RLS)
-- Compatible with Local PostgreSQL session context and Supabase Auth
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Helper Function: Extract Tenant ID from Session or JWT
-- ----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION get_current_tenant_id()
RETURNS VARCHAR AS $$
BEGIN
    -- 1. Check local session variable (standard PostgreSQL)
    IF NULLIF(current_setting('app.current_tenant_id', true), '') IS NOT NULL THEN
        RETURN current_setting('app.current_tenant_id', true);
    END IF;

    -- 2. Check PostgREST / Supabase JWT claims if available
    BEGIN
        IF NULLIF(current_setting('request.jwt.claims', true), '') IS NOT NULL THEN
            RETURN (current_setting('request.jwt.claims', true)::jsonb ->> 'tenant_id');
        END IF;
    EXCEPTION WHEN OTHERS THEN
        -- Fall through if json parsing fails
    END;

    -- 3. Check individual claim setting
    IF NULLIF(current_setting('request.jwt.claim.tenant_id', true), '') IS NOT NULL THEN
        RETURN current_setting('request.jwt.claim.tenant_id', true);
    END IF;

    RETURN NULL;
END;
$$ LANGUAGE plpgsql STABLE;

-- ----------------------------------------------------------------------------
-- 2. Enable RLS on Tenant-Owned Tables
-- ----------------------------------------------------------------------------

ALTER TABLE portfolios ENABLE ROW LEVEL SECURITY;
ALTER TABLE portfolio_holdings ENABLE ROW LEVEL SECURITY;
ALTER TABLE watchlists ENABLE ROW LEVEL SECURITY;
ALTER TABLE watchlist_items ENABLE ROW LEVEL SECURITY;
ALTER TABLE alert_rules ENABLE ROW LEVEL SECURITY;
ALTER TABLE alert_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE saved_searches ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE ai_usage_records ENABLE ROW LEVEL SECURITY;

-- ----------------------------------------------------------------------------
-- 3. Define Tenant Isolation Policies
-- ----------------------------------------------------------------------------

-- Portfolios
DROP POLICY IF EXISTS tenant_isolation_portfolios ON portfolios;
CREATE POLICY tenant_isolation_portfolios ON portfolios
    FOR ALL
    USING (
        tenant_id = get_current_tenant_id()
        OR get_current_tenant_id() IS NULL -- Permissive when session context not explicitly set (e.g. background worker)
    );

-- Portfolio Holdings
DROP POLICY IF EXISTS tenant_isolation_holdings ON portfolio_holdings;
CREATE POLICY tenant_isolation_holdings ON portfolio_holdings
    FOR ALL
    USING (
        tenant_id = get_current_tenant_id()
        OR get_current_tenant_id() IS NULL
    );

-- Watchlists
DROP POLICY IF EXISTS tenant_isolation_watchlists ON watchlists;
CREATE POLICY tenant_isolation_watchlists ON watchlists
    FOR ALL
    USING (
        tenant_id = get_current_tenant_id()
        OR get_current_tenant_id() IS NULL
    );

-- Watchlist Items
DROP POLICY IF EXISTS tenant_isolation_watchlist_items ON watchlist_items;
CREATE POLICY tenant_isolation_watchlist_items ON watchlist_items
    FOR ALL
    USING (
        tenant_id = get_current_tenant_id()
        OR get_current_tenant_id() IS NULL
    );

-- Alert Rules
DROP POLICY IF EXISTS tenant_isolation_alert_rules ON alert_rules;
CREATE POLICY tenant_isolation_alert_rules ON alert_rules
    FOR ALL
    USING (
        tenant_id = get_current_tenant_id()
        OR get_current_tenant_id() IS NULL
    );

-- Alert Events
DROP POLICY IF EXISTS tenant_isolation_alert_events ON alert_events;
CREATE POLICY tenant_isolation_alert_events ON alert_events
    FOR ALL
    USING (
        tenant_id = get_current_tenant_id()
        OR get_current_tenant_id() IS NULL
    );

-- Notifications
DROP POLICY IF EXISTS tenant_isolation_notifications ON notifications;
CREATE POLICY tenant_isolation_notifications ON notifications
    FOR ALL
    USING (
        tenant_id = get_current_tenant_id()
        OR get_current_tenant_id() IS NULL
    );

-- Notification Preferences
DROP POLICY IF EXISTS tenant_isolation_notification_preferences ON notification_preferences;
CREATE POLICY tenant_isolation_notification_preferences ON notification_preferences
    FOR ALL
    USING (
        tenant_id = get_current_tenant_id()
        OR get_current_tenant_id() IS NULL
    );

-- User Preferences
DROP POLICY IF EXISTS tenant_isolation_user_preferences ON user_preferences;
CREATE POLICY tenant_isolation_user_preferences ON user_preferences
    FOR ALL
    USING (
        tenant_id = get_current_tenant_id()
        OR get_current_tenant_id() IS NULL
    );

-- Saved Searches
DROP POLICY IF EXISTS tenant_isolation_saved_searches ON saved_searches;
CREATE POLICY tenant_isolation_saved_searches ON saved_searches
    FOR ALL
    USING (
        tenant_id = get_current_tenant_id()
        OR get_current_tenant_id() IS NULL
    );

-- Audit Logs
DROP POLICY IF EXISTS tenant_isolation_audit_logs ON audit_logs;
CREATE POLICY tenant_isolation_audit_logs ON audit_logs
    FOR ALL
    USING (
        tenant_id = get_current_tenant_id()
        OR get_current_tenant_id() IS NULL
    );

-- AI Usage Records
DROP POLICY IF EXISTS tenant_isolation_ai_usage ON ai_usage_records;
CREATE POLICY tenant_isolation_ai_usage ON ai_usage_records
    FOR ALL
    USING (
        tenant_id = get_current_tenant_id()
        OR get_current_tenant_id() IS NULL
    );
