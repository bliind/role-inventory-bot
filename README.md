# role-inventory-bot

```sql
CREATE TABLE inventory(
    id TEXT PRIMARY KEY NOT NULL,
    user_id INT,
    roles TEXT
);

CREATE TABLE gamba(
    id TEXT PRIMARY KEY NOT NULL,
    user_id INT,
    datestamp INT,
    award TEXT
);

CREATE TABLE hot_hour(
    hour INT,
    active INT,
    odds INT
);
INSERT INTO hot_hour (hour, active, odds) VALUES (15, 0, 6);

CREATE TABLE timed_role (
    role_id INT,
    expire_days INT
);

CREATE TABLE timed_role_user (
    user_id INT,
    role_id INT,
    date_acquired INT
);

CREATE TABLE sr_role (
    role_name TEXT,
    role_id INT
);
CREATE TABLE no_xp_role (
    role_id INT
);
INSERT INTO no_xp_role (role_id) VALUES (0);
```
