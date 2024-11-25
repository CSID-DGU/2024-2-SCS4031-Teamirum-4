document.addEventListener("DOMContentLoaded", () => {
    const recommendationContainer = document.querySelector(".insurance-list");
    const recommendationData = JSON.parse(localStorage.getItem("recommendationData"));

    console.log("불러온 데이터:", recommendationData);

    if (recommendationData && Array.isArray(recommendationData.recommendations) && recommendationData.recommendations.length > 0) {
        // 추천 데이터를 기반으로 동적으로 보험 아이템 생성
        recommendationData.recommendations.forEach((item, index) => {
            const insuranceItem = document.createElement("div");
            insuranceItem.classList.add("insurance-item");

            insuranceItem.innerHTML = `
                <div class="insurance-image" style="background-image: url('../assets/images/placeholder.png');"></div>
                <div class="insurance-info">
                    <h2 class="insurance-title">추천 ${index + 1}: ${item.product_name || "추천 상품"}</h2>
                    <p class="insurance-description">${item.reason || "추천 이유를 확인할 수 없습니다."}</p>
                    <a class="btn btn-primary simulate-button" href="#">챗봇으로 시뮬레이션 돌려보기</a>
                </div>
            `;
            recommendationContainer.appendChild(insuranceItem);
        });

        // "챗봇으로 시뮬레이션 돌려보기" 버튼 클릭 이벤트 추가
        const simulateButtons = document.querySelectorAll(".simulate-button");
        simulateButtons.forEach((button) => {
            button.addEventListener("click", () => {
                window.location.href = "4.chatbot.html"; // 4.chatbot.html로 이동
            });
        });
    } else {
        // 추천 데이터가 없는 경우
        recommendationContainer.innerHTML = "<p>추천 데이터를 불러올 수 없습니다.</p>";
    }
});