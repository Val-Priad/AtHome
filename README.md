# AtHome project

## Installation

Required environment variables:

```
APP_BASE_URL=
MEDIA_BASE_URL=
RESEND_API_KEY=
JWT_SECRET_KEY=

RATE_LIMIT_STORAGE_URI=
RATE_LIMIT_TEST_STORAGE_URI=memory://

POSTGRES_PORT=
POSTGRES_USER=
POSTGRES_PASSWORD=

DATABASE_URL=
TEST_DATABASE_URL=

REDIS_PORT=
REDIS_URL=

S3_BUCKET_NAME=
```

Optional environment variables:

```
S3_REGION=
S3_ACCESS_KEY_ID=
S3_SECRET_ACCESS_KEY=
S3_PRESIGNED_URL_TTL_SECONDS=300
MEDIA_ORPHAN_MIN_AGE_HOURS=24
```

## Browser media uploads

Request upload URLs with `POST /api/media/upload-urls`. For every file, send
the exact browser `File.type` as `content_type` and `File.size` as
`size_bytes`.

Upload the original `File` to the returned `upload_url` with `PUT` and the
same `Content-Type`. The presigned URL includes both `Content-Type` and
`Content-Length` in its signature, so changing the file or either value makes
S3 reject the request.

Store the returned `object_key` in the subsequent profile or estate request.
Upload URLs and object keys are one-time reservations and must not be reused
for another attachment.

## Orphaned media cleanup

Run the internal cleanup job with:

```bash
PYTHONPATH=src uv run flask --app wsgi:app media cleanup-orphans
```

Schedule this command externally, for example with cron or a platform
scheduler. Running it once per day is sufficient.
