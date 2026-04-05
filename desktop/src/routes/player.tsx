import { useEffect } from "react";
import { Link, useParams } from "react-router-dom";
import { PlayerControls } from "../components/PlayerControls";
import { SubtitleView } from "../components/SubtitleView";
import { useLibraryStore } from "../store/libraryStore";
import { usePlayerStore } from "../store/playerStore";

export function PlayerPage() {
  const { articleId } = useParams();
  const article = useLibraryStore((state) =>
    articleId ? state.getArticleById(articleId) : undefined,
  );
  const activeSegmentId = usePlayerStore((state) => state.activeSegmentId);
  const currentTimeMs = usePlayerStore((state) => state.currentTimeMs);
  const durationMs = usePlayerStore((state) => state.durationMs);
  const isPlaying = usePlayerStore((state) => state.isPlaying);
  const rate = usePlayerStore((state) => state.rate);
  const loadArticle = usePlayerStore((state) => state.loadArticle);
  const play = usePlayerStore((state) => state.play);
  const pause = usePlayerStore((state) => state.pause);
  const seekTo = usePlayerStore((state) => state.seekTo);
  const setRate = usePlayerStore((state) => state.setRate);
  const syncFromAudio = usePlayerStore((state) => state.syncFromAudio);
  const cleanup = usePlayerStore((state) => state.cleanup);

  useEffect(() => {
    if (!article) {
      return;
    }

    loadArticle(article);

    const timerId = window.setInterval(() => {
      syncFromAudio(article.segments);
    }, 150);

    return () => {
      window.clearInterval(timerId);
      cleanup();
    };
  }, [article, cleanup, loadArticle, syncFromAudio]);

  if (!article) {
    return (
      <section className="page">
        <div className="empty-state">
          <h1 className="page-title">Article Not Found</h1>
          <p className="page-subtitle">
            The player route is ready, but the requested mock article does not exist.
          </p>
          <Link className="secondary-link" to="/">
            Back to Library
          </Link>
        </div>
      </section>
    );
  }

  return (
    <section className="page">
      <div className="page-header">
        <div>
          <h1 className="page-title">Player</h1>
          <p className="page-subtitle">Article ID: {articleId}</p>
        </div>
        <Link className="secondary-link" to="/">
          Back to Library
        </Link>
      </div>

      <div className="player-layout">
        <SubtitleView
          segments={article.segments}
          activeSegmentId={activeSegmentId}
        />
        <PlayerControls
          title={article.title}
          isPlaying={isPlaying}
          currentTimeMs={currentTimeMs}
          durationMs={durationMs}
          rate={rate}
          onPlay={play}
          onPause={pause}
          onSeek={seekTo}
          onRateChange={setRate}
        />
      </div>
    </section>
  );
}
