// Import the functions you need from the SDKs you need
import { initializeApp } from "firebase/app";
import { getAnalytics } from "firebase/analytics";
// TODO: Add SDKs for Firebase products that you want to use
// https://firebase.google.com/docs/web/setup#available-libraries

// Your web app's Firebase configuration
// For Firebase JS SDK v7.20.0 and later, measurementId is optional
const firebaseConfig = {
  apiKey: "AIzaSyDUox5I6RG7sFABAyX_tUXi4rhiX80MDTY",
  authDomain: "birdnesttgminiapp.firebaseapp.com",
  projectId: "birdnesttgminiapp",
  storageBucket: "birdnesttgminiapp.firebasestorage.app",
  messagingSenderId: "1000241241106",
  appId: "1:1000241241106:web:d23c6df3a1723aba100ccb",
  measurementId: "G-M7FE78B3EM"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const analytics = getAnalytics(app);