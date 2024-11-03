from flask import Flask, jsonify, render_template, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import os
import base64

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{os.environ.get('DB_USERNAME')}:{os.environ.get('DB_PASSWORD')}@"
    f"{os.environ.get('DB_HOST')}:{os.environ.get('DB_PORT')}/{os.environ.get('DB_NAME')}"
)
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Article 모델
class Article(db.Model):
    __tablename__ = 'article'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    content = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(100), nullable=False)
    files = db.relationship('InsertedFile', back_populates='article', cascade="all, delete-orphan", lazy='dynamic')
    comments = db.relationship('Comment', back_populates='article', cascade="all, delete-orphan", lazy='dynamic')

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "author": self.author,
            "files": [file.to_dict() for file in self.files],
            "comments": [comment.to_dict() for comment in self.comments]
        }

# Comment 모델
class Comment(db.Model):
    __tablename__ = 'comment'
    comment_id = db.Column(db.Integer, primary_key=True)
    comment_author = db.Column(db.String(100), nullable=False)
    comment_content = db.Column(db.Text, nullable=False)
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    article = db.relationship('Article', back_populates='comments')
    parent_comment_id = db.Column(db.Integer, db.ForeignKey('comment.comment_id'))
    parent_comment = db.relationship('Comment', remote_side=[comment_id], backref='child_comments')

    def to_dict(self):
        return {
            "comment_id": self.comment_id,
            "comment_author": self.comment_author,
            "comment_content": self.comment_content,
            "child_comments": [child.to_dict() for child in self.child_comments]
        }

class InsertedFile(db.Model):
    __tablename__ = 'inserted_file'
    id = db.Column(db.Integer, primary_key=True)
    uuid_file_name = db.Column(db.String(255), nullable=False)
    original_file_name = db.Column(db.String(255), nullable=False)
    file_data = db.Column(db.LargeBinary, nullable=True)  # Store image as BLOB
    article_id = db.Column(db.Integer, db.ForeignKey('article.id'), nullable=False)
    article = db.relationship('Article', back_populates='files')

    def to_dict(self):
        return {
            "id": self.id,
            "uuid_file_name": self.uuid_file_name,
            "original_file_name": self.original_file_name,
            "image_data": "data:image/png;base64," + base64.b64encode(self.file_data).decode('utf-8') if self.file_data else None
        }


# User 모델
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), nullable=False, unique=True)
    nickname = db.Column(db.String(100), unique=True)
    profile_image = db.Column(db.LargeBinary)
    profile_url = db.Column(db.String(255))
    role = db.Column(db.String(50))

    def to_dict(self):
        return {
            "id": self.id,
            "email": self.email,
            "nickname": self.nickname,
            "profile_url": self.profile_url,
            "role": self.role,
            "profile_image": self.get_profile_image_as_base64()
        }

    def get_profile_image_as_base64(self):
        if self.profile_image:
            return "data:image/png;base64," + base64.b64encode(self.profile_image).decode('utf-8')
        return None

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/users', methods=['GET'])
def user_home():
    return render_template('user.html')


@app.route('/api/articles', methods=['GET'])
def get_articles():
    try:
        articles = Article.query.all()
        return jsonify([article.to_dict() for article in articles]), 200
    except Exception as e:
        print("Error fetching articles:", e)  # 콘솔에 에러 메시지 출력
        return jsonify({"error": str(e)}), 500

@app.route('/api/users', methods=['GET'])
def get_users():
    try:
        users = User.query.all()
        return jsonify([user.to_dict() for user in users]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/upload/file', methods=['GET'])
def get_file():
    article_id = request.args.get('articleId')
    uuid_file_name = request.args.get('uuidFileName')

    # 데이터베이스에서 해당 파일 조회
    file_record = InsertedFile.query.filter_by(article_id=article_id, uuid_file_name=uuid_file_name).first()

    if file_record:
        # 이미지 데이터 반환
        return (file_record.file_data, 200, {'Content-Type': 'image/png'})
    else:
        return jsonify({"error": "File not found"}), 404

# 데이터베이스 article 엔티티 안에, content 칼럼에 텍스트 뿐만이 아니라, 이미지도 담겨있어서 1차로 조회되고
# 2차로 조회되는게 별도의 엔티티에서 다시 불러오는 것 (인공지능 모델에 어느쪽을 넣어도 상관은 없다)


if __name__ == '__main__':
    app.run(debug=True)