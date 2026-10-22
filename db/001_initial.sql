-- Initial schema for the single-household application.
-- Run as the backend database owner; never expose its credentials to the browser.
BEGIN;


CREATE TABLE IF NOT EXISTS households (
	id VARCHAR NOT NULL, 
	revision INTEGER NOT NULL, 
	preferences JSON NOT NULL, 
	PRIMARY KEY (id)
)

;

ALTER TABLE households ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE households FROM PUBLIC;

REVOKE ALL ON TABLE households FROM anon, authenticated;


CREATE TABLE IF NOT EXISTS inventory_batches (
	id VARCHAR NOT NULL, 
	household_id VARCHAR NOT NULL, 
	ingredient_id VARCHAR NOT NULL, 
	quantity FLOAT NOT NULL, 
	unit VARCHAR NOT NULL, 
	created_at VARCHAR NOT NULL, 
	expires_on VARCHAR, 
	source VARCHAR NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT nonnegative_batch_quantity CHECK (quantity >= 0), 
	FOREIGN KEY(household_id) REFERENCES households (id)
)

;

ALTER TABLE inventory_batches ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE inventory_batches FROM PUBLIC;

REVOKE ALL ON TABLE inventory_batches FROM anon, authenticated;


CREATE TABLE IF NOT EXISTS inventory_events (
	id VARCHAR NOT NULL, 
	household_id VARCHAR NOT NULL, 
	created_at VARCHAR NOT NULL, 
	kind VARCHAR NOT NULL, 
	payload JSON NOT NULL, 
	changes JSON NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(household_id) REFERENCES households (id)
)

;

ALTER TABLE inventory_events ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE inventory_events FROM PUBLIC;

REVOKE ALL ON TABLE inventory_events FROM anon, authenticated;


CREATE TABLE IF NOT EXISTS plans (
	id VARCHAR NOT NULL, 
	household_id VARCHAR NOT NULL, 
	created_at VARCHAR NOT NULL, 
	opening_revision INTEGER NOT NULL, 
	parameters JSON NOT NULL, 
	result JSON NOT NULL, 
	receipts_confirmed INTEGER NOT NULL, 
	archived INTEGER NOT NULL, 
	meal_status JSON NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(household_id) REFERENCES households (id)
)

;

ALTER TABLE plans ENABLE ROW LEVEL SECURITY;

REVOKE ALL ON TABLE plans FROM PUBLIC;

REVOKE ALL ON TABLE plans FROM anon, authenticated;

COMMIT;
