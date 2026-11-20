import { initializeApp, getApps, type FirebaseApp } from 'firebase/app'
import {
  browserLocalPersistence,
  createUserWithEmailAndPassword,
  indexedDBLocalPersistence,
  initializeAuth,
  signInWithEmailAndPassword,
  signOut,
  type Auth,
} from 'firebase/auth'

import type { AuthConfig } from './types'

/**
 * Firebase Authentication (email + password).
 *
 * The config comes from `GET /api/v1/auth/config` - the API key and project
 * ID are public values that ship in every Firebase web app config. The ID
 * token Firebase issues is verified **on the Laravel server**; the browser
 * never decides who the player is.
 */

let firebaseAuth: Auth | null = null

export function firebaseAuthFromConfig(config: AuthConfig): Auth | null {
  if (!config.firebaseEnabled || !config.firebaseApiKey || !config.firebaseProjectId) {
    return null
  }

  if (firebaseAuth) return firebaseAuth

  const existing = getApps()[0]
  const app: FirebaseApp = existing ?? initializeApp({
    apiKey: config.firebaseApiKey,
    authDomain: config.firebaseAuthDomain ?? `${config.firebaseProjectId}.firebaseapp.com`,
    projectId: config.firebaseProjectId,
  })

  // initializeAuth avoids theIndexedDB probe errors in private windows and
  // falls back to local storage explicitly.
  firebaseAuth = initializeAuth(app, {
    persistence: [indexedDBLocalPersistence, browserLocalPersistence],
  })

  return firebaseAuth
}

/** Create a new Firebase account and return a fresh ID token. */
export async function firebaseSignUp(
  auth: Auth,
  email: string,
  password: string,
): Promise<string> {
  const credential = await createUserWithEmailAndPassword(auth, email.trim(), password)
  return credential.user.getIdToken()
}

/** Sign in to an existing Firebase account and return a fresh ID token. */
export async function firebaseSignIn(
  auth: Auth,
  email: string,
  password: string,
): Promise<string> {
  const credential = await signInWithEmailAndPassword(auth, email.trim(), password)
  return credential.user.getIdToken()
}

/** Forget the Firebase session locally (the app session is separate). */
export async function firebaseSignOut(auth: Auth): Promise<void> {
  await signOut(auth)
}
