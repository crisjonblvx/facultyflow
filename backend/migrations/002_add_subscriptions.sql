-- ReadySetClass Subscription System
-- Migration 002: Add subscription tracking

-- Add subscription columns to users table
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_tier VARCHAR(20) DEFAULT 'trial' CHECK (subscription_tier IN ('trial', 'pro', 'team', 'enterprise'));
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_status VARCHAR(20) DEFAULT 'active' CHECK (subscription_status IN ('active', 'canceled', 'past_due', 'trialing'));
ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_customer_id VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS stripe_subscription_id VARCHAR(255);
ALTER TABLE users ADD COLUMN IF NOT EXISTS trial_ends_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS subscription_ends_at TIMESTAMP;
ALTER TABLE users ADD COLUMN IF NOT EXISTS ai_generations_this_month INTEGER DEFAULT 0;
ALTER TABLE users ADD COLUMN IF NOT EXISTS billing_cycle_start TIMESTAMP;

-- Create subscription_plans table (for reference)
CREATE TABLE IF NOT EXISTS subscription_plans (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    display_name VARCHAR(100) NOT NULL,
    price_monthly DECIMAL(10, 2) NOT NULL,
    price_yearly DECIMAL(10, 2),
    stripe_price_id_monthly VARCHAR(255),
    stripe_price_id_yearly VARCHAR(255),
    ai_generations_limit INTEGER,  -- NULL = unlimited
    max_users INTEGER DEFAULT 1,
    features JSONB,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Insert default subscription plans
INSERT INTO subscription_plans (name, display_name, price_monthly, price_yearly, ai_generations_limit, max_users, features) VALUES
('trial', 'Free Trial', 0.00, 0.00, 50, 1, '{"duration_days": 14, "support": "email"}'),
('pro', 'Pro', 29.00, 290.00, NULL, 1, '{"ai_generations": "unlimited", "priority_support": true, "grade_levels": true}'),
('team', 'Team', 99.00, 990.00, NULL, 10, '{"ai_generations": "unlimited", "priority_support": true, "grade_levels": true, "team_sharing": true, "admin_dashboard": true}'),
('enterprise', 'Enterprise', 299.00, 2990.00, NULL, NULL, '{"ai_generations": "unlimited", "priority_support": true, "grade_levels": true, "team_sharing": true, "admin_dashboard": true, "custom_branding": true, "dedicated_support": true}')
ON CONFLICT (name) DO NOTHING;

-- Create payment_transactions table
CREATE TABLE IF NOT EXISTS payment_transactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
    stripe_payment_intent_id VARCHAR(255),
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(20),
    description TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_users_stripe_customer ON users(stripe_customer_id);
CREATE INDEX IF NOT EXISTS idx_users_subscription_tier ON users(subscription_tier);
CREATE INDEX IF NOT EXISTS idx_payment_transactions_user ON payment_transactions(user_id);

-- Success message
SELECT 'Subscription tables created successfully!' as message;
