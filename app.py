from flask import Flask, render_template, request, redirect, url_for, flash, send_from_directory, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from email_validator import validate_email, EmailNotValidError
from config import Config
from models import db, User, Game, Comment
from urllib.parse import urlparse, urljoin
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
    # Load all comments for this game, ordered by creation time
    comments = Comment.query.filter_by(game_id=game_id, parent_id=None).order_by(Comment.created_at.asc()).all()
    return render_template('game_detail.html', game=game, comments=comments)


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
    tag = request.form.get('tag', '').strip()
    parent_id = request.form.get('parent_id', None)

    # Validation
    if not content:
        flash('Comment cannot be empty.', 'error')
        return redirect(url_for('game_detail', game_id=game_id))

    if len(content) > 1000:
        flash('Comment is too long (maximum 1000 characters).', 'error')
        return redirect(url_for('game_detail', game_id=game_id))

    # Validate tag
    ALLOWED_TAGS = ['feedback', 'bug', 'request', 'discussion']
    if not tag or tag not in ALLOWED_TAGS:
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
        game_id=game_id,
        user_id=current_user.id if current_user.is_authenticated else None,
        guest_name='guest',  # Always 'guest' for non-authenticated users
        parent_id=parent_id
    )

    db.session.add(comment)
    db.session.commit()

    flash('Comment posted successfully!', 'success')
    return redirect(url_for('game_detail', game_id=game_id))


if __name__ == '__main__':
    app.run(debug=True)
