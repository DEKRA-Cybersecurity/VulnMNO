-- Generated from app.models via Base.metadata. Phase 1 schema.


CREATE TABLE audit_events (
	id INTEGER NOT NULL, 
	event_type VARCHAR(64) NOT NULL, 
	actor_id VARCHAR(32), 
	target_type VARCHAR(32), 
	target_id VARCHAR(64), 
	payload JSON NOT NULL, 
	ip_address VARCHAR(45), 
	timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id)
);

CREATE INDEX ix_audit_events_actor_id_timestamp ON audit_events (actor_id, timestamp);

CREATE INDEX ix_audit_events_event_type ON audit_events (event_type);


CREATE TABLE customers (
	id INTEGER NOT NULL, 
	public_id VARCHAR(32) NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	email VARCHAR(160), 
	primary_msisdn VARCHAR(20) NOT NULL, 
	account_type VARCHAR(8) NOT NULL, 
	status VARCHAR(9) NOT NULL, 
	loyalty_tier VARCHAR(8) NOT NULL, 
	password_hash VARCHAR(255) NOT NULL, 
	otp_enrolled BOOLEAN NOT NULL, 
	otp_fixed_code VARCHAR(6), 
	last_login_at DATETIME, 
	billing_address JSON, 
	notification_preferences JSON NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	deleted_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (public_id), 
	UNIQUE (primary_msisdn)
);


CREATE TABLE plans (
	id INTEGER NOT NULL, 
	public_id VARCHAR(64) NOT NULL, 
	name VARCHAR(120) NOT NULL, 
	description VARCHAR(500), 
	monthly_price NUMERIC(12, 2) NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	data_limit_mb INTEGER NOT NULL, 
	voice_limit_min INTEGER NOT NULL, 
	sms_limit INTEGER NOT NULL, 
	category VARCHAR(8) NOT NULL, 
	eligibility_rules JSON NOT NULL, 
	available_services JSON NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (public_id)
);


CREATE TABLE products (
	id INTEGER NOT NULL, 
	public_id VARCHAR(64) NOT NULL, 
	name VARCHAR(160) NOT NULL, 
	description VARCHAR(500), 
	category VARCHAR(12) NOT NULL, 
	price NUMERIC(12, 2) NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	validity_days INTEGER, 
	eligible_plans JSON NOT NULL, 
	featured BOOLEAN NOT NULL, 
	availability VARCHAR(9) NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (public_id)
);


CREATE TABLE promotions (
	id INTEGER NOT NULL, 
	public_id VARCHAR(64) NOT NULL, 
	name VARCHAR(160) NOT NULL, 
	description VARCHAR(500), 
	discount_type VARCHAR(7) NOT NULL, 
	discount_value NUMERIC(10, 2) NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	starts_at DATETIME NOT NULL, 
	ends_at DATETIME NOT NULL, 
	eligibility_rules JSON NOT NULL, 
	eligible_product_ids JSON NOT NULL, 
	combinable BOOLEAN NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (public_id)
);


CREATE TABLE sim_profiles (
	id INTEGER NOT NULL, 
	public_id VARCHAR(32) NOT NULL, 
	iccid VARCHAR(22) NOT NULL, 
	imsi_alias VARCHAR(32) NOT NULL, 
	sim_type VARCHAR(8) NOT NULL, 
	status VARCHAR(9) NOT NULL, 
	activation_date DATE NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	deleted_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (public_id), 
	UNIQUE (iccid)
);


CREATE TABLE accounts (
	id INTEGER NOT NULL, 
	public_id VARCHAR(32) NOT NULL, 
	customer_id INTEGER NOT NULL, 
	account_type VARCHAR(8) NOT NULL, 
	billing_status VARCHAR(13) NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (public_id), 
	UNIQUE (customer_id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE RESTRICT
);

CREATE INDEX ix_accounts_customer_id ON accounts (customer_id);


CREATE TABLE coupons (
	id INTEGER NOT NULL, 
	code VARCHAR(64) NOT NULL, 
	promotion_id INTEGER NOT NULL, 
	status VARCHAR(9) NOT NULL, 
	usage_limit INTEGER NOT NULL, 
	usage_count INTEGER NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (code), 
	FOREIGN KEY(promotion_id) REFERENCES promotions (id) ON DELETE CASCADE
);

CREATE INDEX ix_coupons_promotion_id ON coupons (promotion_id);


CREATE TABLE customer_services (
	id INTEGER NOT NULL, 
	customer_id INTEGER NOT NULL, 
	service_id VARCHAR(64) NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE CASCADE
);

CREATE INDEX ix_customer_services_customer_id ON customer_services (customer_id);


CREATE TABLE device_tokens (
	id INTEGER NOT NULL, 
	customer_id INTEGER NOT NULL, 
	token VARCHAR(4096) NOT NULL, 
	platform VARCHAR(7) NOT NULL, 
	app_version VARCHAR(40), 
	last_seen_at DATETIME, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE CASCADE, 
	UNIQUE (token)
);

CREATE INDEX ix_device_tokens_customer_id ON device_tokens (customer_id);


CREATE TABLE idempotency_keys (
	id INTEGER NOT NULL, 
	customer_id INTEGER NOT NULL, 
	"key" VARCHAR(128) NOT NULL, 
	endpoint VARCHAR(128) NOT NULL, 
	request_hash VARCHAR(64) NOT NULL, 
	response_status INTEGER NOT NULL, 
	response_body VARCHAR(8000) NOT NULL, 
	expires_at DATETIME NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT uq_idempotency_scope UNIQUE (customer_id, endpoint, "key"), 
	FOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE CASCADE
);

CREATE INDEX ix_idempotency_keys_expires_at ON idempotency_keys (expires_at);


CREATE TABLE mobile_lines (
	id INTEGER NOT NULL, 
	public_id VARCHAR(32) NOT NULL, 
	msisdn VARCHAR(20) NOT NULL, 
	customer_id INTEGER NOT NULL, 
	plan_id INTEGER, 
	sim_id INTEGER, 
	status VARCHAR(10) NOT NULL, 
	activated_at DATE, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	deleted_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (public_id), 
	UNIQUE (msisdn), 
	FOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE RESTRICT, 
	FOREIGN KEY(plan_id) REFERENCES plans (id) ON DELETE SET NULL, 
	UNIQUE (sim_id), 
	FOREIGN KEY(sim_id) REFERENCES sim_profiles (id) ON DELETE SET NULL
);

CREATE INDEX ix_mobile_lines_customer_id ON mobile_lines (customer_id);

CREATE INDEX ix_mobile_lines_plan_id ON mobile_lines (plan_id);


CREATE TABLE notifications (
	id INTEGER NOT NULL, 
	public_id VARCHAR(32) NOT NULL, 
	customer_id INTEGER NOT NULL, 
	channel VARCHAR(6) NOT NULL, 
	message_type VARCHAR(21) NOT NULL, 
	title VARCHAR(160) NOT NULL, 
	body VARCHAR(2000) NOT NULL, 
	read_at DATETIME, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (public_id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE CASCADE
);

CREATE INDEX ix_notifications_customer_id_created_at ON notifications (customer_id, created_at);


CREATE TABLE otp_challenges (
	id INTEGER NOT NULL, 
	customer_id INTEGER NOT NULL, 
	challenge_token VARCHAR(64) NOT NULL, 
	code_hash VARCHAR(64) NOT NULL, 
	attempts INTEGER NOT NULL, 
	expires_at DATETIME NOT NULL, 
	consumed_at DATETIME, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE CASCADE, 
	UNIQUE (challenge_token)
);

CREATE INDEX ix_otp_challenges_expires_at ON otp_challenges (expires_at);


CREATE TABLE password_resets (
	id INTEGER NOT NULL, 
	customer_id INTEGER NOT NULL, 
	code_hash VARCHAR(64) NOT NULL, 
	expires_at DATETIME NOT NULL, 
	consumed_at DATETIME, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE CASCADE
);

CREATE INDEX ix_password_resets_expires_at ON password_resets (expires_at);


CREATE TABLE plan_changes (
	id INTEGER NOT NULL, 
	public_id VARCHAR(32) NOT NULL, 
	customer_id INTEGER NOT NULL, 
	from_plan_id INTEGER, 
	to_plan_id INTEGER NOT NULL, 
	mode VARCHAR(9) NOT NULL, 
	status VARCHAR(9) NOT NULL, 
	effective_date DATE, 
	applied_at DATETIME, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (public_id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE RESTRICT, 
	FOREIGN KEY(from_plan_id) REFERENCES plans (id) ON DELETE RESTRICT, 
	FOREIGN KEY(to_plan_id) REFERENCES plans (id) ON DELETE RESTRICT
);

CREATE INDEX ix_plan_changes_customer_id ON plan_changes (customer_id);

CREATE INDEX ix_plan_changes_status ON plan_changes (status);


CREATE TABLE purchases (
	id INTEGER NOT NULL, 
	public_id VARCHAR(32) NOT NULL, 
	customer_id INTEGER NOT NULL, 
	product_id INTEGER NOT NULL, 
	promotion_id INTEGER, 
	status VARCHAR(9) NOT NULL, 
	original_price NUMERIC(12, 2) NOT NULL, 
	final_price NUMERIC(12, 2) NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	provisioning_status VARCHAR(7) NOT NULL, 
	provisioning_activated_at DATETIME, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (public_id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE RESTRICT, 
	FOREIGN KEY(product_id) REFERENCES products (id) ON DELETE RESTRICT, 
	FOREIGN KEY(promotion_id) REFERENCES promotions (id) ON DELETE SET NULL
);

CREATE INDEX ix_purchases_customer_id_created_at ON purchases (customer_id, created_at);

CREATE INDEX ix_purchases_status ON purchases (status);


CREATE TABLE refresh_tokens (
	id INTEGER NOT NULL, 
	customer_id INTEGER NOT NULL, 
	token_hash VARCHAR(64) NOT NULL, 
	parent_id INTEGER, 
	access_jti VARCHAR(32) NOT NULL, 
	expires_at DATETIME NOT NULL, 
	revoked_at DATETIME, 
	revoked_reason VARCHAR(64), 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE CASCADE, 
	UNIQUE (token_hash), 
	FOREIGN KEY(parent_id) REFERENCES refresh_tokens (id) ON DELETE SET NULL
);

CREATE INDEX ix_refresh_tokens_customer_id ON refresh_tokens (customer_id);

CREATE INDEX ix_refresh_tokens_expires_at ON refresh_tokens (expires_at);


CREATE TABLE support_tickets (
	id INTEGER NOT NULL, 
	public_id VARCHAR(32) NOT NULL, 
	customer_id INTEGER NOT NULL, 
	topic VARCHAR(9) NOT NULL, 
	description VARCHAR(4000) NOT NULL, 
	status VARCHAR(7) NOT NULL, 
	last_updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	deleted_at DATETIME, 
	PRIMARY KEY (id), 
	UNIQUE (public_id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE RESTRICT
);

CREATE INDEX ix_support_tickets_customer_id_created_at ON support_tickets (customer_id, created_at);

CREATE INDEX ix_support_tickets_status ON support_tickets (status);


CREATE TABLE balances (
	id INTEGER NOT NULL, 
	account_id INTEGER NOT NULL, 
	amount NUMERIC(12, 2) NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	last_updated DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (account_id), 
	FOREIGN KEY(account_id) REFERENCES accounts (id) ON DELETE CASCADE
);


CREATE TABLE invoices (
	id INTEGER NOT NULL, 
	public_id VARCHAR(32) NOT NULL, 
	account_id INTEGER NOT NULL, 
	period VARCHAR(7) NOT NULL, 
	total_amount NUMERIC(12, 2) NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	status VARCHAR(7) NOT NULL, 
	issued_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (public_id), 
	FOREIGN KEY(account_id) REFERENCES accounts (id) ON DELETE RESTRICT
);

CREATE INDEX ix_invoices_account_id_period ON invoices (account_id, period);

CREATE INDEX ix_invoices_status ON invoices (status);


CREATE TABLE refunds (
	id INTEGER NOT NULL, 
	public_id VARCHAR(32) NOT NULL, 
	customer_id INTEGER NOT NULL, 
	target_type VARCHAR(8) NOT NULL, 
	target_public_id VARCHAR(32) NOT NULL, 
	reason VARCHAR(500) NOT NULL, 
	status VARCHAR(8) NOT NULL, 
	ticket_id INTEGER, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (public_id), 
	FOREIGN KEY(customer_id) REFERENCES customers (id) ON DELETE RESTRICT, 
	FOREIGN KEY(ticket_id) REFERENCES support_tickets (id) ON DELETE SET NULL
);

CREATE INDEX ix_refunds_customer_id ON refunds (customer_id);


CREATE TABLE ticket_attachments (
	id INTEGER NOT NULL, 
	public_id VARCHAR(32) NOT NULL, 
	ticket_id INTEGER NOT NULL, 
	filename VARCHAR(255) NOT NULL, 
	size_bytes INTEGER NOT NULL, 
	content_type VARCHAR(120) NOT NULL, 
	storage_path VARCHAR(500) NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (public_id), 
	FOREIGN KEY(ticket_id) REFERENCES support_tickets (id) ON DELETE CASCADE
);

CREATE INDEX ix_ticket_attachments_ticket_id ON ticket_attachments (ticket_id);


CREATE TABLE ticket_messages (
	id INTEGER NOT NULL, 
	public_id VARCHAR(32) NOT NULL, 
	ticket_id INTEGER NOT NULL, 
	author_role VARCHAR(8) NOT NULL, 
	author_display_name VARCHAR(120) NOT NULL, 
	body VARCHAR(4000) NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (public_id), 
	FOREIGN KEY(ticket_id) REFERENCES support_tickets (id) ON DELETE CASCADE
);

CREATE INDEX ix_ticket_messages_ticket_id ON ticket_messages (ticket_id);


CREATE TABLE usage_records (
	id INTEGER NOT NULL, 
	public_id VARCHAR(32) NOT NULL, 
	line_id INTEGER NOT NULL, 
	type VARCHAR(7) NOT NULL, 
	direction VARCHAR(8), 
	destination VARCHAR(40), 
	started_at DATETIME NOT NULL, 
	duration_seconds INTEGER, 
	volume_megabytes NUMERIC(12, 3), 
	country VARCHAR(2), 
	network_type VARCHAR(16), 
	roaming BOOLEAN NOT NULL, 
	cost NUMERIC(12, 2) NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (public_id), 
	FOREIGN KEY(line_id) REFERENCES mobile_lines (id) ON DELETE RESTRICT
);

CREATE INDEX ix_usage_records_type ON usage_records (type);

CREATE INDEX ix_usage_records_line_id_started_at ON usage_records (line_id, started_at);


CREATE TABLE invoice_line_items (
	id INTEGER NOT NULL, 
	invoice_id INTEGER NOT NULL, 
	description VARCHAR(255) NOT NULL, 
	amount NUMERIC(12, 2) NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	related_product_public_id VARCHAR(64), 
	related_plan_public_id VARCHAR(64), 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(invoice_id) REFERENCES invoices (id) ON DELETE CASCADE
);

CREATE INDEX ix_invoice_line_items_invoice_id ON invoice_line_items (invoice_id);


CREATE TABLE transactions (
	id INTEGER NOT NULL, 
	public_id VARCHAR(32) NOT NULL, 
	account_id INTEGER NOT NULL, 
	type VARCHAR(10) NOT NULL, 
	amount NUMERIC(12, 2) NOT NULL, 
	currency VARCHAR(3) NOT NULL, 
	balance_after NUMERIC(12, 2) NOT NULL, 
	related_purchase_id INTEGER, 
	related_invoice_id INTEGER, 
	timestamp DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	updated_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	UNIQUE (public_id), 
	FOREIGN KEY(account_id) REFERENCES accounts (id) ON DELETE RESTRICT, 
	FOREIGN KEY(related_purchase_id) REFERENCES purchases (id) ON DELETE SET NULL, 
	FOREIGN KEY(related_invoice_id) REFERENCES invoices (id) ON DELETE SET NULL
);

CREATE INDEX ix_transactions_account_id_timestamp ON transactions (account_id, timestamp);

CREATE INDEX ix_transactions_type ON transactions (type);
