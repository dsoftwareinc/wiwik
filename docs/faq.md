# Frequently asked questions

## Convert postgres to sqlite3

If you need a dump of a DB from a server for local testing, you can convert
postgresql to sqlite database
using `db-to-sqlite`.

```bash
db-to-sqlite "postgresql://devbb:devbb@localhost/devbb" my2021-12-10.sqlite3 --all
```

Then copy the database file (`my.sqlite3`) under `forum/` folder locally and you
can run the local server using the data
from the server.

### Reset all users passwords

Can be done by running:

```bash
cd forum/
python manage.py reset_users_password
```

## Restore postgres from dump

```
psql --file=scripts/backup_2021-11-06__00-00-01.sql --username=devbb --host=localhost --port=5432 devbb
```

## Is it ok to copy stackoverflow features?

Yes,
see [here](https://meta.stackoverflow.com/questions/306517/is-so-reputation-mechanism-patented)
