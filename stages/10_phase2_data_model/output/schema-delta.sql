-- Phase 2 delta: new tables + column additions on existing tables.
-- Generated from app.models via Base.metadata.



CREATE TABLE admin_users (
	id INTEGER NOT NULL, 
	public_id VARCHAR(32) NOT NULL, 
	username VARCHAR(64) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	full_name VARCHAR(120) NOT NULL, 
	role VARCHAR(16) NOT NULL, 
	status VARCHAR(11) NOT NULL, 
	last_login_at DATETIME, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	deleted_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (public_id), 
	UNIQUE (username)
);

CREATE INDEX ix_admin_users_username ON admin_users (username);


CREATE TABLE loyalty_tiers (
	id INTEGER NOT NULL, 
	name VARCHAR(8) NOT NULL, 
	threshold_lifetime_points INTEGER NOT NULL, 
	multiplier NUMERIC(4, 2) NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (name)
);


CREATE TABLE loyalty_accounts (
	id INTEGER NOT NULL, 
	public_id VARCHAR(32) NOT NULL, 
	customer_id INTEGER NOT NULL, 
	points INTEGER NOT NULL, 
	lifetime_points INTEGER NOT NULL, 
	tier VARCHAR(8) NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (public_id), 
	UNIQUE (customer_id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE CASCADE
);

CREATE INDEX ix_loyalty_accounts_customer_id ON loyalty_accounts (customer_id);


CREATE TABLE loyalty_transactions (
	id INTEGER NOT NULL, 
	public_id VARCHAR(32) NOT NULL, 
	account_id INTEGER NOT NULL, 
	delta INTEGER NOT NULL, 
	balance_after INTEGER NOT NULL, 
	reason VARCHAR(13) NOT NULL, 
	related_purchase_id INTEGER, 
	timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (public_id), 
	FOREIGN KEY(account_id) REFERENCES loyalty_accounts (id) ON DELETE CASCADE, 
	FOREIGN KEY(related_purchase_id) REFERENCES purchases (id) ON DELETE SET NULL
);

CREATE INDEX ix_loyalty_tx_account_id_ts ON loyalty_transactions (account_id, timestamp);



-- ALTER additions on existing Phase-1 tables:

ALTER TABLE notifications ADD COLUMN delivery_status VARCHAR(8) NOT NULL DEFAULT 'queued';

ALTER TABLE notifications ADD COLUMN delivered_at DATETIME;

ALTER TABLE notifications ADD COLUMN provider_message_id VARCHAR(255);

ALTER TABLE transactions ADD COLUMN gateway_charge_id VARCHAR(128);

ALTER TABLE purchases ADD COLUMN provisioning_id VARCHAR(128);
