from flask import Flask, jsonify, render_template, request
import requests

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


# 게시글 중에서, 인공지능에 넣을 데이터만 별도 조회 (전처리 작업)
@app.route('/api/articles/simple', methods=['GET'])
def get_articles_simple():
    try:
        # 데이터베이스에서 모든 Article 객체를 조회합니다.
        articles = Article.query.all()

        # 각 게시글의 제목과 내용을 "Title: 제목, Content: 내용" 형식의 문자열로 변환 후 줄바꿈으로 연결합니다.
        formatted_articles = "\n".join([f"Title: {article.title}, Content: {article.content}" for article in articles])

        # 변환된 문자열을 콘솔에 출력합니다.
        print(formatted_articles)

        # 가공된 데이터 `formatted_articles`를 JSON 형식으로 반환합니다.
        return jsonify({"formatted_articles": formatted_articles}), 200
    except Exception as e:
        # 오류 발생 시 에러 메시지를 콘솔에 출력하고 JSON 형식으로 반환합니다.
        print("Error fetching articles:", e)
        return jsonify({"error": str(e)}), 500


# 조회된 데이터를 chatGPT(LLM) 활용하여 분석 (전처리 된 데이터 -> 모델 입력[학습 완료된] )
@app.route('/chat', methods=['POST'])
def chat_with_gpt():
    try:
        # `get_articles_simple` 함수 호출해 게시글 데이터를 가져옵니다.
        articles_response = get_articles_simple()

        # `get_articles_simple`의 HTTP 상태 코드가 200(성공)이 아닌 경우 오류 메시지를 반환합니다.
        if articles_response[1] != 200:
            return jsonify({"error": "Articles could not be fetched"}), 500

        # 정상적으로 가져온 경우 JSON 데이터에서 `formatted_articles` 키의 값을 추출합니다.
        articles_content = articles_response[0].json["formatted_articles"]

        # ChatGPT API 호출을 위한 URL과 헤더, 페이로드 설정
        api_url = "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {API_KEY}",  # API 인증을 위해 `API_KEY` 사용
            "Content-Type": "application/json"
        }

        # ChatGPT에 전달할 메시지와 추가 질문 설정
        user_input = f"{articles_content}\n\nHow many phone number patterns are detected in this data?"
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": user_input}]
        }

        # API에 POST 요청 보내기
        response = requests.post(api_url, headers=headers, json=payload)
        response.raise_for_status()  # 응답 상태가 오류인 경우 예외를 발생시킵니다.

        # 응답에서 ChatGPT가 생성한 답변 내용 추출
        reply = response.json()['choices'][0]['message']['content']

        # ChatGPT의 답변을 JSON 형식으로 반환
        return jsonify({"reply": reply})

    except Exception as e:
        # 오류 발생 시 콘솔에 에러 메시지를 출력하고 JSON 형식으로 반환
        print("Error during GPT request:", e)
        return jsonify({"error": str(e)}), 500

# Routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/question')
def question():
    return render_template('question.html')


@app.route('/answer')
def display_answer():
    # URL의 쿼리 파라미터에서 `result` 값을 가져옵니다.
    # ex: http://127.0.0.1:5000/answer?result=There%20are%202%20phone%20number%20patterns%20detected%20in%20this%20data.
    # 만약 `result` 값이 없으면 기본 값 "AI 분석 결과를 표시할 내용입니다."을 사용합니다.
    result = request.args.get('result', "AI 분석 결과를 표시할 내용입니다.")

    # `result` 값을 `answer.html` 템플릿으로 전달
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