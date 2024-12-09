document.addEventListener("DOMContentLoaded", () => {
    console.log("3.rec.js 실행됨");

    const recommendationContainer = document.querySelector("#recommendation-container");

    // 로컬 스토리지에서 추천 데이터 가져오기
    const recommendationData = JSON.parse(localStorage.getItem("recommendationData"));
    const userName = localStorage.getItem("userName") || "고객";

    // 사용자 입력 정보 가져오기
    const userInfo = JSON.parse(localStorage.getItem("userInfo"));

    if (!recommendationData || !Array.isArray(recommendationData.recommendations)) {
        recommendationContainer.innerHTML = "<p>추천 데이터를 불러올 수 없습니다. 다시 시도해주세요.</p>";
        console.error("추천 데이터가 유효하지 않습니다.");
        return;
    }

    // 제목 추가
    const titleElement = document.createElement("h1");
    titleElement.className = "form-title";
    titleElement.style.textAlign = "center";
    titleElement.style.fontSize = "28px"; // 글씨 크기 키움
    titleElement.style.fontWeight = "bold";
    titleElement.textContent = `${userName}님의 정보에 기반하여 추천하는 보험 상품입니다.🤓`;
    recommendationContainer.appendChild(titleElement);

    // 입력 정보 표시 (카드 스타일)
    const userInfoSection = document.createElement("div");
    userInfoSection.className = "user-info-card";
    userInfoSection.style.border = "1.5px solid #2094f3";
    userInfoSection.style.borderRadius = "10px";
    userInfoSection.style.margin = "20px auto";
    userInfoSection.style.padding = "20px";
    userInfoSection.style.backgroundColor = "#e8f4ff"; // 밝은 파란색 배경
    userInfoSection.style.color = "#003366"; // 진한 파란색 텍스트
    userInfoSection.style.width = "40%";
    userInfoSection.style.fontFamily = "'Noto Sans', sans-serif";

    // 입력 정보 제목 추가 (카드 내부에 포함)
    userInfoSection.innerHTML = `
        <h2 style="text-align: center; font-size: 22px; margin-bottom: 20px;">
            입력한 정보 다시보기🔍
        </h2>
        <ul style="list-style-type: none; padding: 0; font-size: 16px; margin: 0;">
            ${Object.entries(userInfo)
                .map(([key, value]) => {
                    if (typeof value === "object") {
                        return `<li style="margin-bottom: 10px;"><strong>${key}:</strong> ${Object.entries(value)
                            .map(([subKey, subValue]) => `${subKey}: ${subValue}`)
                            .join(", ")}</li>`;
                    }
                    return `<li style="margin-bottom: 10px;"><strong>${key}:</strong> ${value}</li>`;
                })
                .join("")}
        </ul>
    `;

    // 입력 정보 카드를 추천 리스트 위에 삽입
    recommendationContainer.appendChild(userInfoSection);

    // 구분선 추가
    const divider = document.createElement("hr");
    divider.style.border = "none";
    divider.style.borderTop = "2px solid #ddd";
    divider.style.width = "50%";
    divider.style.margin = "20px auto";
    recommendationContainer.appendChild(divider);

    // 추천 데이터를 화면에 표시
    recommendationData.recommendations.forEach((item, index) => {
        const cleanedTitle = (item.product_name || "상품 이름 없음")
            .replace(/^추천\s*/, "")
            .replace(/\.pdf$/i, "");

        const companyName = cleanedTitle.split('-')[0].trim();
        const hashtags = (item.reason || "")
            .match(/([가-힣]+이\(가\))/g)
            ?.map(keyword => `#${keyword.replace(/이$begin:math:text$가$end:math:text$/, "")}`)
            ?.map(tag => tag.replace(/이\(가\)$/, "")) // "이(가)" 제거
            .join(" ") || "";

        const evaluationText = index === 0 ? "매우 적합" : "적합";
        const evaluationColor = index === 0 ? "#00cc66" : "#ffa500";

        const logoPathMap = {
            "신한라이프": "../assets/images/rec_shinhan_logo.png",
            "한화생명": "../assets/images/rec_hanwha_logo.png",
            "삼성생명": "../assets/images/rec_samsung_logo.png",
            "교보생명": "../assets/images/rec_kyobo_logo.jpg",
        };
        const logoPath = logoPathMap[companyName] || "";

        const insuranceItem = document.createElement("div");
        insuranceItem.className = "insurance-item";
        insuranceItem.style.border = "1px solid #ddd";
        insuranceItem.style.borderRadius = "10px";
        insuranceItem.style.marginBottom = "20px";
        insuranceItem.style.padding = "15px";
        insuranceItem.style.boxShadow = "0px 4px 6px rgba(0, 0, 0, 0.1)";
        insuranceItem.style.width = "80%"; // 가로폭 조정
        insuranceItem.style.margin = "20px auto";

        insuranceItem.innerHTML = `
            <div class="insurance-info">
                <img src="${logoPath}" alt="${companyName}" style="max-width: 100px; margin-bottom: 10px;">
                <h2 class="insurance-title" style="font-size: 18px; font-weight: 600;">${cleanedTitle}</h2>
                <p class="insurance-evaluation" style="font-size: 14px; color: #555;">
                    평가: <span style="display: inline-block; width: 16px; height: 16px; border-radius: 50%; border: 2px solid black; background-color: ${evaluationColor}; margin-right: 5px;"></span> ${evaluationText}
                </p>
                <p class="insurance-description" style="font-size: 14px; color: #555;">${hashtags}</p>
            </div>
        `;
        recommendationContainer.appendChild(insuranceItem);
    });

    // 버튼 추가
    const simulateButton = document.createElement("button");
    simulateButton.type = "button";
    simulateButton.className = "simulate-button";
    simulateButton.textContent = "챗봇으로 시뮬레이션 돌려보기";
    simulateButton.style.padding = "10px 20px";
    simulateButton.style.fontSize = "16px";
    simulateButton.style.backgroundColor = "#5a7d9a";
    simulateButton.style.color = "white";
    simulateButton.style.border = "none";
    simulateButton.style.borderRadius = "5px";
    simulateButton.style.margin = "20px auto";
    simulateButton.style.display = "block";

    recommendationContainer.appendChild(simulateButton);

    // 각 버튼에 이벤트 추가: 4.chatbot.html로 이동
    simulateButton.addEventListener("mouseover", () => {
        simulateButton.style.backgroundColor = "#004085";
        simulateButton.style.transform = "scale(1.05)";
        simulateButton.style.boxShadow = "0px 4px 6px rgba(0, 0, 0, 0.2)";
    });

    simulateButton.addEventListener("mouseout", () => {
        simulateButton.style.backgroundColor = "#5a7d9a";
        simulateButton.style.transform = "scale(1)";
        simulateButton.style.boxShadow = "none";
    });

    simulateButton.addEventListener("mousedown", () => {
        simulateButton.style.transform = "scale(0.95)";
    });

    simulateButton.addEventListener("mouseup", () => {
        simulateButton.style.transform = "scale(1.05)";
    });

    simulateButton.addEventListener("click", (event) => {
        event.preventDefault();
        console.log("챗봇 페이지로 이동 버튼 클릭됨");
        window.location.href = "http://localhost:8501";
    });
});