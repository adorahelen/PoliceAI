from flask import Flask, jsonify, render_template, request
import requests
from bs4 import BeautifulSoup


from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from dotenv import load_dotenv
import os
import base64
import logging
import re


app = Flask(__name__)

# .env 파일에서 API 키 불러오기
load_dotenv()
API_KEY = os.getenv("OPENAI_API_KEY")

# 로깅 설정 (콘솔에 에러 메시지를 출력)
logging.basicConfig(level=logging.INFO)

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



def contains_phone_number(text):
    # HTML 태그 제거
    soup = BeautifulSoup(text, "html.parser")
    clean_text = soup.get_text()
    clean_text = clean_text.replace("&nbsp;", " ")

    # 전화번호 형식 검출 (다양한 형식 지원)
    pattern = r"\b\d{2,3}-\d{3,4}-\d{4}\b"
    return re.search(pattern, clean_text) is not None

def check_phone_numbers(article):
    try:
        api_url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": article['content']}]
        }

        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()
        reply = response.json()['choices'][0]['message']['content']

        # 패턴 확인 로깅 추가
        logging.info(f"API 응답 내용: {reply}")

        phone_pattern = re.compile(r'\b\d{2,3}-\d{3,4}-\d{4}\b')
        found_numbers = phone_pattern.findall(reply)

        if found_numbers:
            logging.info(f"전화번호 발견: {found_numbers} - 게시물 제목: {article['title']}")
        else:
            logging.info("전화번호가 발견되지 않았습니다.")

    except requests.exceptions.RequestException as e:
        logging.error(f"API 요청 오류: {e}")
    except Exception as e:
        logging.error(f"예상치 못한 오류: {e}")

@app.route('/chat', methods=['POST'])
def chat_with_gpt():
    try:
        # ChatGPT API URL과 헤더를 여기서 정의
        api_url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }

        articles = Article.query.all()
        detected_entries = []

        for article in articles:
            if contains_phone_number(article.title) or contains_phone_number(article.content):
                detected_entries.append({
                    "title": article.title,
                    "content": article.content,
                    "author": article.author,
                    "analysis_result": None
                })
                check_phone_numbers(article)  # 전화번호 확인 호출

            for comment in article.comments:
                if contains_phone_number(comment.comment_content):
                    detected_entries.append({
                        "comment_author": comment.comment_author,
                        "comment_content": comment.comment_content,
                        "analysis_result": None
                    })
                    check_phone_numbers(comment)  # 댓글에 대한 전화번호 확인 호출

        # ChatGPT API를 통해 분석 요청
        for entry in detected_entries:
            content_text = entry.get("content") or entry.get("comment_content")
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "음란물 및 민감 정보 분석 시스템입니다."},
                    {"role": "user", "content": f"분석할 텍스트: {content_text}"}
                ]
            }

            response = requests.post(api_url, headers=headers, json=payload)
            response.raise_for_status()

            analysis_result = response.json()['choices'][0]['message']['content']
            entry['analysis_result'] = analysis_result

        return render_template('answer.html', results=detected_entries)

    except requests.exceptions.RequestException as e:
        logging.error(f"ChatGPT API request failed: {e}")
        return jsonify({"error": "ChatGPT API 요청 실패"}), 500

    except Exception as e:
        logging.error(f"Server error: {e}")
        return jsonify({"error": "서버에서 오류가 발생했습니다."}), 500





# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/question')
def question():
    return render_template('question.html')
# 인공지능 프로젝트의 목적을 설명하고 버튼을 통해 인공지능 분석을 시작하는 페이지

@app.route('/answer')
def display_answer():
    result = "AI 분석 결과를 표시할 내용입니다."  # 예시 데이터
    return render_template('answer.html', result=result)

@app.route('/api/articles', methods=['GET'])
def get_articles():
    try:
        articles = Article.query.all()
        return jsonify([article.to_dict() for article in articles]), 200
    except Exception as e:
        print("Error fetching articles:", e)  # 콘솔에 에러 메시지 출력
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