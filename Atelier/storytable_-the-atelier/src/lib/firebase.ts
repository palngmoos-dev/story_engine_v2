import { initializeApp } from 'firebase/app';
import { getAuth, GoogleAuthProvider, signInWithPopup, signOut } from 'firebase/auth';
import { 
  getFirestore, 
  collection, 
  addDoc, 
  setDoc,
  query, 
  where, 
  getDocs, 
  orderBy, 
  serverTimestamp,
  deleteDoc,
  doc
} from 'firebase/firestore';
import firebaseConfig from '../../firebase-applet-config.json';
import { GeneratedStory, Mode } from '../types';

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
export const db = getFirestore(app, firebaseConfig.firestoreDatabaseId);

const googleProvider = new GoogleAuthProvider();

export const signInWithGoogle = () => signInWithPopup(auth, googleProvider);
export const logOut = () => signOut(auth);

export async function saveStory(userId: string, story: GeneratedStory, mode: Mode) {
  if (story.id) {
    const storyRef = doc(db, 'users', userId, 'stories', story.id);
    const { id, ...data } = story;
    return setDoc(storyRef, {
      ...data,
      userId,
      mode,
      updatedAt: serverTimestamp(),
    }, { merge: true });
  }

  const storiesRef = collection(db, 'users', userId, 'stories');
  return addDoc(storiesRef, {
    ...story,
    userId,
    mode,
    createdAt: serverTimestamp(),
  });
}

export async function getUserStories(userId: string): Promise<GeneratedStory[]> {
  const storiesRef = collection(db, 'users', userId, 'stories');
  const q = query(storiesRef, orderBy('createdAt', 'desc'));
  const querySnapshot = await getDocs(q);
  
  return querySnapshot.docs.map(doc => ({
    id: doc.id,
    ...doc.data()
  })) as GeneratedStory[];
}

export async function deleteStory(userId: string, storyId: string) {
  const storyRef = doc(db, 'users', userId, 'stories', storyId);
  return deleteDoc(storyRef);
}
