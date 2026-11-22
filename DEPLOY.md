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

## Deploy the web app and API on one Ubuntu VPS with aaPanel

1. From a root terminal on Ubuntu 24.04, install and start Docker and Compose.

   ```bash
   apt update
   apt install -y docker.io docker-compose-v2 docker-buildx
   systemctl enable --now docker
   docker compose version
   ```

2. Clone the repository on the VPS. In Supabase, open **Connect → Session pooler** and copy the PostgreSQL URI. Use a URL-encoded database password in the URI and include `sslmode=require`.

   ```bash
   git clone https://github.com/zxtni/EcoCycle-AI.git /opt/ecocycle-ai
   cd /opt/ecocycle-ai
   test -e .env || install -m 600 .env.example .env
   nano .env
   ```

   Set `DATABASE_URL` and `WEB_ORIGIN=https://eco.zxtni.in` in `.env`. Set `GOOGLE_CLIENT_ID` when OAuth is configured for that origin. Leave `ECO_WEB_PORT` unset to use host port 8108 or choose another unused port.

3. Start both services. The API container applies Alembic migrations at startup. A named volume saves refreshed forecasts. The Next.js container serves the site and forwards `/api/` requests across the Docker network. The VPS publishes only the web port, bound to localhost.

   ```bash
   docker compose -f compose.production.yaml up -d --build --wait
   docker compose -f compose.production.yaml ps
   curl -fsS http://127.0.0.1:8108/api/health
   ```

4. Point `eco.zxtni.in` to the VPS public IP in DNS. In aaPanel, add the domain as a site, issue its HTTPS certificate, and proxy the site to `http://127.0.0.1:8108`. Disable proxy caching for the API and allow request bodies of at least 9 MiB for photo uploads. Verify `https://eco.zxtni.in/` and `https://eco.zxtni.in/api/health`. Use this HTTPS URL for email sign-in, camera access and PWA installation.

5. Provision the first administrator through the running container. In the VPS terminal, use Bash's silent prompt to enter the password, then clear the shell variables after provisioning.

   ```bash
   read -r -p 'Admin email: ' ECO_ADMIN_EMAIL
   read -r -s -p 'Admin password: ' ECO_ADMIN_PASSWORD
   printf '\n'
   export ECO_ADMIN_EMAIL ECO_ADMIN_PASSWORD
   docker compose -f compose.production.yaml exec -T -e ECO_ADMIN_EMAIL -e ECO_ADMIN_PASSWORD api python -m backend.provision
   unset ECO_ADMIN_EMAIL ECO_ADMIN_PASSWORD
   ```

See [Ubuntu Compose package](https://packages.ubuntu.com/noble/docker-compose-v2) and [aaPanel website configuration](https://www.aapanel.com/docs/SubaaPanel/Website.html).
