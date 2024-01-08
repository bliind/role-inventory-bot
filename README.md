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
    datestamp INT
);
```
