from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from email_validator import validate_email, EmailNotValidError
from config import Config
from models import db, User, Game, Comment, CommentTagHistory
from urllib.parse import urlparse, urljoin
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config.from_object(Config)

# Initialize extensions
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Create upload folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Create database tables
with app.app_context():
    db.create_all()

    # Migration: Update existing comments to have target_type and target_id
    # This ensures backwards compatibility with existing data
    comments_to_migrate = Comment.query.filter(Comment.target_type == None).all()
    if comments_to_migrate:
        for comment in comments_to_migrate:
            comment.target_type = 'game'
            comment.target_id = comment.game_id
        db.session.commit()

    # Migration: Initialize soft delete fields for existing comments
    # Set is_deleted=False for any existing comments that don't have this field set
    try:
        comments_to_update = Comment.query.filter(Comment.is_deleted == None).all()
        if comments_to_update:
            for comment in comments_to_update:
                comment.is_deleted = False
            db.session.commit()
    except Exception:
        # Column might not exist yet on first run after schema update
        db.session.rollback()

    # Migration: Initialize is_admin for existing users
    try:
        users_to_update = User.query.filter(User.is_admin == None).all()
        if users_to_update:
            for user in users_to_update:
                user.is_admin = False
            db.session.commit()
    except Exception:
        # Column might not exist yet on first run after schema update
        db.session.rollback()


# Flask-Login user loader
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Helper function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


# Helper function to validate redirect URLs (prevents open redirect attacks)
def is_safe_url(target):
    """
    Validate that a redirect URL is safe (same domain).
    Prevents open redirect vulnerabilities.
    """
    if not target:
        return False
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc


def record_tag_change(comment, old_tag, new_tag, changed_by_user_id=None, changed_by='system'):
    """Record tag change in history."""
    history = CommentTagHistory(
        comment_id=comment.id,
        old_tag=old_tag,
        new_tag=new_tag,
        changed_by_user_id=changed_by_user_id,
        changed_by=changed_by
    )
    db.session.add(history)


def auto_restore_hidden_comments(comments):
    """Auto-restore comments that have been hidden for 7+ days."""
    now = datetime.utcnow()
    for comment in comments:
        if comment.tag == 'hidden' and comment.hidden_at:
            days_hidden = (now - comment.hidden_at).days
            if days_hidden >= 7:
                # Restore original tag
                old_tag = comment.tag
                comment.tag = comment.original_tag
                comment.hidden_at = None
                record_tag_change(comment, old_tag, comment.tag, changed_by='system')
        # Recursively check replies
        if comment.replies:
            auto_restore_hidden_comments(comment.replies)


def admin_required(f):
    """Decorator to require admin privileges."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Please log in to access this page.', 'warning')
            return redirect(url_for('login'))
        if not current_user.is_admin:
            flash('Admin privileges required.', 'danger')
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# AUTHENTICATION ROUTES
# ============================================================================

@app.route('/register', methods=['GET', 'POST'])
def register():
    """User registration route."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validation
        errors = []
        if not username or len(username) < 3:
            errors.append('Username must be at least 3 characters long.')
        if not email:
            errors.append('Email is required.')
        else:
            try:
                validate_email(email)
            except EmailNotValidError:
                errors.append('Invalid email address.')
        if not password or len(password) < 6:
            errors.append('Password must be at least 6 characters long.')
        if password != confirm_password:
            errors.append('Passwords do not match.')

        # Check for existing user
        if User.query.filter_by(username=username).first():
            errors.append('Username already exists.')
        if User.query.filter_by(email=email).first():
            errors.append('Email already registered.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('register.html')

        # Create new user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    """User login route."""
    if current_user.is_authenticated:
        return redirect(url_for('index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            # Validate redirect URL to prevent open redirect attacks
            next_page = request.args.get('next')
            if next_page and is_safe_url(next_page):
                return redirect(next_page)
            return redirect(url_for('index'))
        else:
            flash('Invalid username or password.', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    """User logout route."""
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


# ============================================================================
# GAME ROUTES
# ============================================================================

@app.route('/')
def index():
    """Public game list page - anyone can view."""
    games = Game.query.order_by(Game.created_at.desc()).all()
    return render_template('index.html', games=games)


@app.route('/game/upload', methods=['GET', 'POST'])
@login_required
def upload_game():
    """Game upload route - authenticated users only."""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()
        file = request.files.get('game_file')

        # Validation
        errors = []
        if not title:
            errors.append('Game title is required.')
        if not file or file.filename == '':
            errors.append('Please select a ZIP file to upload.')
        elif not allowed_file(file.filename):
            errors.append('Only ZIP files are allowed.')

        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('upload.html')

        # Save file with secure filename
        original_filename = secure_filename(file.filename)
        # Create unique filename to avoid collisions
        filename = f"{current_user.id}_{Game.query.count() + 1}_{original_filename}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # Create game record
        game = Game(
            title=title,
            description=description,
            filename=filename,
            uploader_id=current_user.id
        )
        db.session.add(game)
        db.session.commit()

        flash(f'Game "{title}" uploaded successfully!', 'success')
        return redirect(url_for('game_detail', game_id=game.id))

    return render_template('upload.html')


@app.route('/game/<int:game_id>')
def game_detail(game_id):
    """Game detail page - public, shows metadata and download button."""
    game = Game.query.get_or_404(game_id)

    # Get filter parameters
    tag_filter = request.args.get('tag_filter', '')
    show_hidden = request.args.get('show_hidden', 'false') == 'true'
    show_deleted = request.args.get('show_deleted', 'false') == 'true'

    # Check if current user is the author or admin
    is_author = current_user.is_authenticated and current_user.id == game.uploader_id
    is_admin = current_user.is_authenticated and current_user.is_admin

    # Load all top-level comments
    query = Comment.query.filter_by(game_id=game_id, parent_id=None)

    # Apply tag filter
    if tag_filter == 'no_tag':
        query = query.filter(Comment.tag.is_(None))
    elif tag_filter and tag_filter != 'all':
        query = query.filter_by(tag=tag_filter)

    comments = query.order_by(Comment.created_at.asc()).all()

    # Auto-restore hidden comments (7-day rule)
    auto_restore_hidden_comments(comments)
    db.session.commit()

    # Filter out hidden and deleted comments based on user role
    def filter_comments(comment_list):
        filtered = []
        for comment in comment_list:
            # Filter deleted comments (admin-only visibility)
            if comment.is_deleted:
                if is_admin and show_deleted:
                    filtered.append(comment)
                # Non-admins and admins without show_deleted flag: skip
                continue

            # Filter hidden comments
            if comment.tag == 'hidden':
                if is_author and show_hidden:
                    filtered.append(comment)
                # Non-authors and authors without show_hidden flag: skip
            else:
                filtered.append(comment)

            # Recursively filter replies
            if comment.replies:
                comment.replies = filter_comments(comment.replies)

        return filtered

    comments = filter_comments(comments)

    return render_template('game_detail.html', game=game, comments=comments,
                         tag_filter=tag_filter, show_hidden=show_hidden,
                         show_deleted=show_deleted, is_author=is_author, is_admin=is_admin)


@app.route('/game/<int:game_id>/download')
def download_game(game_id):
    """Download game ZIP file."""
    game = Game.query.get_or_404(game_id)
    return send_from_directory(
        app.config['UPLOAD_FOLDER'],
        game.filename,
        as_attachment=True,
        download_name=f"{game.title}.zip"
    )


@app.route('/game/<int:game_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_game(game_id):
    """Edit game metadata - only uploader can edit."""
    game = Game.query.get_or_404(game_id)

    # Authorization check
    if game.uploader_id != current_user.id:
        flash('You do not have permission to edit this game.', 'error')
        abort(403)

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        description = request.form.get('description', '').strip()

        if not title:
            flash('Game title is required.', 'error')
            return render_template('edit_game.html', game=game)

        game.title = title
        game.description = description
        db.session.commit()

        flash(f'Game "{title}" updated successfully!', 'success')
        return redirect(url_for('game_detail', game_id=game.id))

    return render_template('edit_game.html', game=game)


@app.route('/game/<int:game_id>/delete', methods=['POST'])
@login_required
def delete_game(game_id):
    """Delete game - only uploader can delete."""
    game = Game.query.get_or_404(game_id)

    # Authorization check
    if game.uploader_id != current_user.id:
        flash('You do not have permission to delete this game.', 'error')
        abort(403)

    # Delete file from filesystem
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], game.filename)
    if os.path.exists(filepath):
        os.remove(filepath)

    # Delete database record
    db.session.delete(game)
    db.session.commit()

    flash('Game deleted successfully.', 'success')
    return redirect(url_for('index'))


@app.route('/game/<int:game_id>/comment', methods=['POST'])
def post_comment(game_id):
    """Post a comment or reply to a game - open to both users and guests."""
    game = Game.query.get_or_404(game_id)

    content = request.form.get('content', '').strip()
    tag = request.form.get('tag', '').strip() or None  # Allow empty tag
    parent_id = request.form.get('parent_id', None)

    # Validation
    if not content:
        flash('Comment cannot be empty.', 'error')
        return redirect(url_for('game_detail', game_id=game_id))

    if len(content) > 1000:
        flash('Comment is too long (maximum 1000 characters).', 'error')
        return redirect(url_for('game_detail', game_id=game_id))

    # Validate tag (optional but must be valid if provided)
    ALLOWED_TAGS = ['feedback', 'bug', 'request', 'discussion']
    if tag and tag not in ALLOWED_TAGS:
        flash('Invalid tag. Please select a valid tag.', 'error')
        return redirect(url_for('game_detail', game_id=game_id))

    # Validate parent_id if provided
    if parent_id:
        try:
            parent_id = int(parent_id)
            parent_comment = Comment.query.get(parent_id)
            if not parent_comment or parent_comment.game_id != game_id:
                flash('Invalid reply target.', 'error')
                return redirect(url_for('game_detail', game_id=game_id))
        except ValueError:
            parent_id = None

    # Create comment
    comment = Comment(
        content=content,
        tag=tag,
        target_type='game',
        target_id=game_id,
        game_id=game_id,
        user_id=current_user.id if current_user.is_authenticated else None,
        guest_name='guest',  # Always 'guest' for non-authenticated users
        parent_id=parent_id
    )

    db.session.add(comment)
    db.session.commit()

    flash('Comment posted successfully!', 'success')
    return redirect(url_for('game_detail', game_id=game_id))


@app.route('/game/<int:game_id>/comment/<int:comment_id>/change_tag', methods=['POST'])
@login_required
def change_comment_tag(game_id, comment_id):
    """Change a comment's tag - only game author can do this."""
    game = Game.query.get_or_404(game_id)
    comment = Comment.query.get_or_404(comment_id)

    # Authorization check: only game author
    if game.uploader_id != current_user.id:
        flash('You do not have permission to change comment tags on this game.', 'error')
        abort(403)

    # Verify comment belongs to this game
    if comment.game_id != game_id:
        flash('Invalid comment.', 'error')
        abort(400)

    new_tag = request.form.get('new_tag', '').strip() or None

    # Validate new tag
    ALLOWED_TAGS = ['feedback', 'bug', 'request', 'discussion', 'hidden']
    if new_tag and new_tag not in ALLOWED_TAGS:
        flash('Invalid tag.', 'error')
        return redirect(url_for('game_detail', game_id=game_id))

    # Record change
    old_tag = comment.tag

    # If changing to hidden, save current tag as original_tag
    if new_tag == 'hidden':
        comment.original_tag = old_tag
        comment.hidden_at = datetime.utcnow()
    elif old_tag == 'hidden':
        # Restoring from hidden - clear hidden fields
        comment.hidden_at = None
        comment.original_tag = None

    comment.tag = new_tag

    # Record history
    record_tag_change(comment, old_tag, new_tag, current_user.id, f'user_{current_user.id}')

    db.session.commit()

    flash('Comment tag updated successfully!', 'success')
    return redirect(url_for('game_detail', game_id=game_id))


@app.route('/comment/<int:comment_id>/delete', methods=['POST'])
@admin_required
def delete_comment(comment_id):
    """Soft delete a comment - admin only."""
    comment = Comment.query.get_or_404(comment_id)

    # Get optional reason
    reason = request.form.get('reason', '').strip() or None

    # Soft delete the comment
    comment.is_deleted = True
    comment.deleted_at = datetime.utcnow()
    comment.deleted_by_user_id = current_user.id
    comment.delete_reason = reason

    db.session.commit()

    flash('Comment deleted successfully.', 'success')

    # Redirect back to the appropriate page
    if comment.target_type == 'game' and comment.target_id:
        return redirect(url_for('game_detail', game_id=comment.target_id))
    else:
        return redirect(url_for('requests_board'))


@app.route('/comment/<int:comment_id>/restore', methods=['POST'])
@admin_required
def restore_comment(comment_id):
    """Restore a soft-deleted comment - admin only."""
    comment = Comment.query.get_or_404(comment_id)

    # Restore the comment
    comment.is_deleted = False
    comment.deleted_at = None
    comment.deleted_by_user_id = None
    comment.delete_reason = None

    db.session.commit()

    flash('Comment restored successfully.', 'success')

    # Redirect back to the appropriate page
    if comment.target_type == 'game' and comment.target_id:
        return redirect(url_for('game_detail', game_id=comment.target_id))
    else:
        return redirect(url_for('requests_board'))


# ============================================================================
# REQUESTS BOARD ROUTES
# ============================================================================

@app.route('/requests')
def requests_board():
    """Requests board page - public, shows all request board comments."""
    # Get filter parameters
    tag_filter = request.args.get('tag_filter', '')
    show_deleted = request.args.get('show_deleted', 'false') == 'true'

    # Check if current user is admin
    is_admin = current_user.is_authenticated and current_user.is_admin

    # Load all top-level requests board comments
    query = Comment.query.filter_by(target_type='request', parent_id=None)

    # Apply tag filter
    if tag_filter == 'no_tag':
        query = query.filter(Comment.tag.is_(None))
    elif tag_filter and tag_filter != 'all':
        query = query.filter_by(tag=tag_filter)

    comments = query.order_by(Comment.created_at.asc()).all()

    # Auto-restore hidden comments (7-day rule)
    auto_restore_hidden_comments(comments)
    db.session.commit()

    # Filter out hidden and deleted comments
    def filter_comments(comment_list):
        filtered = []
        for comment in comment_list:
            # Filter deleted comments (admin-only visibility)
            if comment.is_deleted:
                if is_admin and show_deleted:
                    filtered.append(comment)
                # Non-admins and admins without show_deleted flag: skip
                continue

            # Filter hidden comments (no author concept on requests board, so hide from everyone)
            if comment.tag != 'hidden':
                filtered.append(comment)
                # Recursively filter replies
                if comment.replies:
                    comment.replies = filter_comments(comment.replies)
        return filtered

    comments = filter_comments(comments)

    return render_template('requests.html', comments=comments, tag_filter=tag_filter,
                         show_deleted=show_deleted, is_admin=is_admin)


@app.route('/requests/comment', methods=['POST'])
def post_request_comment():
    """Post a comment or reply on the requests board - open to both users and guests."""
    content = request.form.get('content', '').strip()
    tag = request.form.get('tag', '').strip() or None  # Allow empty tag
    parent_id = request.form.get('parent_id', None)

    # Validation
    if not content:
        flash('Comment cannot be empty.', 'error')
        return redirect(url_for('requests_board'))

    if len(content) > 1000:
        flash('Comment is too long (maximum 1000 characters).', 'error')
        return redirect(url_for('requests_board'))

    # Validate tag (optional but must be valid if provided)
    ALLOWED_TAGS = ['feedback', 'bug', 'request', 'discussion']
    if tag and tag not in ALLOWED_TAGS:
        flash('Invalid tag. Please select a valid tag.', 'error')
        return redirect(url_for('requests_board'))

    # Validate parent_id if provided
    if parent_id:
        try:
            parent_id = int(parent_id)
            parent_comment = Comment.query.get(parent_id)
            if not parent_comment or parent_comment.target_type != 'request':
                flash('Invalid reply target.', 'error')
                return redirect(url_for('requests_board'))
        except ValueError:
            parent_id = None

    # Create comment for requests board
    comment = Comment(
        content=content,
        tag=tag,
        target_type='request',
        target_id=None,
        game_id=None,  # No game association
        user_id=current_user.id if current_user.is_authenticated else None,
        guest_name='guest',  # Always 'guest' for non-authenticated users
        parent_id=parent_id
    )

    db.session.add(comment)
    db.session.commit()

    flash('Comment posted successfully!', 'success')
    return redirect(url_for('requests_board'))


if __name__ == '__main__':
    app.run(debug=True)
