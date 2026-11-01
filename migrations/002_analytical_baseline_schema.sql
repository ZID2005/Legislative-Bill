-- ============================================================================
-- 002_analytical_baseline_schema.sql
-- Legislative Intelligence & Market Impact Platform
-- Canonical PostgreSQL Migration: Analytical Baselines & Econometric Outputs
-- Strict Immutability & Statutory Firewall Enforcement
-- ============================================================================

-- ----------------------------------------------------------------------------
-- 1. Analytical Baseline Manifest Registry
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS analytical_baselines (
    baseline_id VARCHAR(64) PRIMARY KEY, -- e.g. 'production_baseline_v1'
    version VARCHAR(32) NOT NULL,        -- '1.1.0'
    sha256 VARCHAR(64) NOT NULL,         -- '50ae76039bccf2e4a671cf2ae915889e490b17404db6eb2e49e7965ecd6400b7'
    manifest_name VARCHAR(255) NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'FROZEN', -- 'FROZEN', 'ACTIVE'
    record_counts JSONB NOT NULL DEFAULT '{}'::jsonb,
    invariants JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_frozen BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    verified_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_baselines_sha256 ON analytical_baselines(sha256);

-- ----------------------------------------------------------------------------
-- 2. Predictions Storage (4,700 Central Event-Study Predictions)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS predictions (
    prediction_id VARCHAR(64) PRIMARY KEY,
    baseline_id VARCHAR(64) NOT NULL REFERENCES analytical_baselines(baseline_id),
    bill_id VARCHAR(128) NOT NULL REFERENCES bills(bill_id),
    company_isin VARCHAR(16) NOT NULL REFERENCES companies(isin),
    company_name VARCHAR(255),
    company_symbol VARCHAR(32),
    event_window VARCHAR(32) NOT NULL,
    predicted_direction VARCHAR(32) NOT NULL, -- 'POSITIVE', 'NEGATIVE', 'NEUTRAL'
    direction_probability JSONB NOT NULL DEFAULT '{}'::jsonb,
    predicted_market_moving BOOLEAN NOT NULL DEFAULT FALSE,
    market_moving_probability NUMERIC(6, 4) NOT NULL DEFAULT 0.0,
    predicted_impact_strength VARCHAR(32) NOT NULL DEFAULT 'MEDIUM',
    impact_probabilities JSONB NOT NULL DEFAULT '{}'::jsonb,
    predicted_confidence VARCHAR(32) NOT NULL DEFAULT 'MEDIUM',
    confidence_probability JSONB NOT NULL DEFAULT '{}'::jsonb,
    model_confidence NUMERIC(6, 4) NOT NULL DEFAULT 0.0,
    anticipation_class VARCHAR(64) DEFAULT 'MODERATE_EVIDENCE',
    anticipation_score NUMERIC(6, 4) DEFAULT 0.0,
    model_name JSONB NOT NULL DEFAULT '{}'::jsonb,
    model_version VARCHAR(32) NOT NULL DEFAULT 'v1.0',
    feature_version VARCHAR(32) NOT NULL DEFAULT 'v1.0',
    prediction_timestamp TIMESTAMPTZ NOT NULL,
    decision_reason TEXT,
    expected_impact_estimate TEXT,
    risk_indicators JSONB NOT NULL DEFAULT '[]'::jsonb,
    data_quality_status VARCHAR(32) NOT NULL DEFAULT 'VALID',
    is_frozen BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Statutory State Firewall Constraint: Absolutely NO predictions for State Acts
    CONSTRAINT chk_predictions_state_firewall
        CHECK (bill_id NOT LIKE 'ap_%' AND bill_id NOT LIKE 'ka_%' AND bill_id NOT LIKE 'kl_%' AND bill_id NOT LIKE 'ts_%'),

    -- Authoritative Event Horizons Constraint
    CONSTRAINT chk_predictions_event_windows
        CHECK (event_window IN ('[-1,+1]', '[-3,+3]', '[-5,+5]', '[-5,+10]', '[-10,+10]', '[-20,+20]', '[-2,+2]'))
);

CREATE INDEX IF NOT EXISTS idx_predictions_bill ON predictions(bill_id);
CREATE INDEX IF NOT EXISTS idx_predictions_company ON predictions(company_isin);
CREATE INDEX IF NOT EXISTS idx_predictions_window ON predictions(event_window);
CREATE INDEX IF NOT EXISTS idx_predictions_direction ON predictions(predicted_direction);
CREATE INDEX IF NOT EXISTS idx_predictions_market_moving ON predictions(predicted_market_moving);
CREATE INDEX IF NOT EXISTS idx_predictions_baseline ON predictions(baseline_id);

-- ----------------------------------------------------------------------------
-- 3. Decision Support Storage (4,700 Central Recommendations)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS decisions (
    decision_id VARCHAR(64) PRIMARY KEY,
    baseline_id VARCHAR(64) NOT NULL REFERENCES analytical_baselines(baseline_id),
    bill_id VARCHAR(128) NOT NULL REFERENCES bills(bill_id),
    company_isin VARCHAR(16) NOT NULL REFERENCES companies(isin),
    event_window VARCHAR(32) NOT NULL,
    predicted_direction VARCHAR(32) NOT NULL,
    direction_probability JSONB NOT NULL DEFAULT '{}'::jsonb,
    market_moving_probability NUMERIC(6, 4) NOT NULL DEFAULT 0.0,
    predicted_impact_strength VARCHAR(32) NOT NULL DEFAULT 'MEDIUM',
    confidence_probability JSONB NOT NULL DEFAULT '{}'::jsonb,
    anticipation_class VARCHAR(64) DEFAULT 'MODERATE_EVIDENCE',
    anticipation_score NUMERIC(6, 4) DEFAULT 0.0,
    impact_score NUMERIC(6, 4) NOT NULL DEFAULT 0.0,
    risk_score NUMERIC(6, 4) NOT NULL DEFAULT 0.0,
    risk_category VARCHAR(32) NOT NULL DEFAULT 'MODERATE', -- 'LOW', 'MODERATE', 'HIGH', 'CRITICAL'
    pricing_in_risk VARCHAR(32) NOT NULL DEFAULT 'LOW',
    investor_summary TEXT,
    business_summary TEXT,
    public_summary TEXT,
    decision_reason TEXT,
    model_version VARCHAR(32) NOT NULL DEFAULT 'v1.0',
    feature_version VARCHAR(32) NOT NULL DEFAULT 'v1.0',
    is_frozen BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,

    -- Statutory State Firewall Constraint
    CONSTRAINT chk_decisions_state_firewall
        CHECK (bill_id NOT LIKE 'ap_%' AND bill_id NOT LIKE 'ka_%' AND bill_id NOT LIKE 'kl_%' AND bill_id NOT LIKE 'ts_%')
);

CREATE INDEX IF NOT EXISTS idx_decisions_bill ON decisions(bill_id);
CREATE INDEX IF NOT EXISTS idx_decisions_company ON decisions(company_isin);
CREATE INDEX IF NOT EXISTS idx_decisions_window ON decisions(event_window);
CREATE INDEX IF NOT EXISTS idx_decisions_risk ON decisions(risk_category);

-- ----------------------------------------------------------------------------
-- 4. Anticipation Analytics Storage (940 Bill-Company Pairs)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS anticipation_scores (
    score_id VARCHAR(64) PRIMARY KEY, -- e.g. 'ant_the-banking-laws-amendment-bill-2024_INE062A01020'
    baseline_id VARCHAR(64) NOT NULL REFERENCES analytical_baselines(baseline_id),
    bill_id VARCHAR(128) NOT NULL REFERENCES bills(bill_id),
    company_isin VARCHAR(16) NOT NULL REFERENCES companies(isin),
    company_name VARCHAR(255),
    -- Task 8.29 Decoupled Epistemic Dimensions:
    market_signal_level VARCHAR(32) NOT NULL DEFAULT 'MODERATE',   -- 'STRONG', 'MODERATE', 'WEAK', 'NEUTRAL'
    market_signal_score NUMERIC(6, 4) NOT NULL DEFAULT 0.0,
    public_signal_level VARCHAR(32) NOT NULL DEFAULT 'MODERATE',   -- 'STRONG', 'MODERATE', 'WEAK', 'NEUTRAL'
    evidence_strength VARCHAR(32) NOT NULL DEFAULT 'CONFIRMED',    -- 'SUBSTANTIVE', 'MODERATE', 'MINIMAL', 'CONFIRMED'
    combined_classification VARCHAR(64) NOT NULL DEFAULT 'SUBSTANTIAL_CONCURRENT',
    anticipation_score NUMERIC(6, 4) NOT NULL DEFAULT 0.0,
    evidence_items_count INT NOT NULL DEFAULT 0,
    evidence_context JSONB NOT NULL DEFAULT '{}'::jsonb,
    is_frozen BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (bill_id, company_isin)
);

CREATE INDEX IF NOT EXISTS idx_anticipation_bill ON anticipation_scores(bill_id);
CREATE INDEX IF NOT EXISTS idx_anticipation_company ON anticipation_scores(company_isin);

-- ----------------------------------------------------------------------------
-- 5. Stakeholder Reports Storage (14,100 Frozen Analytical + User-Generated)
-- ----------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS stakeholder_reports (
    report_id VARCHAR(64) PRIMARY KEY,
    baseline_id VARCHAR(64) REFERENCES analytical_baselines(baseline_id),
    bill_id VARCHAR(128) NOT NULL REFERENCES bills(bill_id),
    company_isin VARCHAR(16) REFERENCES companies(isin),
    stakeholder_type VARCHAR(32) NOT NULL, -- 'INVESTOR', 'BUSINESS', 'PUBLIC', 'POLICYMAKER'
    report_type VARCHAR(32) NOT NULL DEFAULT 'FROZEN_ANALYTICAL', -- 'FROZEN_ANALYTICAL' vs 'USER_GENERATED'
    executive_summary TEXT NOT NULL,
    risk_factors JSONB NOT NULL DEFAULT '[]'::jsonb,
    opportunity_areas JSONB NOT NULL DEFAULT '[]'::jsonb,
    recommended_actions JSONB NOT NULL DEFAULT '[]'::jsonb,
    epistemic_disclaimer TEXT,
    is_frozen BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reports_bill ON stakeholder_reports(bill_id);
CREATE INDEX IF NOT EXISTS idx_reports_company ON stakeholder_reports(company_isin);
CREATE INDEX IF NOT EXISTS idx_reports_type ON stakeholder_reports(stakeholder_type, report_type);

-- ----------------------------------------------------------------------------
-- 6. Immutability Protection Functions & Triggers
-- ----------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION enforce_frozen_immutability()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.is_frozen = TRUE THEN
        RAISE EXCEPTION 'IMMUTABLE_FROZEN_RECORD_VIOLATION: Table % record % cannot be updated or deleted because it is part of the frozen analytical baseline.', TG_TABLE_NAME, OLD;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Attach Immutability Triggers
DROP TRIGGER IF EXISTS trg_immutability_baselines ON analytical_baselines;
CREATE TRIGGER trg_immutability_baselines
BEFORE UPDATE OR DELETE ON analytical_baselines
FOR EACH ROW EXECUTE FUNCTION enforce_frozen_immutability();

DROP TRIGGER IF EXISTS trg_immutability_predictions ON predictions;
CREATE TRIGGER trg_immutability_predictions
BEFORE UPDATE OR DELETE ON predictions
FOR EACH ROW EXECUTE FUNCTION enforce_frozen_immutability();

DROP TRIGGER IF EXISTS trg_immutability_decisions ON decisions;
CREATE TRIGGER trg_immutability_decisions
BEFORE UPDATE OR DELETE ON decisions
FOR EACH ROW EXECUTE FUNCTION enforce_frozen_immutability();

DROP TRIGGER IF EXISTS trg_immutability_anticipation ON anticipation_scores;
CREATE TRIGGER trg_immutability_anticipation
BEFORE UPDATE OR DELETE ON anticipation_scores
FOR EACH ROW EXECUTE FUNCTION enforce_frozen_immutability();

DROP TRIGGER IF EXISTS trg_immutability_reports ON stakeholder_reports;
CREATE TRIGGER trg_immutability_reports
BEFORE UPDATE OR DELETE ON stakeholder_reports
FOR EACH ROW EXECUTE FUNCTION enforce_frozen_immutability();
