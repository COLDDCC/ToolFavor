-- Keep users.id as an internal immutable key. Public display numbers are separate.
CREATE TABLE IF NOT EXISTS public_numbers (
 number INTEGER PRIMARY KEY CHECK(number BETWEEN 1 AND 999999999),
 user_id INTEGER UNIQUE REFERENCES users(id) ON DELETE SET NULL,
 tier TEXT NOT NULL DEFAULT 'standard' CHECK(tier IN ('founder','standard','premium')),
 status TEXT NOT NULL DEFAULT 'available' CHECK(status IN ('available','assigned','reserved','retired')),
 assigned_at TEXT,
 CHECK((status='assigned' AND user_id IS NOT NULL) OR (status!='assigned' AND user_id IS NULL))
);
CREATE TABLE IF NOT EXISTS number_history (
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 user_id INTEGER NOT NULL,
 number INTEGER NOT NULL,
 event TEXT NOT NULL CHECK(event IN ('assigned','replaced','retired')),
 created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- Founder #1 is reserved until the founder account is explicitly linked.
INSERT OR IGNORE INTO public_numbers(number,tier,status) VALUES(1,'founder','reserved');
-- Reserve the best-known premium patterns from the free pool.
INSERT OR IGNORE INTO public_numbers(number,tier,status) VALUES(8,'premium','reserved'),(11,'premium','reserved'),(88,'premium','reserved'),(123,'premium','reserved'),(520,'premium','reserved'),(666,'premium','reserved'),(888,'premium','reserved'),(6666,'premium','reserved'),(8888,'premium','reserved'),(77777,'premium','reserved'),(10000,'premium','reserved');
