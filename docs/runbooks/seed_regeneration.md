# Runbook: Seed Regeneration

## When Needed
- Stale demo data
- Schema/index changes

## Steps
1. Stop stack (optional): `docker compose down` (data persists if volume kept)
2. Drop target collections (optional): connect to Mongo shell and `db.learners.drop()` etc.
3. Run seed script:
```
python data/seeds/seed_demo.py
```
4. Verify indexes: in Mongo shell `db.learners.getIndexes()`.

## Safety
- Never run in production cluster.
- Use distinct DB name for local vs staging.
