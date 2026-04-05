import { Howl } from "howler";
import { create } from "zustand";
import type { Article, Segment } from "../types/article";

type PlayerState = {
  articleId: string | null;
  howl: Howl | null;
  isPlaying: boolean;
  currentTimeMs: number;
  durationMs: number;
  rate: number;
  activeSegmentId: string | null;
  loadArticle: (article: Article) => void;
  play: () => void;
  pause: () => void;
  seekTo: (nextMs: number) => void;
  setRate: (nextRate: number) => void;
  syncFromAudio: (segments: Segment[]) => void;
  cleanup: () => void;
};

function findActiveSegmentId(segments: Segment[], currentTimeMs: number): string | null {
  for (const segment of segments) {
    if (currentTimeMs >= segment.startMs && currentTimeMs < segment.endMs) {
      return segment.id;
    }
  }

  const fallback = segments[segments.length - 1];
  return fallback ? fallback.id : null;
}

function unloadHowl(howl: Howl | null) {
  if (!howl) {
    return;
  }

  howl.stop();
  howl.unload();
}

function getLastSegmentEndMs(segments: Segment[]) {
  const lastSegment = segments[segments.length - 1];
  return lastSegment ? lastSegment.endMs : 0;
}

export const usePlayerStore = create<PlayerState>((set, get) => ({
  articleId: null,
  howl: null,
  isPlaying: false,
  currentTimeMs: 0,
  durationMs: 0,
  rate: 1,
  activeSegmentId: null,
  loadArticle: (article) => {
    const current = get();

    if (current.articleId === article.id && current.howl) {
      return;
    }

    unloadHowl(current.howl);

    if (!article.audioPath) {
      set({
        articleId: article.id,
        howl: null,
        isPlaying: false,
        currentTimeMs: 0,
        durationMs: getLastSegmentEndMs(article.segments),
        activeSegmentId: article.segments[0]?.id ?? null,
      });
      return;
    }

    const nextHowl = new Howl({
      src: [article.audioPath],
      html5: true,
      preload: true,
      rate: current.rate,
      onplay: () => set({ isPlaying: true }),
      onpause: () => set({ isPlaying: false }),
      onstop: () => set({ isPlaying: false }),
      onend: () =>
        set((state) => ({
          isPlaying: false,
          currentTimeMs: state.durationMs,
        })),
      onload: () => {
        const durationMs = Math.round(nextHowl.duration() * 1000);
        const startMs = article.lastPlayedMs;

        if (startMs > 0) {
          nextHowl.seek(startMs / 1000);
        }

        set({
          durationMs,
          currentTimeMs: startMs,
          activeSegmentId: findActiveSegmentId(article.segments, startMs),
        });
      },
      onloaderror: () => {
        set({ isPlaying: false });
      },
      onplayerror: () => {
        set({ isPlaying: false });
      },
    });

    set({
      articleId: article.id,
      howl: nextHowl,
      isPlaying: false,
      currentTimeMs: article.lastPlayedMs,
      durationMs: getLastSegmentEndMs(article.segments),
      activeSegmentId: findActiveSegmentId(article.segments, article.lastPlayedMs),
    });
  },
  play: () => {
    get().howl?.play();
  },
  pause: () => {
    get().howl?.pause();
  },
  seekTo: (nextMs) => {
    const howl = get().howl;
    if (!howl) {
      return;
    }

    howl.seek(nextMs / 1000);
    set({ currentTimeMs: nextMs });
  },
  setRate: (nextRate) => {
    const howl = get().howl;
    if (howl) {
      howl.rate(nextRate);
    }

    set({ rate: nextRate });
  },
  syncFromAudio: (segments) => {
    const howl = get().howl;
    if (!howl) {
      return;
    }

    const currentSeek = howl.seek();
    const currentTimeMs =
      typeof currentSeek === "number" ? Math.round(currentSeek * 1000) : 0;

    set({
      currentTimeMs,
      activeSegmentId: findActiveSegmentId(segments, currentTimeMs),
      durationMs: Math.max(Math.round(howl.duration() * 1000), getLastSegmentEndMs(segments)),
    });
  },
  cleanup: () => {
    unloadHowl(get().howl);
    set({
      articleId: null,
      howl: null,
      isPlaying: false,
      currentTimeMs: 0,
      durationMs: 0,
      activeSegmentId: null,
    });
  },
}));
