import { useState, useEffect } from "react";
import { getBookmarks, removeBookmark } from "../bookmarks";
import { useNavigate } from "react-router-dom";

export default function BookmarksPage() {
  const [bookmarks, setBookmarks] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    fetchBookmarks();
  }, []);

  const fetchBookmarks = async () => {
    const data = await getBookmarks();
    setBookmarks(data);
    setLoading(false);
  };

  const handleRemove = async (id) => {
    await removeBookmark(id);
    setBookmarks(bookmarks.filter(b => b.id !== id));
  };

  return (
    <div className="min-h-screen bg-green-50">
      {/* Header */}
      <div className="bg-green-800 text-white p-4 flex items-center gap-3">
        <button onClick={() => navigate("/")} className="text-white text-xl">←</button>
        <h1 className="text-lg font-bold">🔖 Meri Saved Schemes</h1>
      </div>

      <div className="p-4">
        {loading ? (
          <p className="text-center text-gray-500 mt-10">Loading...</p>
        ) : bookmarks.length === 0 ? (
          <div className="text-center mt-20">
            <div className="text-5xl mb-4">🔖</div>
            <p className="text-gray-500">Koi saved scheme nahi hai</p>
            <p className="text-gray-400 text-sm mt-2">Chat mein schemes save karo!</p>
            <button
              onClick={() => navigate("/")}
              className="mt-4 bg-green-600 text-white px-6 py-2 rounded-lg"
            >
              Chat Pe Jaao
            </button>
          </div>
        ) : (
          <div>
            <p className="text-gray-500 text-sm mb-4">{bookmarks.length} schemes saved hain</p>
            {bookmarks.map((b) => (
              <div key={b.id} className="bg-white rounded-xl p-4 mb-3 shadow-sm border border-green-100">
                <div className="flex justify-between items-start">
                  <div>
                    <h3 className="font-bold text-green-800">{b.name}</h3>
                    <p className="text-gray-500 text-sm mt-1">{b.benefit}</p>
                    <p className="text-gray-300 text-xs mt-1">{b.savedAt?.slice(0,10)}</p>
                  </div>
                  <button
                    onClick={() => handleRemove(b.id)}
                    className="text-red-400 hover:text-red-600 text-sm"
                  >
                    ✕ Remove
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}