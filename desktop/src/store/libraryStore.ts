import { create } from "zustand";
import { listArticles } from "../lib/tauri";
import type { ArticleSummary } from "../types/article";

type LibraryState = {
  summaries: ArticleSummary[];
  isLoading: boolean;
  error: string | null;
  loadSummaries: () => Promise<void>;
};

export const useLibraryStore = create<LibraryState>((set) => ({
  summaries: [],
  isLoading: false,
  error: null,
  loadSummaries: async () => {
    set({ isLoading: true, error: null });

    try {
      const summaries = await listArticles();
      set({ summaries, isLoading: false, error: null });
    } catch (error) {
      const message =
        error instanceof Error ? error.message : "Failed to load articles from Tauri";
      set({ isLoading: false, error: message });
    }
  },
}));
