-- Some Notes:
-- * The collection names are maxed to 32 characters.
-- * fqids can be max 48 chars long. The longest collection is currently `motion_change_recommendation` with 28 chars. The
--   maximum is 32 chars. So 15 chars are left for ids, which means there can be (10^16)-1 ids. That are about 4.5x10^6 more ids
--   in 15 characters in comparison to (2^31)-1 for the sql INTEGER type. This should be enough.
-- * In contrast, collectionfields cna be very long in fact of structured keys. I choose 255 to be save. Maybe this can be
--   reduced in the future to save space...


-- Why doesn't postgres have a "CREATE TYPE IF NOT EXISTS"???????
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'event_type') THEN
        CREATE TYPE event_type AS ENUM ('create', 'update', 'delete', 'deletefields', 'restore', 'noop');
    ELSE
        RAISE NOTICE 'type "event_type" already exists, skipping';
    END IF;
END$$;


CREATE TABLE IF NOT EXISTS positions (
    position SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ,
    user_id INTEGER NOT NULL,
    information JSON
);

CREATE TABLE IF NOT EXISTS events (
    id BIGSERIAL PRIMARY KEY,
    position INTEGER REFERENCES positions(position) ON DELETE CASCADE,
    fqid VARCHAR(48) NOT NULL,
    type event_type NOT NULL,
    data JSONB
);
CREATE INDEX IF NOT EXISTS events_fqid_idx ON events (fqid);

CREATE TABLE IF NOT EXISTS models_lookup (
    fqid VARCHAR(48) PRIMARY KEY,
    deleted BOOLEAN NOT NULL
);

CREATE TABLE IF NOT EXISTS id_sequences (
    collection VARCHAR(32) PRIMARY KEY,
    id INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS collectionfields (
    id BIGSERIAL PRIMARY KEY,
    collectionfield VARCHAR(255) UNIQUE NOT NULL,
    position INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS collectionfields_collectionfield_idx on collectionfields (collectionfield);

CREATE TABLE IF NOT EXISTS events_to_collectionfields (
    event_id BIGINT REFERENCES events(id) ON UPDATE CASCADE ON DELETE CASCADE,
    collectionfield_id BIGINT REFERENCES collectionfields(id) ON UPDATE CASCADE ON DELETE CASCADE,
    CONSTRAINT events_to_collectionfields_pkey PRIMARY KEY (event_id, collectionfield_id)
);

CREATE TABLE IF NOT EXISTS models (
    fqid VARCHAR(48) PRIMARY KEY,
    data JSONB NOT NULL
);
