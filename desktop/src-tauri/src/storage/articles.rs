use std::fs;
use std::io::ErrorKind;
use std::path::PathBuf;
use crate::types::{ArticleDetail, ArticleSummary};

fn dev_articles_dir() -> PathBuf{
    PathBuf::from(env!("CARGO_MANIFEST_DIR"))
        .join("dev_data")
        .join("articles")
}

fn article_index_path() -> PathBuf{
    dev_articles_dir().join("index.json")
}

fn article_detail_path(article_id: &str) -> PathBuf{
    dev_articles_dir().join(format!("{}.json", article_id))
}

pub fn load_article_index_from_dev_data() -> Result<Vec<ArticleSummary>, String>{
    let path = article_index_path();

    let contents = fs::read_to_string(&path)
        .map_err(|e| format!("Failed to read article index: {}", e))?;

    let index = serde_json::from_str::<Vec<ArticleSummary>>(&contents)
        .map_err(|e| format!("Failed to parse article index: {}", e))?;

    Ok(index)
}

pub fn save_article_index_to_dev_data(index: &[ArticleSummary]) -> Result<(), String>{
    let path = article_index_path();

    let json = serde_json::to_string_pretty(index)
        .map_err(|e| format!("Failed to serialize article index: {}", e))?;

    fs::write(&path, json)
        .map_err(|e| format!("Failed to write article index: {}", e))?;

    Ok(())
}

// 从 dev_data 导入数据
pub fn load_article_from_dev_data(article_id: &str)->Result<Option<ArticleDetail>, String>{
    let path = article_detail_path(article_id);

    let contents = match fs::read_to_string(&path){
        Ok(contents) => contents,
        Err(error) if error.kind() == ErrorKind::NotFound => return Ok(None),
        Err(error) => {
            return Err(format!("Failed to read {}: {}", path.display(), error));
        }
    };

    let article = serde_json::from_str::<ArticleDetail>(&contents)
        .map_err(|error| format!("Failed to parse {}: {}", path.display(), error))?;
    Ok(Some(article))
}

pub fn save_article_to_dev_data(article: &ArticleDetail) -> Result<(), String>{
    let path = article_detail_path(&article.id);

    let json = serde_json::to_string_pretty(article)
        .map_err(|e| format!("Failed to serialize article detail: {}", e))?;

    fs::write(&path, json)
        .map_err(|e| format!("Failed to write article detail: {}", e))?;

    Ok(())
}

pub fn update_article_progress_in_dev_data(article_id: &str, last_played_ms: u64)
    ->Result<(), String>{
    let mut index = load_article_index_from_dev_data()?;

    let summary = index
        .iter_mut()
        .find(|article| article.id == article_id)
        .ok_or_else(|| format!("Article {} was not found in index.json", article_id))?;

    summary.last_played_ms = last_played_ms;

    save_article_index_to_dev_data(&index)?;

    let mut article = load_article_from_dev_data(article_id)?
        .ok_or_else(|| format!("Article {} was not found in index.json", article_id))?;

    article.last_played_ms = last_played_ms;

    save_article_to_dev_data(&article)?;

    Ok(())
}

fn build_summary_from_detail(article: &ArticleDetail) -> ArticleSummary {
    ArticleSummary {
        id: article.id.clone(),
        title: article.title.clone(),
        status: article.status.clone(),
        created_at: article.created_at.clone(),
        audio_path: article.audio_path.clone(),
        last_played_ms: article.last_played_ms,
        segment_count: article.segments.len(),
    }
}

fn slugify_title(title: &str) -> String {}