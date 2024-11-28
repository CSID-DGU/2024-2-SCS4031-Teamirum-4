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
        const insuranceItem = document.createElement("div");
        insuranceItem.classList.add("insurance-item");

        // 추천 상품 HTML 구조
        insuranceItem.innerHTML = `
            <div class="insurance-image" style="background-image: url('../assets/images/placeholder.png');"></div>
            <div class="insurance-info">
                <h2 class="insurance-title">추천 ${index + 1}: ${item.product_name || "상품 이름 없음"}</h2>
                <p class="insurance-description">${item.reason || "추천 이유가 제공되지 않았습니다."}</p>
                <a class="btn btn-primary simulate-button" href="#">챗봇으로 시뮬레이션 돌려보기</a>
            </div>
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