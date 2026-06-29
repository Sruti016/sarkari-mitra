import { useState, useEffect } from "react";
import BookmarksPage from "./pages/BookmarksPage";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { auth } from "./firebase";
import { onAuthStateChanged } from "firebase/auth";
import AuthPage from "./pages/AuthPage";
import ChatPage from "./pages/ChatPage";
import SchemesPage from "./pages/SchemesPage";
import YojanaDetailPage from "./pages/YojanaDetailPage";

function App() {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, (currentUser) => {
      setUser(currentUser);
      setLoading(false);
    });
    return () => unsubscribe();
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-green-50">
        <div className="text-green-600 text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <BrowserRouter>
      <Routes>
        <Route
          path="/login"
          element={!user ? <AuthPage onLogin={() => setUser(auth.currentUser)} /> : <Navigate to="/" />}
        />
        <Route
          path="/"
          element={user ? <ChatPage user={user} /> : <Navigate to="/login" />}
        />
        <Route
          path="/schemes"
          element={user ? <SchemesPage /> : <Navigate to="/login" />}
        />
        <Route
  path="/bookmarks"
  element={!user ? <Navigate to="/login" /> : <BookmarksPage />}
/>
<Route
  path="/yojana/:id"
  element={user ? <YojanaDetailPage /> : <Navigate to="/login" />}
/>
      </Routes>
    </BrowserRouter>
  );
}

export default App;