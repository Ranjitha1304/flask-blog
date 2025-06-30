from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db
from app.models import User, Post, Category, Tag, Comment
from app.forms import RegisterForm, LoginForm, PostForm, CommentForm

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    query = Post.query.order_by(Post.date_posted.desc())
    
    category = request.args.get('category')
    if category:
        query = query.join(Category).filter(Category.name == category)

    tag = request.args.get('tag')
    if tag:
        query = query.join(Post.tags).filter(Tag.name == tag)

    search = request.args.get('search')
    if search:
        query = query.filter(Post.title.ilike(f"%{search}%"))

    page = request.args.get('page', 1, type=int)
    posts = query.paginate(page=page, per_page=5)

    return render_template('index.html', posts=posts)

@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        hashed = generate_password_hash(form.password.data)

        # Create user with selected role (reader or author)
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=hashed,
            role=form.role.data  # Get role from the dropdown
        )

        db.session.add(user)
        db.session.commit()
        flash('Account created! You can now log in.', 'success')
        return redirect(url_for('main.login'))

    return render_template('register.html', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)
            return redirect(url_for('main.index'))
        flash('Invalid email or password.', 'danger')
    return render_template('login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have logged out.', 'info')
    return redirect(url_for('main.index'))

@bp.route('/profile')
@login_required
def profile():
    return render_template('profile.html')

@bp.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    form.category.choices = [(c.id, c.name) for c in Category.query.all()]
    if form.validate_on_submit():
        tags = []
        for name in form.tags.data.split(','):
            name = name.strip()
            if name:
                tag = Tag.query.filter_by(name=name).first() or Tag(name=name)
                tags.append(tag)

        post = Post(
            title=form.title.data,
            content=form.content.data,
            author=current_user,
            category_id=form.category.data,
            tags=tags
        )
        db.session.add(post)
        db.session.commit()
        flash('Post created!', 'success')
        return redirect(url_for('main.index'))
    return render_template('post_form.html', form=form, title="New Post")

@bp.route('/post/<int:post_id>')
def post_detail(post_id):
    post = Post.query.get_or_404(post_id)
    form = CommentForm()
    approved_comments = Comment.query.filter_by(post_id=post_id, approved=True).order_by(Comment.date_posted.desc())
    return render_template('post_detail.html', post=post, form=form, comments=approved_comments)

@bp.route('/post/<int:post_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get_or_404(post_id)
    if current_user != post.author and current_user.role != 'admin':
        flash('Unauthorized', 'danger')
        return redirect(url_for('main.index'))

    form = PostForm(obj=post)
    form.category.choices = [(c.id, c.name) for c in Category.query.all()]
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        post.category_id = form.category.data
        post.tags.clear()
        for name in form.tags.data.split(','):
            name = name.strip()
            if name:
                tag = Tag.query.filter_by(name=name).first() or Tag(name=name)
                post.tags.append(tag)
        db.session.commit()
        flash('Post updated!', 'success')
        return redirect(url_for('main.post_detail', post_id=post.id))
    
    form.tags.data = ', '.join(tag.name for tag in post.tags)
    return render_template('post_form.html', form=form, title="Edit Post")

@bp.route('/post/<int:post_id>/delete')
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if current_user != post.author and current_user.role != 'admin':
        flash('Unauthorized', 'danger')
        return redirect(url_for('main.index'))
    db.session.delete(post)
    db.session.commit()
    flash('Post deleted!', 'info')
    return redirect(url_for('main.index'))

@bp.route('/post/<int:post_id>/comment', methods=['POST'])
@login_required
def comment_post(post_id):
    form = CommentForm()
    if form.validate_on_submit():
        comment = Comment(
            content=form.content.data,
            user=current_user,
            post_id=post_id,
            approved=False  # admin must approve
        )
        db.session.add(comment)
        db.session.commit()
        flash('Comment submitted for review.', 'info')
    return redirect(url_for('main.post_detail', post_id=post_id))

@bp.route('/moderate/comments')
@login_required
def moderate_comments():
    if current_user.role != 'admin':
        flash('Admin access required.', 'danger')
        return redirect(url_for('main.index'))
    comments = Comment.query.order_by(Comment.date_posted.desc()).all()
    return render_template('comment_moderation.html', comments=comments)

@bp.route('/approve/<int:comment_id>')
@login_required
def approve_comment(comment_id):
    if current_user.role != 'admin':
        flash('Admin access required.', 'danger')
        return redirect(url_for('main.index'))
    comment = Comment.query.get_or_404(comment_id)
    comment.approved = True
    db.session.commit()
    flash('Comment approved.', 'success')
    return redirect(url_for('main.moderate_comments'))

@bp.route('/delete_comment/<int:comment_id>')
@login_required
def delete_comment(comment_id):
    if current_user.role != 'admin':
        flash('Admin access required.', 'danger')
        return redirect(url_for('main.index'))
    comment = Comment.query.get_or_404(comment_id)
    db.session.delete(comment)
    db.session.commit()
    flash('Comment deleted.', 'info')
    return redirect(url_for('main.moderate_comments'))
