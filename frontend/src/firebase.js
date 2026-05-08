import { initializeApp } from 'firebase/app';
import { getAuth } from 'firebase/auth';

const apiKey = process.env.REACT_APP_FIREBASE_API_KEY;
const authDomain = process.env.REACT_APP_FIREBASE_AUTH_DOMAIN;
const projectId = process.env.REACT_APP_FIREBASE_PROJECT_ID;

const firebaseConfigured = apiKey && authDomain && projectId;

let app = null;
let auth = null;

if (firebaseConfigured) {
  app = initializeApp({ apiKey, authDomain, projectId });
  auth = getAuth(app);
}

export { auth, app, firebaseConfigured };
