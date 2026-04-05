# Auris Phase 1

第一阶段先做一个 Python 原型，目标是把这条链路跑通：

`txt / md / url -> 提取文本 -> 分段 -> 腾讯翻译 -> Edge TTS -> mp3 + lrc`

## 当前范围

- 输入：`.txt`、`.md`、网页 `URL`
- 抓取：尽量提取网页正文，并保存为 `.txt` 或 `.md`
- 分段：偏短、适合单屏字幕显示
- 翻译：腾讯云 `TextTranslate`
- TTS：`edge-tts`
- 输出：抓取内容文件默认存到 `originals/`，`.mp3` 和 `.lrc` 存到 `output/`
- 失败策略：翻译失败时保留英文；TTS 失败时整次任务终止

## 目录

- `main.py`：CLI 入口、读文件、写输出
- `fetcher.py`：抓取网页并提取正文
- `pipeline.py`：主流程编排
- `models.py`：数据结构
- `splitter.py`：文本清洗和分段
- `translator.py`：腾讯翻译调用和限速
- `tts.py`：`edge-tts` 逐段生成音频并合并
- `lrc.py`：生成双语 LRC

## 依赖

1. 安装 Python 3.11+
2. 安装 `uv`
3. 安装 `ffmpeg` 和 `ffprobe`

当前默认用法是：先 `cd phase1`，再用 `uv run` 启动。

## ffmpeg 说明

- 如果 `ffmpeg` 和 `ffprobe` 已经加入系统 `PATH`，不需要改 `.env`
- 如果没有加入 `PATH`，就在 `.env` 里设置它们的绝对路径

例如：

```env
AURIS_FFMPEG_COMMAND=C:/ffmpeg/bin/ffmpeg.exe
AURIS_FFPROBE_COMMAND=C:/ffmpeg/bin/ffprobe.exe
```

可以用下面的命令检查是否已在 `PATH` 中：

```powershell
ffmpeg -version
ffprobe -version
```

## 环境变量

复制 `.env.example` 中的键值，至少需要：

- `TENCENT_SECRET_ID`
- `TENCENT_SECRET_KEY`
- `TENCENT_REGION`

```powershell
Copy-Item .env.example .env
```

注意：`.env` 里的每一行都必须是 `KEY=VALUE` 格式，不能多出单独一行文本。Windows 路径建议写成正斜杠，例如 `C:/ffmpeg/bin/ffmpeg.exe`。

如果你只想抓取网页保存文件，不跑翻译/TTS，可以不用填腾讯云密钥。

抓下来的原文默认保存到 `originals/`。如果你想改目录，可以设置：

```env
AURIS_SOURCE_DIR=originals
```

## 运行

```powershell
cd phase1
uv run --env-file .env -m main --file path\to\article.md --out-dir output
```

```powershell
cd phase1
uv run --env-file .env -m main --text "Web3 is the next generation internet." --out-dir output
```

只抓网页并保存成 Markdown：

```powershell
cd phase1
uv run --env-file .env -m main --url https://ethereum.org/en/what-is-ethereum/ --fetch-only --save-format md --source-dir originals
```

抓网页、保存正文，同时继续生成音频和字幕：

```powershell
cd phase1
uv run --env-file .env -m main --url https://ethereum.org/en/what-is-ethereum/ --save-format txt --source-dir originals --out-dir output
```

## 说明

- 腾讯云文档当前写的是 `TextTranslate` 默认 `5 次/秒`，单次文本长度低于 `6000` 字符。
- `edge-tts` 这里走命令行方式，便于和 `ffmpeg` 合并流程保持简单。
- `ffmpeg` 和 `ffprobe` 不是 Python 包，需要你本机可用；在 `PATH` 中时可直接使用，不在 `PATH` 中时再通过 `.env` 指定路径。
- 网页抓取是启发式正文提取，对强依赖 JavaScript 或强反爬的网站不一定稳定。
- 还没有加自动重试、批量翻译请求和手动修段编辑。
