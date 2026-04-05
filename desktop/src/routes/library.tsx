import { Link } from "react-router-dom";
import { useLibraryStore } from "../store/libraryStore";

export function LibraryPage() {
  const articles = useLibraryStore((state) => state.articles);

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Library</h1>
          <p className="page-subtitle">
            Mock article data for the desktop MVP front-end.
          </p>
        </div>
        <button className="primary-button" type="button">
          Import Article
        </button>
      </div>

      <div className="card-list">
        {articles.map((article) => (
          <article className="card" key={article.id}>
            <div className="card-top">
              <div>
                <h2 className="card-title">{article.title}</h2>
                <p className="card-meta">
                  Status: {article.status} · {article.segments.length} segments
                </p>
                <p className="card-note">
                  Audio fixture: {article.audioPath ?? "Unavailable"} · Resume from{" "}
                  {article.lastPlayedMs} ms
                </p>
              </div>
              <Link className="card-link" to={`/player/${article.id}`}>
                Open
              </Link>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}
