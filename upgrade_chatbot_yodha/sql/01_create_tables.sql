-- ======================================================
-- DDL — create all tables for ChatBotYodha v2
-- Compatible with PostgreSQL 14+
-- ======================================================

CREATE TABLE IF NOT EXISTS customer (
    customer_id   SERIAL PRIMARY KEY,
    party_type    VARCHAR(20),          -- Individual / Business / MKTG
    first_name    VARCHAR(50),
    last_name     VARCHAR(50),
    middle_name   VARCHAR(50),
    email         VARCHAR(100) UNIQUE,
    phone         VARCHAR(20),
    addr1         VARCHAR(200),
    addr2         VARCHAR(200),
    city          VARCHAR(100),
    state         VARCHAR(50),
    zipcode       VARCHAR(20),
    country       VARCHAR(50),
    comments      VARCHAR(500),
    telegram_chat_id BIGINT,
    created_at    TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS product (
    product_id      SERIAL PRIMARY KEY,
    product_name    VARCHAR(200) NOT NULL,
    category        VARCHAR(100),
    type            VARCHAR(50),
    version         VARCHAR(20),
    description     TEXT,
    price           NUMERIC(10,2) DEFAULT 0,
    stock_quantity  INTEGER DEFAULT 0,
    warranty_period VARCHAR(100),
    created_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sales (
    sale_id       SERIAL PRIMARY KEY,
    customer_id   INTEGER NOT NULL REFERENCES customer(customer_id),
    product_id    INTEGER NOT NULL REFERENCES product(product_id),
    quantity      INTEGER DEFAULT 1,
    sale_date     DATE,
    total_amount  NUMERIC(10,2),
    comments      VARCHAR(500)
);

CREATE TABLE IF NOT EXISTS activity (
    activity_id   SERIAL PRIMARY KEY,
    customer_id   INTEGER NOT NULL REFERENCES customer(customer_id),
    product_id    INTEGER REFERENCES product(product_id),
    sales_id      INTEGER REFERENCES sales(sale_id),
    activity_type VARCHAR(50),
    description   TEXT,
    comments      VARCHAR(500),
    activity_date TIMESTAMP DEFAULT NOW(),
    session_id    VARCHAR(100),
    url_data      VARCHAR(1000)
);

-- Indexes for common look-ups
CREATE INDEX IF NOT EXISTS idx_customer_email ON customer(email);
CREATE INDEX IF NOT EXISTS idx_customer_party ON customer(party_type);
CREATE INDEX IF NOT EXISTS idx_sales_customer ON sales(customer_id);
CREATE INDEX IF NOT EXISTS idx_activity_customer ON activity(customer_id);
CREATE INDEX IF NOT EXISTS idx_activity_session ON activity(session_id);
