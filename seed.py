from app import create_app, db
from app.models import User, Category, Tag, Post, Comment
from werkzeug.security import generate_password_hash
from datetime import datetime
import random

app = create_app()

with app.app_context():
    # Clear all existing data (optional)
    db.drop_all()
    db.create_all()

    # Create Users
    admin = User(username='admin', email='admin@example.com', password=generate_password_hash('123456'), role='admin')
    author = User(username='author1', email='author@example.com', password=generate_password_hash('123456'), role='author')
    reader = User(username='reader1', email='reader@example.com', password=generate_password_hash('123456'), role='reader')

    db.session.add_all([admin, author, reader])
    db.session.commit()

    # Create Categories
    categories = [Category(name='Tech'), Category(name='Life'), Category(name='Travel')]
    db.session.add_all(categories)
    db.session.commit()

    # Create Tags
    tag_python = Tag(name='Python')
    tag_flask = Tag(name='Flask')
    tag_lifestyle = Tag(name='Lifestyle')
    db.session.add_all([tag_python, tag_flask, tag_lifestyle])
    db.session.commit()

    # Create Posts
    post1 = Post(
        title='Getting Started with Flask',
        content='Flask is a micro web framework...',
        author=author,
        category=categories[0],
        tags=[tag_python, tag_flask],
        date_posted=datetime.utcnow()
    )

    post2 = Post(
        title='My Trip to the Mountains',
        content='Traveling helps refresh the soul...',
        author=author,
        category=categories[2],
        tags=[tag_lifestyle],
        date_posted=datetime.utcnow()
    )

    db.session.add_all([post1, post2])
    db.session.commit()

    # Create Comments
    comment1 = Comment(content="Great article!", user=reader, post=post1, approved=True)
    comment2 = Comment(content="I want to try Flask.", user=reader, post=post1, approved=False)
    comment3 = Comment(content="Awesome journey!", user=reader, post=post2, approved=True)

    db.session.add_all([comment1, comment2, comment3])
    db.session.commit()

    print("✅ Sample data seeded successfully.")
