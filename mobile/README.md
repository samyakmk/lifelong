# Baseline Lab for iOS

This Expo React Native app uses the Flask member API for sign-in, order status, booking, published reports, trends, insights, and chat. The Simulator path uses Expo Go with SDK 57. It was exercised on an iPhone 17 Pro with iOS 26.2 and Xcode 26.2.

## Run from the repository root

In the first terminal, start the seeded backend after [the Python setup](../README.md):

```sh
npm run demo:seed
npm start
```

In a second terminal, boot the simulator and launch the app:

```sh
xcrun simctl list devices available
xcrun simctl boot 'iPhone 17 Pro'
xcrun simctl bootstatus 'iPhone 17 Pro' -b
npm --prefix mobile ci
npm run ios
```

If the simulator is already booted, start with `bootstatus`. Expo CLI installs its matching Expo Go build on first launch. If the Simulator window is hidden, run `open -a Simulator`. To reopen an existing Metro session, run `xcrun simctl openurl booted exp://127.0.0.1:8084`.

By default the app uses `http://127.0.0.1:5050/api/v1`. To use a Flask instance on another loopback port, set the full API base before starting Metro:

```sh
EXPO_PUBLIC_BASELINE_API_URL=http://127.0.0.1:5053/api/v1 npm run ios
```

The API URL is public configuration baked into the bundle. Restart Metro with the new value when switching instances. The npm Expo scripts disable loading dotenv files. The app stores the bearer session in SecureStore and scopes it to the configured API URL. The API issues sessions for 24 hours.

## Rehearse on the simulator

- Sign in as **Casey Harper** using the [prepared account credentials](../README.md). Leave the member signed in before the interview.
- Open **Results**. The latest report opens first. Use **Choose draw** for the baseline report and **Trends** to select a biomarker. The default LDL trend shows 142 mg/dL on April 10, 2025 and 104 mg/dL on October 16, 2025.
- Open **Insights** to see the comparisons computed by Flask. In **Chat**, tap “What changed in my LDL cholesterol since my first test?” or type it. The answer should give the 38 mg/dL decrease and link both source draws.
- Rehearse booking with a separate member created through public signup. Approve the order at `/staff`, sign in as that member in Expo Go, choose **Book a draw**, select a slot, and confirm. The app returns to Home and shows the saved appointment and prep. Reload that member’s staff case to compare the location and time.

[Results screenshot](screenshots/results.png) · [Chat screenshot](screenshots/chat.png)

To relaunch the simulator app without the Expo Go developer controls covering the screen, keep Metro running and use:

```sh
xcrun simctl launch --terminate-running-process booted host.exp.Exponent \
  -EXDevMenuIsOnboardingFinished 1 -EXDevMenuShowsAtLaunch 0 -EXDevMenuShowFloatingActionButton 0
xcrun simctl openurl booted exp://127.0.0.1:8084
```

Open the desired screen and capture it with `xcrun simctl io booted screenshot path/to/screenshot.png`. [Expo developer menu launch arguments](https://docs.expo.dev/eas/simulators/how-to/iterate-on-your-code/)

## Checks and export

```sh
npm --prefix mobile run typecheck
npm run build:ios
```

The export contains the iOS JavaScript bundle and assets. Use `npm run ios` to run the native app on the simulator. [Expo’s simulator setup](https://docs.expo.dev/workflow/ios-simulator/)
