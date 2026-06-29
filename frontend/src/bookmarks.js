import { db, auth } from "./firebase";
import { 
  doc, 
  setDoc, 
  deleteDoc, 
  collection, 
  getDocs 
} from "firebase/firestore";

// Scheme bookmark karo
export const addBookmark = async (scheme) => {
  const user = auth.currentUser;
  if (!user) return;
  
  const ref = doc(db, "users", user.uid, "bookmarks", scheme.id);
  await setDoc(ref, {
    id: scheme.id,
    name: scheme.name,
    benefit: scheme.benefit,
    savedAt: new Date().toISOString()
  });
};

// Bookmark hatao
export const removeBookmark = async (schemeId) => {
  const user = auth.currentUser;
  if (!user) return;
  
  const ref = doc(db, "users", user.uid, "bookmarks", schemeId);
  await deleteDoc(ref);
};

// Saare bookmarks fetch karo
export const getBookmarks = async () => {
  const user = auth.currentUser;
  if (!user) return [];
  
  const ref = collection(db, "users", user.uid, "bookmarks");
  const snap = await getDocs(ref);
  return snap.docs.map(d => d.data());
};