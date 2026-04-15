# Offline Sync Design (SQLite ↔ PostgreSQL)

## Mode of operation
- Remote airstrip tablets run the same FastAPI app with `DATABASE_URL=sqlite:///./airstrip.db`.
- Central server runs PostgreSQL.

## Sync protocol
1. **Push first**: tablet posts local changes to `POST /sync/push` as `SyncPushItem` events.
2. **Pull second**: tablet fetches new central events from `GET /sync/pull?since=<iso-date>`.
3. Tablet applies returned events to local SQLite.

## Conflict resolution
- Strategy: **Last-write-wins + audit trail**.
- Every event includes `updated_at` and `device_id`.
- If incoming update is older than stored event timestamp, server keeps current record and ignores stale update.
- All accepted events are retained in `sync_events` for replay/troubleshooting.

## Reliability notes
- Use UUID/external IDs on client for offline-created records.
- Keep local retry queue with exponential backoff.
- Persist `last_successful_sync_at` on each device.
