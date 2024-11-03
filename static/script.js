// script.js
function startAnalysis() {
    fetch('/chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ message: "인공지능 분석을 시작합니다." })
    })
    .then(() => {
        // 분석 결과 페이지로 이동
        window.location.href = '/answer';
    })
    .catch(error => console.error('Error:', error));
}