# Deploy EcoCycle AI

1. Push the repository to a Git provider. Review the shipped model notices and make the corresponding source available with deployment. See [model notices](backend/vision_assets/NOTICE.md).
2. Create a PostgreSQL database in Supabase. Copy a direct connection string or a session-mode pooler string for IPv4 hosting. Keep the credentials private.
3. Create a Vercel project with root directory `web`. Record its production HTTPS origin.
4. Import `render.yaml` as a Render Blueprint. Set `DATABASE_URL` to the PostgreSQL connection string and `WEB_ORIGIN` to the Vercel origin. The Docker entrypoint applies Alembic migrations and starts the API. Verify `/api/health`.
5. Set `API_ORIGIN` in Vercel to the Render HTTPS origin and deploy. Create a Google OAuth Web client with the browser origin registered and set the public client ID on Render as `GOOGLE_CLIENT_ID`.
6. To create the initial administrator, run `python -m backend.provision` in the Render shell with `ECO_ADMIN_EMAIL` and `ECO_ADMIN_PASSWORD` set. Remove these bootstrap variables after provisioning.
7. On the hosted site, verify login, scanning, reports and model refresh. Configure storage backups and alerting in the providers.

Use `docker compose up --build` for a local SQLite API. Start the frontend with `pnpm --dir web run dev`. Production uses HTTPS for secure cookies and camera access.
