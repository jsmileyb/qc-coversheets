DO $$
DECLARE
    r RECORD;
BEGIN
    FOR r IN (
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'qc_coversheet'
    )
    LOOP
        EXECUTE 'TRUNCATE TABLE qc_coversheet.' 
                || quote_ident(r.tablename) 
                || ' RESTART IDENTITY CASCADE';
    END LOOP;
END $$;