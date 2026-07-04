// Pages are AUTO-ROUTED: every file in src/pages/<Name>.tsx becomes /<name> (Home.tsx → /).
// Generated pages need zero wiring — drop the file in src/pages/ and it is live.
// Login/Register are public; every other page is wrapped in ProtectedRoute.
import { BrowserRouter, Routes, Route, Link } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";

const modules = import.meta.glob("./pages/*.tsx", { eager: true }) as Record<
  string,
  { default: React.ComponentType }
>;

const PUBLIC = new Set(["login", "register"]);

const pages = Object.entries(modules).map(([path, mod]) => {
  const name = path.replace("./pages/", "").replace(".tsx", "");
  const route = name.toLowerCase() === "home" ? "/" : `/${name.toLowerCase()}`;
  return { name, route, Component: mod.default, isPublic: PUBLIC.has(name.toLowerCase()) };
});

function Nav() {
  const { user, logout } = useAuth();
  return (
    <header className="flex items-center justify-between px-6 py-3 bg-slate-800 text-white">
      <h1 className="font-bold">{"BRD"}</h1>
      <nav className="flex items-center gap-4 text-sm">
        {pages.filter((p) => !p.isPublic).map((p) => (
          <Link key={p.route} to={p.route} className="hover:underline">{p.name}</Link>
        ))}
        {user ? (
          <button onClick={logout} className="bg-slate-600 px-3 py-1 rounded">Logout</button>
        ) : (
          <Link to="/login" className="bg-blue-600 px-3 py-1 rounded">Login</Link>
        )}
      </nav>
    </header>
  );
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Nav />
        <main className="p-6">
          <Routes>
            {pages.map(({ route, Component, isPublic }) => (
              <Route
                key={route}
                path={route}
                element={isPublic ? <Component /> : <ProtectedRoute><Component /></ProtectedRoute>}
              />
            ))}
          </Routes>
        </main>
      </BrowserRouter>
    </AuthProvider>
  );
}
