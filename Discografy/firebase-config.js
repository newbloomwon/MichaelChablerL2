// Firebase Configuration
// TODO: Replace with your actual config from Firebase Console
const firebaseConfig = {
    apiKey: "YOUR_API_KEY", // Replace with valid Firebase Key if needed
    authDomain: "discopgrafy.firebaseapp.com",
    projectId: "discopgrafy",
    storageBucket: "discopgrafy.appspot.com",
    messagingSenderId: "YOUR_SENDER_ID",
    appId: "YOUR_APP_ID"
};

// Jamendo Configuration
// TODO: Register at https://developer.jamendo.com/ to get a Client ID
const JAMENDO_CLIENT_ID = "4660cc38";

// Initialize Firebase
firebase.initializeApp(firebaseConfig);
const db = firebase.firestore();
const auth = firebase.auth();

// Optional Firebase authentication - gracefully handle errors
firebase.auth().signInAnonymously()
    .then(() => {
        console.log("✅ Signed in anonymously to Firebase.");
    })
    .catch((error) => {
        console.warn("⚠️ Firebase authentication failed (app will continue without it):", error.message);
        console.log("💡 To enable Firebase: Update API key in .env and firebase-config.js");
    });
