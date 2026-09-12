# Cashflow Mobile

Expo React Native client for the Cashflow Simulator API.

## Features

- Login and registration
- Secure token storage with `expo-secure-store`
- Starting account setup
- Daily projection dashboard
- Negative-day summary
- Optimizer recommendation with hypothetical Apply/Undo
- Demo onboarding is intentionally scoped to web for this release; mobile keeps the authenticated login/register flow and does not create synthetic accounts.
- Add, edit, pause, resume, and delete income and bills

## Local Development

```powershell
cd mobile
npm install
$env:EXPO_PUBLIC_API_URL = 'http://192.168.1.183:8000'
npx expo start --dev-client --lan
```

The mobile project uses Expo SDK 57 and an Expo development build. For a physical iPhone, use the host computer's LAN IP and keep both devices on the same Wi-Fi network.

## Build A Development Client

```powershell
npx eas build --platform ios --profile development
```

Install the resulting development build on the registered device, then run Metro with `npx expo start --dev-client --lan`.

## Checks

```powershell
npm run typecheck
npx expo-doctor
npm run export
```

The app stores the bearer token and selected account ID in `expo-secure-store`. Financial recommendations remain hypothetical schedule changes; the app does not initiate real payments.
