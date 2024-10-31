from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    # 텍스트와 이미지 데이터 수신
    text = request.form.get('text')
    image = request.files.get('image')

    # 간단한 처리 예제 (AI 분석 대신 가짜 결과 반환)
    text_result = f"'{text}' 분석 완료 (비속어 없음)"
    image_result = "이미지 분석 완료 (음란물 아님)"

    # 결과 페이지에 표시
    return render_template('result.html', text_result=text_result, image_result=image_result)

if __name__ == '__main__':
    app.run(debug=True)