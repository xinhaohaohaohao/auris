// 将 struct 转换成前端能接收的 json
use serde::{Serialize, Deserialize};



#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ArticleSummary {
    pub id: String,
    pub title: String,
    pub status: String,
    pub created_at: String,
    pub audio_path: Option<String>,
    pub last_played_ms: u64,
    pub segment_count: usize,
}

// Data Transfer Object 专门给前端传输用的数据结构
#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct SegmentDto {
    pub id: String,
    pub source_text: String,
    pub translated_text: Option<String>,
    pub start_ms: u64,
    pub end_ms: u64,
}

#[derive(Debug, Clone, Serialize, Deserialize)]
#[serde(rename_all = "camelCase")]
pub struct ArticleDetail {
    pub id: String,
    pub title: String,
    pub status: String,
    pub created_at: String,
    pub audio_path: Option<String>,
    pub last_played_ms: u64,
    pub segments: Vec<SegmentDto>,
}