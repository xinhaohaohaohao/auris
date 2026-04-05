import { create } from "zustand";
import { demoArticles } from "../mocks/demoArticles";
import type { Article } from "../types/article";

type LibraryState = {
  articles: Article[];
  getArticleById: (articleId: string) => Article | undefined;
};

export const useLibraryStore = create<LibraryState>((_set, get) => ({
  articles: demoArticles,
  getArticleById: (articleId) =>
    get().articles.find((article) => article.id === articleId),
}));
