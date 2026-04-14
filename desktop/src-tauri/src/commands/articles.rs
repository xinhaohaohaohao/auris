use crate::storage::articles::{load_article_from_dev_data, load_article_index_from_dev_data, update_article_progress_in_dev_data};
use crate::types::{ArticleDetail, ArticleSummary, SegmentDto};

#[tauri::command]
pub fn list_articles() -> Result<Vec<ArticleSummary>, String> {
    load_article_index_from_dev_data()
}

#[tauri::command]
pub fn get_article(article_id: String) -> Result<Option<ArticleDetail>, String> {
    load_article_from_dev_data(&article_id)
}

#[tauri::command]
pub fn update_playback_progress(article_id: String, last_played_ms: u64) -> Result<(), String> {
    update_article_progress_in_dev_data(&article_id, last_played_ms)
}