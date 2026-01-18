
## PyForge MVP

### 概要
Python製ゲーム投稿プラットフォームのMVP。

### 機能
- ゲーム一覧表示
- ゲーム投稿
- ゲーム詳細表示
- 削除

### 起動方法
```bash
pip install -r requirements.txt
python app.py
```

### 技術スタック

Flask

SQLite

Jinja2

## Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python app.py
```
Open http://127.0.0.1:5000

## MVP Scope
This MVP focuses on backend completeness.
UI/UX improvements are intentionally postponed.

Implemented:
- User authentication
- Game upload (ZIP)
- Public listing & download
- Owner-only edit/delete

## Comments (v0.2)
- Anyone can post comments (logged-in users or guests)
- Guest comments are posted as "guest"
- Comments support replies using parent-child relationships
- Comments are always visible below the download link
