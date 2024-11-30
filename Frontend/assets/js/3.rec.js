document.addEventListener("DOMContentLoaded", () => {
    const recommendationContainer = document.querySelector(".insurance-list");

    // 로컬 저장소에서 추천 데이터 가져오기
    const recommendationData = JSON.parse(localStorage.getItem("recommendationData"));

    // 추천 데이터 디버깅 로그
    console.log("로컬 저장소에서 불러온 데이터:", recommendationData);

    // 추천 데이터가 없을 경우 처리
    if (!recommendationData || !Array.isArray(recommendationData.recommendations)) {
        recommendationContainer.innerHTML = "<p>추천 데이터를 불러올 수 없습니다. 다시 시도해주세요.</p>";
        return;
    }

    // 추천 데이터가 있을 경우 화면에 추가
    recommendationData.recommendations.forEach((item, index) => {
        const cleanedTitle = (item.product_name || "상품 이름 없음")
            .replace(/^추천\s*/, "") // "추천" 텍스트만 제거
            .replace(/\.pdf$/i, ""); // ".pdf" 텍스트 제거

        const cleanedReasonMatch = (item.reason || "").match(/['"”](.*?)['"”]|\((.*?)\)/);
        const extractedReason = cleanedReasonMatch
            ? cleanedReasonMatch[1] || cleanedReasonMatch[2] || "연관 이유 없음"
            : "연관 이유 없음";

        const finalReason = `연관 이유: ${extractedReason}`;

        // 추천 상품 HTML 구조 생성
        const insuranceItem = document.createElement("div");
        insuranceItem.className = "insurance-item";
        insuranceItem.innerHTML = `
            <div class="insurance-image"></div>
            <div class="insurance-info">
                <h2 class="insurance-title">${cleanedTitle}</h2>
                <p class="insurance-description">${finalReason}</p>
                <a class="btn btn-secondary simulate-button" style="padding: 6px 12px; font-size: 12px; background-color: #5a7d9a; color: white; border: none;" href="#">챗봇으로 시뮬레이션 돌려보기</a>
            </div>
            <hr style="border: none; height: 1px; background-color: #e0e0e0; margin: 20px 0;">
        `;
        recommendationContainer.appendChild(insuranceItem);
    });

    // 버튼 클릭 시 이동 이벤트 추가
    const simulateButtons = document.querySelectorAll(".simulate-button");
    simulateButtons.forEach((button) => {
        button.addEventListener("click", () => {
            window.location.href = "4.chatbot.html"; // 4.chatbot.html로 이동
        });
    });
});