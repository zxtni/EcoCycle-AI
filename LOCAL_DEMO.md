# Run EcoCycle AI on a Windows laptop

Set up the laptop while it has internet access, ideally the day before the presentation. The demo uses local SQLite and bundled ONNX models. It needs no Supabase connection or API keys.

## First-time setup

1. Install Git, Node.js 24 LTS, and uv. Open a fresh PowerShell window so their commands are available.
2. Install the project's pnpm version and clone the repository.

   ```powershell
   npm.cmd install --global pnpm@11.25.0
   git clone https://github.com/zxtni/EcoCycle-AI.git
   cd EcoCycle-AI
   ```

3. Install dependencies, create the local database, and seed the demo accounts.

   ```powershell
   node scripts/setup.mjs
   ```

   The script uses uv to create a Python 3.12 environment. Allow the initial dependency downloads to finish. If PowerShell cannot find a command after installation, reopen the terminal. [Git](https://git-scm.com/install/windows) · [Node.js](https://nodejs.org/en/download) · [uv](https://docs.astral.sh/uv/getting-started/installation/)

## Launch on presentation day

Open PowerShell inside the cloned `EcoCycle-AI` directory and run:

```powershell
node scripts/dev.mjs
```

Keep the terminal open. Open [EcoCycle AI](http://localhost:3000) in a browser. The [health endpoint](http://localhost:3000/api/health) should return `{"status":"ready"}`. Press Ctrl+C in the terminal when you finish.

## Five-minute walkthrough

Both local accounts use the password `EcoCycle local demo 2026!`.

| Account | What to show |
| --- | --- |
| `citizen@example.org` | Open **Scan waste → Upload photo** and select `backend/vision_assets/demo-plastic.jpg` from the cloned project. Click **Analyze photo**, enter **0.125 kg**, click **Calculate estimate**, then **Save to my impact**. Open **My impact** and find the new record. |
| `admin@example.org` | Sign out and sign in as admin. Open **Municipality**, select **Synthetic demo** under **Reporting period**, and click **Apply filters**. Open **Model metrics** and download the CSV or PDF. |

The sample is a real image of plastic packaging. The saved demo history, sample collection points and Bengaluru ward forecasts are labeled synthetic. Image inference, estimates, history and exports work offline after setup. Live OpenStreetMap listings and map tiles require internet, so leave the locator for the end of an offline demo.

## Quick troubleshooting

- **Port in use.** Stop the other instance of EcoCycle or app using port 3000 or 8000, then restart.
- **Demo login fails.** From a fresh PowerShell in the project directory, rerun `node scripts/setup.mjs`. Use the example emails above. Keep any production environment variables out of this local terminal.
- **Camera unavailable.** Give the browser camera permission, or use **Upload photo** with the packaged sample.
- **Need to verify the setup.** Run `node scripts/check.mjs` from the project directory ahead of the demo.

For the data sources and measured model results, see [MODEL_CARD.md](MODEL_CARD.md). For the slide deck, open the [college project presentation](page://page_a1b750cc34b88191a8d2c0a9f2ba7af2).
