# Cashflow mobile client

This is the first Expo client for the Cashflow Simulator. It uses the existing FastAPI auth, saved account, projection, income, and bill endpoints. Mobile optimizer Apply/Undo is intentionally deferred; the projection is read-only and recommendations remain advisory in the API.

## Run locally

From `mobile/`, install dependencies and start Expo:

```powershell
npm install
$env:EXPO_PUBLIC_API_URL = 'http://localhost:8000'
npm start
```

Use `npm run android` or `npm run ios` after starting if a simulator is installed. On a physical device, set `EXPO_PUBLIC_API_URL` to the host machine's LAN address and allow that origin in the backend's `CORS_ORIGINS` setting when needed.

## Checks

```powershell
npm run typecheck
npm run export
```

The app stores the bearer token and selected account ID in `expo-secure-store`. A newly authenticated user is asked for a starting balance and as-of date once, then returns to the saved projection on later launches.