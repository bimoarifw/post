from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    make_response,
    escape,
)
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import desc
from flask_migrate import Migrate
import secrets
import os
from flask import send_from_directory

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///posts.db"
app.secret_key = secrets.token_hex(16)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100))
    content = db.Column(db.String(300))
    anonymous = db.Column(db.Boolean)
    created_at = db.Column(db.DateTime, default=datetime.now)
    like_count = db.Column(db.Integer, default=0)
    unlike_count = db.Column(db.Integer, default=0)


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(
        os.path.join(app.root_path, "static"),
        "favicon.ico",
        mimetype="image/vnd.microsoft.icon",
    )


@app.route("/", methods=["GET", "POST"])
def index():
    anonymous = False
    page = request.args.get("page", 1, type=int)
    per_page = 5
    total_pages = len(Post.query.all()) // per_page + 1
    current_time = datetime.now()
    if request.method == "POST":
        username = request.form.get("username")
        content = request.form["content"]

        if not username:
            username = "Anonymous"
        content = escape(content)
        post = Post(
            username=username,
            content=content,
            anonymous=("anonymous" in request.form),
            like_count=1,
            unlike_count=0,
        )
        db.session.add(post)
        db.session.commit()

        return redirect(url_for("index", page=page))

    total_pages = len(Post.query.all()) // per_page + 1

    offset = (page - 1) * per_page
    limit = per_page

    posts = Post.query.order_by(desc(Post.created_at)).offset(offset).limit(limit).all()

    top_liked_posts = Post.query.order_by(desc(Post.like_count)).limit(5).all()

    return render_template(
        "index.html",
        posts=posts,
        top_liked_posts=top_liked_posts,
        anonymous=anonymous,
        total_pages=total_pages,
        page=page,
        current_time=current_time,
    )


@app.route("/like/<int:post_id>")
def like(post_id):
    page = request.args.get("page", 1, type=int)
    post = Post.query.get(post_id)
    if post is not None:
        liked_cookie = request.cookies.get(f"liked_post_{post_id}")

        if liked_cookie is None:
            post.like_count += 1
        else:
            post.like_count -= 1
            if post.like_count < 0:
                post.like_count = 0

        db.session.commit()

        response = make_response(redirect(url_for("index", page=page)))
        if liked_cookie is None:
            response.set_cookie(f"liked_post_{post_id}", "true")
        else:
            response.delete_cookie(f"liked_post_{post_id}")
        return response

    return redirect(url_for("index", page=page))


@app.route("/unlike/<int:post_id>")
def unlike(post_id):
    page = request.args.get("page", 1, type=int)
    post = Post.query.get(post_id)
    if post is not None:
        unliked_cookie = request.cookies.get(f"unliked_post_{post_id}")

        if unliked_cookie is None:
            post.unlike_count += 1
        else:
            post.unlike_count -= 1
            if post.unlike_count < 0:
                post.unlike_count = 0

        db.session.commit()

        response = make_response(redirect(url_for("index", page=page)))
        if unliked_cookie is None:
            response.set_cookie(f"unliked_post_{post_id}", "true")
        else:
            response.delete_cookie(f"unliked_post_{post_id}")
        return response

    return redirect(url_for("index", page=page))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
