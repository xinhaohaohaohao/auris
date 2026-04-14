import { useEffect, useRef, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { PlayerControls } from "../components/PlayerControls";
import { SubtitleView } from "../components/SubtitleView";
import { getArticle, updatePlaybackProgress } from "../lib/tauri";
import { usePlayerStore } from "../store/playerStore";
import type { Article } from "../types/article";

export function PlayerPage() {
  const { articleId } = useParams();
  const [article, setArticle] = useState<Article | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
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
  const latestProgressRef = useRef(0);
  const lastSavedProgressRef = useRef<number | null>(null);

  latestProgressRef.current = currentTimeMs;

  async function persistProgress(nextMs: number) {
    if (!article?.id) {
      return;
    }

    const normalizedMs = Math.max(0, Math.round(nextMs));

    if (lastSavedProgressRef.current === normalizedMs) {
      return;
    }

    try {
      await updatePlaybackProgress(article.id, normalizedMs);
      lastSavedProgressRef.current = normalizedMs;
    } catch (persistError) {
      console.error("Failed to save playback progress", persistError);
    }
  }

  function handlePause() {
    pause();
    void persistProgress(latestProgressRef.current);
  }

  function handleSeek(nextMs: number) {
    seekTo(nextMs);
    latestProgressRef.current = nextMs;
    void persistProgress(nextMs);
  }

  useEffect(() => {
    if (!articleId) {
      setArticle(null);
      setError("Missing article id.");
      return;
    }

    const currentArticleId = articleId;
    let cancelled = false;

    async function loadCurrentArticle() {
      setIsLoading(true);
      setError(null);

      try {
        const result = await getArticle(currentArticleId);

        if (cancelled) {
          return;
        }

        if (!result) {
          setArticle(null);
          setError(`Article ${currentArticleId} was not found.`);
          setIsLoading(false);
          return;
        }

        setArticle(result);
        setIsLoading(false);
      } catch (loadError) {
        if (cancelled) {
          return;
        }

        const message =
          loadError instanceof Error ? loadError.message : "Failed to load article.";
        setArticle(null);
        setError(message);
        setIsLoading(false);
      }
    }

    void loadCurrentArticle();

    return () => {
      cancelled = true;
    };
  }, [articleId]);

  useEffect(() => {
    if (!article) {
      return;
    }

    lastSavedProgressRef.current = article.lastPlayedMs;
    loadArticle(article);

    const timerId = window.setInterval(() => {
      syncFromAudio(article.segments);
    }, 150);

    return () => {
      void persistProgress(latestProgressRef.current);
      window.clearInterval(timerId);
      cleanup();
    };
  }, [article, cleanup, loadArticle, syncFromAudio]);

  if (isLoading) {
    return (
      <section className="page">
        <div className="empty-state">
          <h1 className="page-title">Loading Article</h1>
          <p className="page-subtitle">Waiting for Rust command `get_article`.</p>
          <Link className="secondary-link" to="/">
            Back to Library
          </Link>
        </div>
      </section>
    );
  }

  if (!article) {
    return (
      <section className="page">
        <div className="empty-state">
          <h1 className="page-title">Article Not Found</h1>
          <p className="page-subtitle">{error ?? "The requested article does not exist."}</p>
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
          onPause={handlePause}
          onSeek={handleSeek}
          onRateChange={setRate}
        />
      </div>
    </section>
  );
}
