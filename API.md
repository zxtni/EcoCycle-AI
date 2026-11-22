# API guide

Run the app and visit http://localhost:3000/api/docs for the interactive OpenAPI schema. The frontend sends requests under `/api` on the website origin. Citizen and administrator sessions use the login cookie.

| Group | Routes |
| --- | --- |
| Identity | `/auth/register`, `/auth/login`, `/auth/me`, `/auth/logout`, `/auth/google` |
| Scanner | `POST /scans` multipart image, `PUT /scans/{id}/correction`, `POST /scans/{id}/confirm` |
| Citizen data | `GET /materials`, `POST /materials/estimate`, `GET /impact`, `GET /centers` |
| Municipality | `GET /municipality/summary`, `GET /municipality/forecast`, `GET /municipality/report/{csv or pdf}` |
| Administration | `/admin/centers`, `/admin/feedback`, `/admin/audit`, `POST /admin/forecast/refresh` |

An unauthorized request returns 401. A signed-in user without the required role receives 403. Validation failures return 422. An oversized upload returns 413. A rate-limited request returns 429.
