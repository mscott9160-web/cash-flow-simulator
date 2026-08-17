# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])

```

## End-to-end tests

The Playwright test covers registration, account creation with a starting balance, saving a bill and income, loading the saved projection, and verifying the saved-item controls in the Bills and Income views.

Install the browser once, then run the test. The Playwright config starts the FastAPI and Vite servers and uses a temporary SQLite database for each run:

```powershell
npx playwright install chromium
npm run e2e
```

For a headed run, use `npm run e2e:headed`.

To start the services manually for exploratory testing, use two terminals from the repository root:

```powershell
$env:DATABASE_PATH = Join-Path $env:TEMP 'cashflow-local.sqlite'
$env:CORS_ORIGINS = 'http://localhost:5173'
python -m uvicorn backend.api:app --host localhost --port 8000
```

```powershell
$env:VITE_API_URL = 'http://localhost:8000'
npm run dev -- --host localhost --port 5173
```

Open `http://localhost:5173` after both services are ready. Remove the temporary database when finished if you do not want to keep local data.

## Operations

The backend reads these environment variables:

- `DATABASE_PATH`: SQLite database file used by the API. Defaults to `cashflow.db`.
- `CORS_ORIGINS`: comma-separated explicit browser origins. Defaults to `http://localhost:5173`.
- `AUTH_SECRET`: JWT signing secret. Required when `ENVIRONMENT=production` or `prod`.
- `ENVIRONMENT`: deployment environment name. Defaults to `development`.

Every response includes an `X-Request-ID`. The API preserves a caller-provided ID or generates a UUID when one is missing. Backend request logs contain only the HTTP method, URL path, status, duration, and request ID; request bodies, passwords, tokens, and financial values are not logged.

### SQLite backup and restore

The scripts use `DATABASE_PATH` unless `--database-path` is supplied. Run them from the repository root:

```powershell
$env:DATABASE_PATH = 'C:\data\cashflow.sqlite'
python scripts/backup_sqlite.py 'C:\backups\cashflow.sqlite'
python scripts/restore_sqlite.py 'C:\backups\cashflow.sqlite'
```

Backup and restore refuse to overwrite an existing non-empty target. To explicitly replace one, add `--confirm-overwrite`:

```powershell
python scripts/restore_sqlite.py 'C:\backups\cashflow.sqlite' --confirm-overwrite
```

Stop the API before restoring a live database. Keep backup files access-controlled because they contain application data.

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])

```
