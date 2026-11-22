# Deploy EcoCycle AI

1. Push the repository to a Git provider. Review the shipped model notices and make the corresponding source available with deployment. See [model notices](backend/vision_assets/NOTICE.md).
2. Create a PostgreSQL database in Supabase. Copy a direct connection string or a session-mode pooler string for IPv4 hosting. Keep the credentials private.
3. Create a Vercel project with root directory `web`. Record its production HTTPS origin.
4. Import `render.yaml` as a Render Blueprint. Set `DATABASE_URL` to the PostgreSQL connection string and `WEB_ORIGIN` to the Vercel origin. The Docker entrypoint applies Alembic migrations and starts the API. Verify `/api/health`.
5. Set `API_ORIGIN` in Vercel to the Render HTTPS origin and deploy. Create a Google OAuth Web client with the browser origin registered and set the public client ID on Render as `GOOGLE_CLIENT_ID`.
6. To create the initial administrator, run `python -m backend.provision` in the Render shell with `ECO_ADMIN_EMAIL` and `ECO_ADMIN_PASSWORD` set. Remove these bootstrap variables after provisioning.
7. On the hosted site, verify login, scanning, reports and model refresh. Configure storage backups and alerting in the providers.

Use `docker compose up --build` for a local SQLite API. Start the frontend with `pnpm --dir web run dev`. Production uses HTTPS for secure cookies and camera access.

## Deploy the API on Railway

1. In Railway, create a service from the EcoCycle-AI GitHub repository and select `main`. Use the repository root. Railway detects the existing root `Dockerfile`. Leave the start command unset so the container applies Alembic migrations before starting Uvicorn.
2. Set `APP_ENV=production`. In Supabase, copy the **Session pooler** PostgreSQL URI and set it as `DATABASE_URL` in Railway Variables. Supply the database password there and append `?sslmode=require` if no query string is present. Keep the connection string private.
3. Set the service healthcheck path to `/api/health` and generate a public HTTPS domain in Railway. For persistent forecast refreshes, attach a volume at `/data`, make it writable by the container's app user, and retain `FORECAST_MODEL_PATH=/data/forecast.json`.
4. Verify that the Railway HTTPS endpoint `/api/health` returns `{"status":"ready"}`. Set Vercel's `API_ORIGIN` to the Railway origin and Railway's `WEB_ORIGIN` to the Vercel origin. Redeploy after the variables are saved.
5. Set `GOOGLE_CLIENT_ID` after adding your Vercel origin to the Google OAuth web client. To provision the first admin, open the deployed service shell with Railway CLI's `railway ssh` and run `python -m backend.provision` with the bootstrap credentials in the service environment. Remove the bootstrap variables after provisioning.

[Railway Dockerfile setup](https://docs.railway.com/builds/dockerfiles) · [Railway healthchecks](https://docs.railway.com/deployments/healthchecks) · [Railway volumes](https://docs.railway.com/volumes)
