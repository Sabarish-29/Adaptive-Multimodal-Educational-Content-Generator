# Migration Framework (Scaffold)

Schema version fields (`schema_version`) added to: adaptation_recs, arm_feedback, content_bundles, evaluations, rag_docs, rag_answers.

Future steps:
1. Create migration scripts named `<version>__description.py` exporting `async def upgrade(db)` and optional `async def downgrade(db)`.
2. Maintain a `migrations` collection storing applied versions.
3. Add runner script invoking unapplied migrations in lexicographic order.

Example skeleton:
```python
# scripts/migrations/0001__add_index_example.py
async def upgrade(db):
    await db.collection.create_index('field')
```
