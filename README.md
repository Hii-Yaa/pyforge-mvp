
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

## Comment Reporting（コメント通報機能）

コミュニティの健全性を保つため、誰でもコメントを通報できる機能を実装しています。

### できること

#### 1. コメントの通報（誰でも可能）
- **誰でも通報可能**：ログインユーザーはもちろん、ゲストユーザーも通報できます
- 各コメントに「Report」ボタンが表示されます（ゲーム詳細ページ、Requests Boardの両方）
- **通報理由の入力**：
  - 「Report」ボタンをクリックすると理由入力フォームが展開されます
  - 理由は任意（空でもOK）、最大200文字まで入力できます
  - 管理画面で最新の通報理由を確認できます

#### 2. 二重通報防止
- **24時間以内の連打を防止**：同じユーザー（またはIP）が同じコメントを24時間以内に複数回通報できません
- ログインユーザーは `user_id` で、ゲストは `IP address` で識別します
- 既に通報済みの場合は「already reported」メッセージが表示されます

#### 3. 管理者専用機能
- **通報数の表示**：管理者だけが各コメントの横に「Reports: N」という通報数を見ることができます
- **通報一覧ページ（Admin Reports Dashboard）**：
  - ナビゲーションに「Admin Reports (N)」リンクが表示されます（**Nは未対応の通報付きコメント数**）
  - `/admin/reports` で通報されたコメント一覧を確認できます
  - **フィルタ機能**：
    - Status: Unresolved（未対応）/ Resolved（対応済み）/ All
    - デフォルトは Unresolved（未対応のみ表示）
  - **ソート機能**：
    - Sort by: Latest Report（最新通報日時）/ Report Count（通報数）
    - Order: Descending（降順）/ Ascending（昇順）
  - **表示内容**：
    - Reports（通報数）
    - Latest Report（最新通報日時）
    - Report Reason（最新の通報理由）
    - Comment（コメント内容）
    - Author（投稿者）
    - Posted（投稿日時）
    - Location（ゲーム or リクエストボードへのリンク）
    - **Status（対応状態）**：Unresolved / Resolved（対応日時と担当者も表示）
  - **対応アクション**：
    - **Mark Resolved**：通報を対応済みにする（対応済みカラムに日時と担当者が記録されます）
    - **Mark Unresolved**：対応済みを未対応に戻す
    - Delete / Restore：コメントの削除・復元（従来通り）
  - 対応済みの行は緑色の背景で表示されます

#### 4. プライバシー保護
- **通報数は一般ユーザーには表示されません**：管理者のみが確認できます
- 通報者の情報（IPアドレス等）は一般ユーザーには公開されません

### 管理画面の使い方

#### 通報の確認と対応
1. 管理者としてログインすると、ナビゲーションに「Admin Reports (N)」が表示されます
2. クリックすると、未対応の通報一覧が表示されます（デフォルトで Unresolved フィルタ）
3. 各通報を確認し、適切な対応を行います：
   - 問題がある場合：「Delete」でコメントを削除
   - 問題がない場合：「Mark Resolved」で対応済みにする
4. 対応済みにすると、その通報は Resolved 状態になり、ナビのバッジカウントから除外されます
5. 必要に応じて「Mark Unresolved」で未対応に戻すこともできます

#### フィルタとソートの活用
- **Status を切り替えて**：
  - Unresolved：未対応の通報のみ確認（デフォルト）
  - Resolved：対応済みの通報を確認
  - All：すべての通報を表示
- **Sort by を切り替えて**：
  - Latest Report：最新の通報から確認
  - Report Count：通報数が多い順に確認（緊急度が高い可能性）

### テクニカル詳細
- データベースに `Report` テーブルを追加
- フィールド：
  - `comment_id`（通報対象のコメント）
  - `reporter_user_id`（ログインユーザーの場合）
  - `reporter_ip`（IPアドレス、取得可能な範囲で）
  - `reason`（通報理由、任意）
  - `created_at`（通報日時）

---

### データ保存（SQLite）
- ローカルでは SQLite を使用します。
- DBファイルはプロジェクトの `instance/` 配下（例：`instance/app.db`）に作成されます。

---

### 今後の拡張候補（アイデア）
- コメント本文検索、並び替え（新しい順/古い順）
- ~~通報機能（通報数を管理者が確認）~~ ✅ 実装済み (v0.4 Comment Reporting)
- ~~管理者アカウント（is_admin）と管理画面（通報/hidden一覧、削除判断など）~~ ✅ 実装済み (v0.4 Admin Reports Dashboard)
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

### Comment Reporting (v0.4)
- Anyone can report comments (including guests)
- Duplicate report prevention (24-hour cooldown per user/IP)
- Report counts are visible only to admins
- Admin dashboard at `/admin/reports` shows:
  - All reported comments
  - Report counts and latest report timestamps
  - Direct links to comment locations (game or requests board)
  - Quick actions: delete or restore comments
- Navigation badge shows number of reported comments (admin only)

## Routes (High-level)
- `/` : Game list
- `/register`, `/login`, `/logout`
- `/game/upload`
- `/game/<id>` : Game detail + comments
- `/game/<id>/download`
- `/game/<id>/edit` (author only)
- `/game/<id>/delete` (author only)
- `/requests` : Global requests board
- `/comment/<id>/report` : Report a comment (anyone)
- `/admin/reports` : Admin reports dashboard (admin only)

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
