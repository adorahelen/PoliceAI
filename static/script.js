async function fetchChatGPTAnalysis() {
    try {
        const response = await fetch('/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ message: "전화번호 분석 요청 메시지" })  // 필요한 메시지를 입력
        });

        const data = await response.json();

        if (data.reply) {
            // `/answer` 페이지로 이동하며 `result` 데이터를 전달
            window.location.href = `/answer?result=${encodeURIComponent(data.reply)}`;
        } else {
            console.error("분석 결과가 없습니다.");
        }
    } catch (error) {
        console.error("Error during fetchChatGPTAnalysis:", error);
    }
}