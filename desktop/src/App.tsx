import { MemoryRouter, NavLink, Route, Routes } from "react-router-dom";
import "./App.css";
import { demoArticles } from "./mocks/demoArticles";
import { LibraryPage } from "./routes/library";
import { PlayerPage } from "./routes/player";

function App() {
  return (
    <MemoryRouter>
      <div className="app-shell">
        <aside className="sidebar">
          <div className="brand-block">
            <p className="brand-mark">Auris</p>
            <p className="brand-subtitle">Desktop MVP</p>
          </div>

          <nav className="nav-list">
            <NavLink
              to="/"
              end
              className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
            >
              Library
            </NavLink>

            <NavLink
              to={`/player/${demoArticles[0].id}`}
              className={({ isActive }) => (isActive ? "nav-link active" : "nav-link")}
            >
              Player
            </NavLink>
          </nav>
        </aside>

        <main className="content">
          <Routes>
            <Route path="/" element={<LibraryPage />} />
            <Route path="/player/:articleId" element={<PlayerPage />} />
          </Routes>
        </main>
      </div>
    </MemoryRouter>
  );
}

export default App;
