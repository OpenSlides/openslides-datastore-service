CREATE OR REPLACE FUNCTION rndnr(int, int)
RETURNS int AS $function$
    SELECT (floor(random()*($2-$1+1))+$1)::int;
$function$ LANGUAGE SQL;

-- https://gist.github.com/marcocitus/dd315960d5923ad3f4d26b105618ed58
CREATE OR REPLACE FUNCTION generate_data(int)
RETURNS jsonb AS $function$
        SELECT ('{'||string_agg(format('"%s":"%s"',md5(random()::text),md5(random()::text)),',') ||'}')::jsonb
        FROM generate_series(1,$1);
$function$ LANGUAGE sql;

CREATE OR REPLACE FUNCTION generate_fields(count int, seed int)
RETURNS jsonb AS $function$
        SELECT ('[' || string_agg(chr(rndnr(65,90)),',') || ']')::jsonb
        FROM generate_series(1,$1);
$function$ LANGUAGE sql;


DO $$
DECLARE
    fields text[] = array['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'];
    collections text[] = ARRAY['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z'];
    types text[] = array['create', 'update', 'delete', 'deletefields', 'restore', 'noop'];
BEGIN
    --- WARNING: Uncommenting this takes a loooong time ---
    -- INSERT INTO events
    --     (position, fqid, type, data)
    -- SELECT
    --     rndnr(0,99999999),
    --     format('collection/%s', i % 100000 + 1), -- 100 events per fqid
    --     type[i % 6 + 1],
    --     (select generate_data(50)), -- data can be the same for all events, is not accessed in the tests
    -- FROM generate_series(0,9999999) s(i);    -- 10.000.000 events

    ALTER SEQUENCE collectionfields_id_seq RESTART WITH 1;
    INSERT INTO collectionfields
        (collectionfield, position)
    SELECT
        format('%s/%s', collections[i / 26 + 1], fields[i % 26 + 1]),
        rndnr(0,99999999)
    FROM generate_series(0,675) s(i); -- 26x26=676 combinations
    RAISE NOTICE 'collectionfields finished';

    INSERT INTO events_to_collectionfields
        (event_id, collectionfield_id)
    SELECT
        i % 1000000 + 1,
        i % 676 + 1
    FROM generate_series(0,9999999) s(i); -- 10.000.000 entries, each event has 10 fields (only the first 1.000.000 events have fields)
    --- Measured time for last 2 insert statements together (first one commented out):
    --- 100.000 entries:    3.7s
    --- 1.000.000 entries:  38s
    --- 10.000.000 entries: 6m37s (397s)
END$$;