document.addEventListener("DOMContentLoaded", () => {
    console.log("3.rec.js 실행됨");

    const recommendationContainer = document.querySelector(".insurance-list");

    // 로컬 스토리지에서 추천 데이터 가져오기
    const recommendationData = JSON.parse(localStorage.getItem("recommendationData"));
    console.log("로컬 스토리지에서 불러온 추천 데이터:", recommendationData);

    // 사용자 이름 가져오기
    const userName = localStorage.getItem("userName") || "고객";

    // 추천 데이터가 없거나 잘못된 경우 처리
    if (!recommendationData || !Array.isArray(recommendationData.recommendations)) {
        recommendationContainer.innerHTML = "<p>추천 데이터를 불러올 수 없습니다. 다시 시도해주세요.</p>";
        console.error("추천 데이터가 유효하지 않습니다. 데이터:", recommendationData);
        return;
    }

    // 제목 추가 (사용자 이름 포함)
    const titleElement = document.createElement("h1");
    titleElement.className = "form-title"; // 동일한 스타일 적용
    titleElement.textContent = `${userName}님의 정보에 기반하여 추천하는 보험 상품입니다.🤓`;

    // 제목을 페이지에 추가
    const container = document.querySelector(".container");
    container.insertBefore(titleElement, container.firstChild);

    // 추천 데이터를 화면에 표시
    recommendationData.recommendations.forEach((item) => {
        const cleanedTitle = (item.product_name || "상품 이름 없음")
            .replace(/^추천\s*/, "") // "추천" 접두어 제거
            .replace(/\.pdf$/i, ""); // 파일 확장자 제거

        const cleanedReasonMatch = (item.reason || "").match(/['"”](.*?)['"”]|\((.*?)\)/);
        const extractedReason = cleanedReasonMatch
            ? cleanedReasonMatch[1] || cleanedReasonMatch[2] || "연관 이유 없음"
            : "연관 이유 없음";

        const finalReason = `연관 이유: ${extractedReason}`;

        // HTML 요소 생성 및 추가
        const insuranceItem = document.createElement("div");
        insuranceItem.className = "insurance-item";
        insuranceItem.innerHTML = `
            <div class="insurance-info">
                <h2 class="insurance-title" style="font-size: 18px; font-weight: 600;">${cleanedTitle}</h2>
                <p class="insurance-description" style="font-size: 14px; color: #555;">${finalReason}</p>
                <a class="btn btn-secondary simulate-button" style="padding: 6px 12px; font-size: 12px; background-color: #5a7d9a; color: white; border: none;" href="#">챗봇으로 시뮬레이션 돌려보기</a>
            </div>
            <hr style="border: none; height: 1px; background-color: #e0e0e0; margin: 20px 0;">
        `;
        recommendationContainer.appendChild(insuranceItem);
    });

    // 각 버튼에 이벤트 추가: 4.chatbot.html로 이동
    const simulateButtons = document.querySelectorAll(".simulate-button");
    simulateButtons.forEach((button) => {
        // 호버 효과
        button.addEventListener("mouseover", () => {
            button.style.backgroundColor = "#004085"; // 진한 색
            button.style.transform = "scale(1.05)"; // 크기 확대
            button.style.boxShadow = "0px 4px 6px rgba(0, 0, 0, 0.2)"; // 그림자
        });

        button.addEventListener("mouseout", () => {
            button.style.backgroundColor = "#5a7d9a"; // 기본 색상 복구
            button.style.transform = "scale(1)";
            button.style.boxShadow = "none";
        });

        // 클릭 효과
        button.addEventListener("mousedown", () => {
            button.style.transform = "scale(0.95)"; // 크기 축소
        });

        button.addEventListener("mouseup", () => {
            button.style.transform = "scale(1.05)"; // 크기 복구
        });

        // 클릭 시 페이지 이동
        button.addEventListener("click", (event) => {
            event.preventDefault();
            console.log("챗봇 페이지로 이동 버튼 클릭됨");
            window.location.href = "http://localhost:8501";
        });
    });
});