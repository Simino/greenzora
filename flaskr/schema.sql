DROP TABLE IF EXISTS classification;
DROP TABLE IF EXISTS settings;

CREATE TABLE classification (
  uid TEXT PRIMARY KEY,             -- The UID of the paper we get from ZORA. Has the same format as a URI.
  sustainable INTEGER NOT NULL      -- The flag that tells us whether a paper was classified as sustainable or not. Since there is no boolean type in SQLite we use 1 (true) and 0 (false).
);

CREATE TABLE settings (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL,               -- The name of the setting
  value TEXT NOT NULL               -- The value of the setting
);