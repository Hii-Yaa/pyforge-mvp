
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

## Requests Board (v0.3)
- Global discussion board accessible from the navigation menu
- Separate from per-game comments - for platform-wide requests and feedback
- Anyone can post (logged-in users or guests, default guest name: "guest")
- Supports nested replies via parent_id (same as game comments)
- Tag system: feedback, bug, request, discussion, or no tag
- Tag filtering available (same as game comments)
- No author concept (unlike game comments, no special permissions)
- Hidden comments automatically filtered out for all users

## コメント機能（MVP）

ゲーム詳細ページ（Downloadリンクの下）にコメント欄があります。  
ログインなしでも投稿でき、返信（スレッド）も可能です。作者側が議論を整理・運用しやすいように、タグ・絞り込み・一時非表示（期限付き）も用意しています。

### できること

#### 1. コメント投稿（ログイン不要）
- ログインしていなくてもコメント投稿ができます（ゲスト扱い）。
- ゲスト名はデフォルトで `guest` になります。
- コメント内容は空文字不可（簡易バリデーションあり）。

#### 2. 返信（コメントにコメント）
- コメントはスレッド形式です（親コメントに対して返信可能）。
- 返信はネスト（入れ子）できます（parent_id を使用）。
- 各コメントの「Reply」ボタンで返信フォームを表示します（最小限のJS）。

#### 3. タグ（任意）と絞り込み
- コメントにはタグを付けられます（任意）。
- タグ未指定でも投稿できます（`-- No Tag --`）。
- コメント一覧はタグで絞り込み表示できます（Filter by tag）。
- 「Show Hidden」を有効にすると、一時非表示（Hidden）のコメントも表示できます（主に作者向け）。

#### 4. 作者コメントの強調表示
- ゲーム作者（アップロード者）のコメントには ★ を表示します。
- 作者のユーザー名部分は背景グレーで強調表示します。

#### 5. 作者によるタグ変更（整理用）
- ゲーム作者は、コメントのタグを後から変更できます。
- 例：感想/バグ/要望/議論 など、議論を分類して追いやすくできます。

#### 6. 一時非表示（Hidden）＋自動復帰＋履歴
- ゲーム作者は特定コメントを「Hidden」扱いにできます。
- Hidden コメントは **作者以外には非表示** です。
- 作者側でもデフォルトでは Hidden は表示されず、「Show Hidden」で表示できます。
- Hidden は **1週間後に自動で元のタグに復帰** します（永久に消し続けない設計）。
- タグ変更やHidden化/復帰は履歴としてDBに記録されます（監査ログ）。

---

## Requests Board（要望掲示板）

ナビゲーションメニューから「Requests」をクリックすると、サイト全体への要望や議論を投稿できる専用ページが開きます。

### できること

#### 1. グローバルな議論の場
- ゲーム個別のコメントとは別に、プラットフォーム全体への要望・フィードバック・バグ報告などを投稿できます。
- ゲストでもログインユーザーでも投稿可能（ゲスト名はデフォルトで `guest`）。

#### 2. ゲームコメントと同じ機能
- 返信機能（parent_id によるネスト対応）
- タグ機能（感想/バグ/要望/議論/タグなし）
- タグによる絞り込み表示

#### 3. ゲームコメントとの違い
- 特定のゲームに紐づかない（プラットフォーム全体の掲示板）
- 作者という概念がないため、タグ変更や★マークなどの権限機能はなし
- Hiddenコメントは全員に非表示

---

### データ保存（SQLite）
- ローカルでは SQLite を使用します。
- DBファイルはプロジェクトの `instance/` 配下（例：`instance/app.db`）に作成されます。

---

### 今後の拡張候補（アイデア）
- コメント本文検索、並び替え（新しい順/古い順）
- 通報機能（通報数を管理者が確認）
- 管理者アカウント（is_admin）と管理画面（通報/hidden一覧、削除判断など）
- ~~ホームに「サイト全体への要望」掲示板（グローバルスレッド）~~ ✅ 実装済み (v0.3 Requests Board)
- スパム対策（レート制限、CAPTCHA、NGワードなど）

## Features (MVP)

### Accounts
- User registration / login / logout (Flask-Login)
- Passwords are stored as secure hashes (bcrypt)

### Game Posting
- Upload a ZIP file as a game
- Public game list
- Game detail page
- Download ZIP
- Only the author can edit/delete their game

### Comments (Per-Game)
- Anyone can post comments (guest posting allowed; default guest name: "guest")
- Nested replies (comment threads)
- Optional tags: feedback / bug / request / discussion (tag can be empty)
- Filter comments by tag
- Author highlight:
  - Author comments show a ★
  - Author username area has a gray background
- Author can change comment tags for organization
- Optional moderation flow (current behavior if enabled):
  - "hidden" tag can temporarily hide comments from others
  - hidden is auto-restored after 7 days
  - tag changes are recorded in history

### Global Requests Board
- A separate page for site-wide requests, feedback, and discussion
- Same comment system as per-game comments:
  - guest posting, nested replies, optional tags, tag filtering

## Routes (High-level)
- `/` : Game list
- `/register`, `/login`, `/logout`
- `/game/upload`
- `/game/<id>` : Game detail + comments
- `/game/<id>/download`
- `/game/<id>/edit` (author only)
- `/game/<id>/delete` (author only)
- `/requests` : Global requests board

## Data Storage
- SQLite database file: `instance/app.db`
- Uploaded files are stored under: `uploads/`

## Run Locally
```bash
pip install -r requirements.txt
python app.py
```
Then open: http://localhost:5000

## Bootstrap Admin Account

For local development convenience, a default admin account is automatically created on startup:

**Credentials:**
- Username: `admin`
- Password: `admin`
- Email: `admin@local`

**⚠️ IMPORTANT SECURITY NOTES:**
1. **Change the password immediately** after first login!
2. This bootstrap account is intended for **local development only**
3. For production deployments, disable bootstrap admin by setting:
   ```bash
   export DISABLE_BOOTSTRAP_ADMIN=1
   ```

**Bootstrap Behavior:**
- If `admin` user doesn't exist → creates it with default credentials
- If `admin` user exists but isn't admin → promotes to admin role
- If `admin` user exists and is admin → no changes (password is NOT reset)
- Startup logs will indicate what action was taken

**Production Setup:**
1. Set `DISABLE_BOOTSTRAP_ADMIN=1` environment variable
2. Create admin account manually via registration
3. Promote to admin via database or migration script
