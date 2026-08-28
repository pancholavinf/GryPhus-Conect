## 2026-07-14T13:28:53Z

You are the Worker subagent for Milestone 1. Your working directory is C:/Users/fcola/Desktop/APPACCURATEK/.agents/worker_m1/.
Your mission is to initialize and set up the React Native Expo application, configure package dependencies, implement the design system (theme, fonts, toast notifications), and implement the basic authentication navigation stack and screens.

## Task Details:
1. **Initialize the app**:
   Create a fresh React Native Expo app inside `C:/Users/fcola/Desktop/APPACCURATEK/app_trackeo_avances` using `npx create-expo-app@51 --template blank` or similar appropriate command in the root folder.
2. **Setup package.json**:
   Install the following dependencies:
   - `@react-native-async-storage/async-storage`
   - `@react-navigation/native`
   - `@react-navigation/native-stack`
   - `@supabase/supabase-js`
   - `expo-font`
   - `expo-image-manipulator`
   - `expo-sqlite`
   - `expo-splash-screen`
   - `react-native-safe-area-context`
   - `react-native-screens`
   - `react-native-url-polyfill`
   - `@expo-google-fonts/montserrat`
   - `@expo-google-fonts/inter`
   - `react-native-toast-message` (or custom toast notification system)
3. **Directory Structure**:
   Ensure this exact folder structure is created:
   - `app_trackeo_avances/src/components/`
   - `app_trackeo_avances/src/screens/`
   - `app_trackeo_avances/src/database/`
   - `app_trackeo_avances/src/services/`
   - `app_trackeo_avances/src/constants/`
4. **Theme Configuration (`app_trackeo_avances/src/constants/theme.js`)**:
   Implement colors and typography based on the design system:
   - Background: #FAFAFA
   - Primary: #1A529B (Headers, branding)
   - Secondary/CTA: #EE741D (rounded-full, min height 48px)
   - Accent: #4BA2E3
   - Support/Gris: #64748B
   - Border: #F1F5F9 (slate-100 style)
   - Statuses: Pending (#F59E0B), Approved (#10B981), Offline/Error (#EF4444)
   - Typography: Montserrat for headings, Inter for body/captions.
5. **Supabase Client Setup (`app_trackeo_avances/src/services/supabase.js`)**:
   Initialize Supabase using credentials from `C:/Users/fcola/Desktop/APPACCURATEK/.env`. Configure custom storage for persistence using `@react-native-async-storage/async-storage`.
6. **Font Loading & Entrypoint (`app_trackeo_avances/App.js`)**:
   - Asynchronously load Montserrat (Bold, SemiBold) and Inter (Regular, Medium, Bold) using `useFonts` or similar.
   - Use `expo-splash-screen` to keep the splash screen visible until fonts are fully loaded.
   - Set up the Toast notification container at the root level.
   - Manage `session` and `userProfile` state. Mock the user profile fetching for now since SQLite/DB is Milestone 2.
   - Configure `@react-navigation/native` container. If the user is authenticated, route them to a tab/stack with `HomeScreen` and a placeholder `SelectionFlowScreen`. If not authenticated, route them to `LoginScreen`.
7. **LoginScreen (`app_trackeo_avances/src/screens/LoginScreen.js`)**:
   - Clean, accessible input fields for email and password.
   - Main CTA Submit button styled as a secondary Naranja (`#EE741D`), rounded-full (border-radius 24+), min-height 48px, text Montserrat Bold white.
   - Background `#FAFAFA`, headers/branding in `#1A529B` (Azul Track).
   - Display error or success notifications via Toast only (no native window alerts).
8. **HomeScreen & Navigation Wrapper**:
   - Create a basic `HomeScreen.js` and `SelectionFlowScreen.js` as a placeholder for navigation setup.
9. **Load Skill**:
   - Load and apply the `frontend-ui-engineering` skill located at `C:/Users/fcola/Desktop/APPACCURATEK/.agents/skills/frontend-ui-engineering_skill/SKILL.md` to ensure your components are high quality, accessible, and not matching any "generic AI aesthetic".
