# role-inventory-bot

RoleInventory.py
```sql
CREATE TABLE inventory(
    id TEXT PRIMARY KEY NOT NULL,
    user_id INT,
    roles TEXT
);

CREATE TABLE sr_role (
    role_name TEXT,
    role_id INT
);
CREATE TABLE no_xp_role (
    role_id INT
);
INSERT INTO no_xp_role (role_id) VALUES (0);

CREATE TABLE champion_role (
    role_name TEXT,
    role_id INT
);
CREATE TABLE allowed_rank (
    role_name TEXT,
    role_id INT
);
```

Gamba.py
```sql
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

CREATE TABLE wallet (
    user_id INT,
    award TEXT,
    count INT
);
```

TimedRole.py
```sql
CREATE TABLE timed_role (
    role_id INT,
    expire_days INT
);

CREATE TABLE timed_role_user (
    user_id INT,
    role_id INT,
    date_acquired INT
);
```

