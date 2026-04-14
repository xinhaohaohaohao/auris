import { useEffect } from "react";
import { Link } from "react-router-dom";
import { useLibraryStore } from "../store/libraryStore";

export function LibraryPage() {
  const summaries = useLibraryStore((state) => state.summaries);
  const isLoading = useLibraryStore((state) => state.isLoading);
  const error = useLibraryStore((state) => state.error);
  const loadSummaries = useLibraryStore((state) => state.loadSummaries);

  useEffect(() => {
    void loadSummaries();
  }, [loadSummaries]);

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Library</h1>
          <p className="page-subtitle">
            Article list loaded from your Rust Tauri command.
          </p>
        </div>
        <button className="primary-button" type="button">
          Import Article
        </button>
      </div>

      {isLoading ? (
        <div className="empty-state">
          <h2 className="card-title">Loading Articles</h2>
          <p className="page-subtitle">Waiting for Rust command `list_articles`.</p>
        </div>
      ) : null}

      {error ? (
        <div className="empty-state">
          <h2 className="card-title">Load Failed</h2>
          <p className="page-subtitle">{error}</p>
        </div>
      ) : null}

      <div className="card-list">
        {summaries.map((article) => (
          <article className="card" key={article.id}>
            <div className="card-top">
              <div>
                <h2 className="card-title">{article.title}</h2>
                <p className="card-meta">
                  Status: {article.status} | {article.segmentCount} segments
                </p>
                <p className="card-note">
                  Audio fixture: {article.audioPath ?? "Unavailable"} | Resume from{" "}
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
