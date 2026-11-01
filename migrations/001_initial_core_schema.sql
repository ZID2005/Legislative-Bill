-- ============================================================================
-- 001_initial_core_schema.sql
-- Legislative Intelligence & Market Impact Platform
-- Canonical PostgreSQL Migration: Core Application & Domain Schema
-- Compatible with Local PostgreSQL and Supabase Free
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Identity & Tenancy
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS tenants (
    tenant_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    plan_tier VARCHAR(32) NOT NULL DEFAULT 'FREE', -- FREE, PRO, TEAM, ENTERPRISE
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',  -- ACTIVE, SUSPENDED, DEACTIVATED, TRIAL, DELETED
    billing_customer_id VARCHAR(128),
    subscription_id VARCHAR(128),
    subscription_status VARCHAR(32) DEFAULT 'NONE',
    seats_limit INT NOT NULL DEFAULT 5,
    max_watchlists INT NOT NULL DEFAULT 5,
    max_rules INT NOT NULL DEFAULT 20,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_tenants_plan ON tenants(plan_tier);
CREATE INDEX IF NOT EXISTS idx_tenants_status ON tenants(status);

CREATE TABLE IF NOT EXISTS users (
    user_id VARCHAR(64) PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255),
    full_name VARCHAR(255),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    is_verified BOOLEAN NOT NULL DEFAULT FALSE,
    external_idp_sub VARCHAR(255) UNIQUE,
    idp_provider VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_external_sub ON users(external_idp_sub);

CREATE TABLE IF NOT EXISTS tenant_memberships (
    membership_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    role VARCHAR(32) NOT NULL DEFAULT 'MEMBER', -- OWNER, ADMIN, MEMBER, VIEWER
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tenant_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_memberships_tenant ON tenant_memberships(tenant_id);
CREATE INDEX IF NOT EXISTS idx_memberships_user ON tenant_memberships(user_id);

CREATE TABLE IF NOT EXISTS user_preferences (
    preference_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    theme VARCHAR(32) DEFAULT 'dark',
    default_jurisdiction VARCHAR(32) DEFAULT 'all',
    risk_appetite VARCHAR(32) DEFAULT 'BALANCED',
    email_notifications BOOLEAN DEFAULT TRUE,
    in_app_notifications BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tenant_id, user_id)
);

CREATE INDEX IF NOT EXISTS idx_user_preferences_user ON user_preferences(tenant_id, user_id);

-- ----------------------------------------------------------------------------
-- 2. Legislation & Governance
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS jurisdictions (
    jurisdiction_code VARCHAR(32) PRIMARY KEY, -- 'CENTRAL', 'AP', 'KA', 'KL', 'TS', etc.
    name VARCHAR(128) NOT NULL,
    type VARCHAR(32) NOT NULL,                 -- 'CENTRAL', 'STATE'
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE', -- 'ACTIVE', 'ROADMAP'
    bills_count INT NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS bills (
    bill_id VARCHAR(128) PRIMARY KEY,
    jurisdiction VARCHAR(32) NOT NULL,         -- 'central', 'state'
    jurisdiction_code VARCHAR(32) NOT NULL REFERENCES jurisdictions(jurisdiction_code),
    state VARCHAR(64),                         -- e.g. 'Andhra Pradesh', 'Karnataka'
    title VARCHAR(512) NOT NULL,
    short_title VARCHAR(256),
    bill_number VARCHAR(64),
    legislature VARCHAR(128),
    house VARCHAR(64),
    year INT,
    introduction_date VARCHAR(32),
    assent_date VARCHAR(32),
    status VARCHAR(64) NOT NULL DEFAULT 'introduced',
    policy_domain VARCHAR(128),
    economic_sectors JSONB NOT NULL DEFAULT '[]'::jsonb,
    secondary_sectors JSONB NOT NULL DEFAULT '[]'::jsonb,
    stakeholders JSONB NOT NULL DEFAULT '[]'::jsonb,
    summary TEXT,
    company_exposure_count INT NOT NULL DEFAULT 0,
    listed_company_exposure_count INT NOT NULL DEFAULT 0,
    market_relevance VARCHAR(32) DEFAULT 'UNKNOWN',
    modeling_eligibility VARCHAR(32) DEFAULT 'ELIGIBLE',
    data_sufficiency VARCHAR(32) DEFAULT 'SUFFICIENT',
    source_url TEXT,
    pdf_url TEXT,
    data_quality VARCHAR(32) DEFAULT 'VALID',
    is_production BOOLEAN NOT NULL DEFAULT TRUE,
    is_scanned BOOLEAN NOT NULL DEFAULT TRUE,
    is_frozen BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_bills_jurisdiction ON bills(jurisdiction);
CREATE INDEX IF NOT EXISTS idx_bills_state ON bills(state);
CREATE INDEX IF NOT EXISTS idx_bills_year ON bills(year);
CREATE INDEX IF NOT EXISTS idx_bills_status ON bills(status);
CREATE INDEX IF NOT EXISTS idx_bills_policy ON bills(policy_domain);

CREATE TABLE IF NOT EXISTS bill_versions (
    version_id VARCHAR(64) PRIMARY KEY,
    bill_id VARCHAR(128) NOT NULL REFERENCES bills(bill_id) ON DELETE CASCADE,
    version_number INT NOT NULL DEFAULT 1,
    content_hash VARCHAR(64) NOT NULL,
    publication_timestamp TIMESTAMPTZ,
    retrieval_timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    source_url TEXT,
    status VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (bill_id, version_number)
);

CREATE INDEX IF NOT EXISTS idx_bill_versions_bill ON bill_versions(bill_id);

CREATE TABLE IF NOT EXISTS official_documents (
    document_id VARCHAR(64) PRIMARY KEY,
    bill_id VARCHAR(128) NOT NULL REFERENCES bills(bill_id) ON DELETE CASCADE,
    document_type VARCHAR(64) NOT NULL, -- 'ACT_PDF', 'BILL_TEXT', 'AMENDMENT', 'PRS_SUMMARY'
    title VARCHAR(256) NOT NULL,
    file_path TEXT,
    url TEXT,
    content_hash VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_documents_bill ON official_documents(bill_id);

CREATE TABLE IF NOT EXISTS sources (
    source_id VARCHAR(64) PRIMARY KEY,
    source_name VARCHAR(255) NOT NULL,
    source_url TEXT NOT NULL,
    jurisdiction_code VARCHAR(32) NOT NULL REFERENCES jurisdictions(jurisdiction_code),
    source_type VARCHAR(64) NOT NULL, -- 'PARLIAMENT', 'GAZETTE', 'STATE_PORTAL', 'REGULATOR'
    credibility_tier VARCHAR(32) NOT NULL DEFAULT 'TIER_1',
    status VARCHAR(32) NOT NULL DEFAULT 'ACTIVE',
    check_interval_hours INT NOT NULL DEFAULT 24,
    last_checked_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_sources_jurisdiction ON sources(jurisdiction_code);

CREATE TABLE IF NOT EXISTS source_health (
    health_id VARCHAR(64) PRIMARY KEY,
    source_id VARCHAR(64) NOT NULL REFERENCES sources(source_id) ON DELETE CASCADE,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(32) NOT NULL, -- 'HEALTHY', 'DEGRADED', 'FAILED'
    response_time_ms INT,
    http_status INT,
    error_message TEXT
);

CREATE INDEX IF NOT EXISTS idx_source_health_source ON source_health(source_id, checked_at DESC);

-- ----------------------------------------------------------------------------
-- 3. Corporate Universe & Classifications
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS sectors (
    sector_name VARCHAR(128) PRIMARY KEY,
    code VARCHAR(64),
    description TEXT
);

CREATE TABLE IF NOT EXISTS industries (
    industry_name VARCHAR(128) PRIMARY KEY,
    sector_name VARCHAR(128) NOT NULL REFERENCES sectors(sector_name),
    description TEXT
);

CREATE TABLE IF NOT EXISTS companies (
    isin VARCHAR(16) PRIMARY KEY,
    company_name VARCHAR(255) NOT NULL,
    ticker_nse VARCHAR(32),
    ticker_bse VARCHAR(32),
    bse_code VARCHAR(32),
    sector VARCHAR(128) NOT NULL,
    industry VARCHAR(128) NOT NULL,
    sub_industry VARCHAR(128),
    market_cap_category VARCHAR(32) DEFAULT 'large_cap', -- large_cap, mid_cap, small_cap, unknown
    market_cap_cr NUMERIC(14, 2),
    hq_state VARCHAR(64),
    hq_city VARCHAR(128),
    website TEXT,
    listing_date VARCHAR(32),
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    listing_status VARCHAR(32) NOT NULL DEFAULT 'Listed',
    entity_type VARCHAR(64) NOT NULL DEFAULT 'listed_company',
    universe_type VARCHAR(32) NOT NULL DEFAULT 'quantitative', -- 'quantitative', 'intelligence', 'both'
    coverage_tier VARCHAR(32) NOT NULL DEFAULT 'QUANTITATIVE',  -- 'QUANTITATIVE', 'INTELLIGENCE_ONLY', 'REFERENCE'
    is_quant_eligible BOOLEAN NOT NULL DEFAULT FALSE,
    aliases JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_companies_ticker_nse ON companies(ticker_nse);
CREATE INDEX IF NOT EXISTS idx_companies_sector ON companies(sector);
CREATE INDEX IF NOT EXISTS idx_companies_industry ON companies(industry);
CREATE INDEX IF NOT EXISTS idx_companies_coverage ON companies(coverage_tier);
CREATE INDEX IF NOT EXISTS idx_companies_quant_eligible ON companies(is_quant_eligible);

CREATE TABLE IF NOT EXISTS corporate_exposures (
    exposure_id VARCHAR(64) PRIMARY KEY,
    bill_id VARCHAR(128) NOT NULL REFERENCES bills(bill_id) ON DELETE CASCADE,
    company_isin VARCHAR(64) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    jurisdiction VARCHAR(32) NOT NULL DEFAULT 'central',
    state VARCHAR(64),
    exposure_type VARCHAR(64) NOT NULL DEFAULT 'regulatory',
    exposure_direction VARCHAR(32) NOT NULL DEFAULT 'neutral', -- 'positive', 'negative', 'neutral', 'mixed'
    exposure_strength VARCHAR(32) NOT NULL DEFAULT 'MEDIUM',   -- 'HIGH', 'MEDIUM', 'LOW'
    direct_indirect VARCHAR(32) NOT NULL DEFAULT 'DIRECT',    -- 'DIRECT', 'INDIRECT'
    mechanism VARCHAR(128) DEFAULT 'compliance',
    market_relevance VARCHAR(32) DEFAULT 'UNKNOWN',
    confidence VARCHAR(32) DEFAULT 'HIGH',
    evidence_count INT NOT NULL DEFAULT 0,
    source_urls JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (bill_id, company_isin)
);

CREATE INDEX IF NOT EXISTS idx_corporate_exposures_bill ON corporate_exposures(bill_id);
CREATE INDEX IF NOT EXISTS idx_corporate_exposures_company ON corporate_exposures(company_isin);

-- ----------------------------------------------------------------------------
-- 4. Evidence
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS evidence_sources (
    source_id VARCHAR(64) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    url TEXT,
    credibility_tier VARCHAR(32) NOT NULL DEFAULT 'TIER_1',
    source_type VARCHAR(64) NOT NULL DEFAULT 'OFFICIAL_PORTAL'
);

CREATE TABLE IF NOT EXISTS evidence (
    evidence_id VARCHAR(64) PRIMARY KEY,
    bill_id VARCHAR(128) NOT NULL REFERENCES bills(bill_id) ON DELETE CASCADE,
    company_isin VARCHAR(16) REFERENCES companies(isin) ON DELETE SET NULL,
    source_id VARCHAR(64) REFERENCES evidence_sources(source_id) ON DELETE SET NULL,
    source_url TEXT,
    source_type VARCHAR(64) NOT NULL,
    credibility_tier VARCHAR(32) NOT NULL DEFAULT 'TIER_1',
    publication_date VARCHAR(32),
    content_hash VARCHAR(64),
    summary TEXT NOT NULL,
    excerpt TEXT,
    temporal_relation VARCHAR(32) DEFAULT 'CONCURRENT', -- 'PRE_EVENT', 'CONCURRENT', 'POST_EVENT'
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_evidence_bill ON evidence(bill_id);
CREATE INDEX IF NOT EXISTS idx_evidence_company ON evidence(company_isin);

-- ----------------------------------------------------------------------------
-- 5. Application & Multi-Tenant Domains
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS portfolios (
    portfolio_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_portfolios_tenant_user ON portfolios(tenant_id, user_id, is_active);

CREATE TABLE IF NOT EXISTS portfolio_holdings (
    holding_id VARCHAR(64) PRIMARY KEY,
    portfolio_id VARCHAR(64) NOT NULL REFERENCES portfolios(portfolio_id) ON DELETE CASCADE,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    company_name VARCHAR(255) NOT NULL,
    ticker VARCHAR(32) NOT NULL,
    isin VARCHAR(16) NOT NULL,
    quantity NUMERIC(14, 4) NOT NULL DEFAULT 1.0,
    avg_purchase_price NUMERIC(14, 2) DEFAULT 0.0,
    current_value NUMERIC(14, 2) DEFAULT 0.0,
    sector VARCHAR(128),
    industry VARCHAR(128),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_holdings_portfolio ON portfolio_holdings(portfolio_id);
CREATE INDEX IF NOT EXISTS idx_holdings_tenant_user ON portfolio_holdings(tenant_id, user_id);
CREATE INDEX IF NOT EXISTS idx_holdings_isin ON portfolio_holdings(isin);

CREATE TABLE IF NOT EXISTS watchlists (
    watchlist_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    is_default BOOLEAN NOT NULL DEFAULT FALSE,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_watchlists_tenant_user ON watchlists(tenant_id, user_id, is_active);

CREATE TABLE IF NOT EXISTS watchlist_items (
    item_id VARCHAR(64) PRIMARY KEY,
    watchlist_id VARCHAR(64) NOT NULL REFERENCES watchlists(watchlist_id) ON DELETE CASCADE,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    entity_type VARCHAR(32) NOT NULL, -- 'bill', 'company', 'sector'
    entity_id VARCHAR(128) NOT NULL,
    canonical_name VARCHAR(255),
    state VARCHAR(64),
    notes TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (watchlist_id, entity_type, entity_id)
);

CREATE INDEX IF NOT EXISTS idx_watchlist_items_entity ON watchlist_items(tenant_id, entity_type, entity_id);

CREATE TABLE IF NOT EXISTS alert_rules (
    rule_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    watchlist_id VARCHAR(64) REFERENCES watchlists(watchlist_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    rule_type VARCHAR(64) NOT NULL,
    minimum_severity VARCHAR(32) NOT NULL DEFAULT 'MEDIUM',
    conditions JSONB NOT NULL DEFAULT '{}'::jsonb,
    enabled BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alert_rules_tenant ON alert_rules(tenant_id, enabled);

CREATE TABLE IF NOT EXISTS alert_events (
    event_id VARCHAR(64) PRIMARY KEY,
    rule_id VARCHAR(64) REFERENCES alert_rules(rule_id) ON DELETE SET NULL,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    bill_id VARCHAR(128),
    company_id VARCHAR(64),
    severity VARCHAR(32) NOT NULL DEFAULT 'MEDIUM',
    event_type VARCHAR(64) NOT NULL,
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_alert_events_tenant ON alert_events(tenant_id, created_at DESC);

CREATE TABLE IF NOT EXISTS notifications (
    notification_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    body TEXT,
    channel VARCHAR(32) NOT NULL DEFAULT 'IN_APP', -- 'IN_APP', 'EMAIL', 'WEBHOOK'
    status VARCHAR(32) NOT NULL DEFAULT 'UNREAD',  -- 'UNREAD', 'READ', 'DELIVERED', 'FAILED'
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_notifications_tenant_user ON notifications(tenant_id, user_id, status);

CREATE TABLE IF NOT EXISTS notification_preferences (
    preference_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    email_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    in_app_enabled BOOLEAN NOT NULL DEFAULT TRUE,
    webhook_url VARCHAR(512),
    digest_frequency VARCHAR(32) NOT NULL DEFAULT 'DAILY', -- 'REALTIME', 'DAILY', 'WEEKLY'
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (tenant_id, user_id)
);

CREATE TABLE IF NOT EXISTS saved_searches (
    search_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL REFERENCES tenants(tenant_id) ON DELETE CASCADE,
    user_id VARCHAR(64) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    query VARCHAR(255) NOT NULL,
    filters JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_saved_searches_tenant ON saved_searches(tenant_id, user_id);

CREATE TABLE IF NOT EXISTS audit_logs (
    log_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    action VARCHAR(128) NOT NULL,
    resource_type VARCHAR(64) NOT NULL,
    resource_id VARCHAR(128),
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_tenant ON audit_logs(tenant_id, created_at DESC);

CREATE TABLE IF NOT EXISTS ai_usage_records (
    record_id VARCHAR(64) PRIMARY KEY,
    tenant_id VARCHAR(64) NOT NULL,
    user_id VARCHAR(64) NOT NULL,
    prompt_tokens INT NOT NULL DEFAULT 0,
    completion_tokens INT NOT NULL DEFAULT 0,
    total_tokens INT NOT NULL DEFAULT 0,
    model_name VARCHAR(64),
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ai_usage_tenant ON ai_usage_records(tenant_id, created_at DESC);
