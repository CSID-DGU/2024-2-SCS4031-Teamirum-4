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
    titleElement.style.fontSize = "28px";
    titleElement.style.fontWeight = "bold";
    titleElement.textContent = `${userName}님의 정보에 기반하여 추천하는 보험 상품입니다.🤓`;
    recommendationContainer.appendChild(titleElement);

    // 입력 정보 표시
    const userInfoSection = document.createElement("div");
    userInfoSection.className = "user-info-card";
    userInfoSection.style.border = "1.5px solid #2094f3";
    userInfoSection.style.borderRadius = "10px";
    userInfoSection.style.margin = "20px auto";
    userInfoSection.style.padding = "20px";
    userInfoSection.style.backgroundColor = "#e8f4ff";
    userInfoSection.style.color = "#003366";
    userInfoSection.style.width = "40%";

    userInfoSection.innerHTML = `
        <h2 style="text-align: center; font-size: 22px; margin-bottom: 20px;">
            입력한 정보 다시보기🔍
        </h2>
        <ul style="list-style-type: none; padding: 0; font-size: 16px; margin: 0;">
            ${Object.entries(userInfo)
                .map(([key, value]) => {
                    if (typeof value === "object") {
                        return `<li><strong>${key}:</strong> ${Object.entries(value)
                            .map(([subKey, subValue]) => `${subKey}: ${subValue}`)
                            .join(", ")}</li>`;
                    }
                    return `<li><strong>${key}:</strong> ${value}</li>`;
                })
                .join("")}
        </ul>
    `;
    recommendationContainer.appendChild(userInfoSection);

    // 구분선 추가
    const divider = document.createElement("hr");
    divider.style.border = "none";
    divider.style.borderTop = "2px solid #ddd";
    divider.style.width = "50%";
    divider.style.margin = "20px auto";
    recommendationContainer.appendChild(divider);

    // 로고 경로 매핑
    const logoPathMap = {
        "신한라이프": "../assets/images/rec_shinhan_logo.png",
        "한화생명": "../assets/images/rec_hanwha_logo.png",
        "삼성생명": "../assets/images/rec_samsung_logo.png",
        "교보생명": "../assets/images/rec_kyobo_logo.jpg",
    };

    // 추천 데이터 렌더링
    recommendationData.recommendations.forEach((item, index) => {
        const cleanedTitle = (item.product_name || "상품 이름 없음")
            .replace(/^추천\s*/, "")
            .replace(/\.pdf$/i, "");

        const companyName = cleanedTitle.split('-')[0].trim();
        console.log(`companyName: ${companyName}`);

        const hashtags = (item.reason || "")
            .match(/([가-힣]+이\(가\))/g)// 한국어 단어만 추출
            ?.map(tag => `#${tag.replace(/이\(가\)$/, "")}`) // "이(가)"를 제거하고 해시태그 추가
            ?.join(" ") || "";// 배열을 문자열로 변환

        const evaluationText = index === 0 ? "매우 적합" : "적합";
        const evaluationColor = index === 0 ? "#00cc66" : "#ffa500";

        // 동적으로 기본 경로 처리
        let logoPath = logoPathMap[companyName];
        if (!logoPath) {
            logoPath = `../assets/images/${companyName.toLowerCase()}_logo.png`; // 예상 경로 생성
        }
        console.log(`logoPath: ${logoPath}`);

        // 추천 아이템 생성
        const insuranceItem = document.createElement("div");
        insuranceItem.className = "insurance-item";
        insuranceItem.style.border = "1px solid #ddd";
        insuranceItem.style.borderRadius = "10px";
        insuranceItem.style.marginBottom = "20px";
        insuranceItem.style.padding = "15px";
        insuranceItem.style.boxShadow = "0px 4px 6px rgba(0, 0, 0, 0.1)";
        insuranceItem.style.width = "80%";
        insuranceItem.style.margin = "20px auto";
        insuranceItem.style.backgroundColor = "#ffffff"; // 흰색 배경 추가

        // 이미지 추가
        const logoImg = document.createElement("img");
        logoImg.src = logoPath;
        logoImg.alt = companyName;
        logoImg.style.maxWidth = "100px";
        logoImg.style.marginBottom = "10px";
        insuranceItem.appendChild(logoImg);

        // 텍스트 추가
        const title = document.createElement("h2");
        title.className = "insurance-title";
        title.style.fontSize = "18px";
        title.style.fontWeight = "600";
        title.textContent = cleanedTitle;
        insuranceItem.appendChild(title);

        const evaluation = document.createElement("p");
        evaluation.className = "insurance-evaluation";
        evaluation.style.fontSize = "14px";
        evaluation.style.color = "#555";
        evaluation.innerHTML = `
            평가: <span style="display: inline-block; width: 16px; height: 16px; border-radius: 50%; border: 2px solid black; background-color: ${evaluationColor}; margin-right: 5px;"></span> ${evaluationText}
        `;
        insuranceItem.appendChild(evaluation);

        const description = document.createElement("p");
        description.className = "insurance-description";
        description.style.fontSize = "14px";
        description.style.color = "#555";
        description.textContent = hashtags;
        insuranceItem.appendChild(description);

        recommendationContainer.appendChild(insuranceItem);
    });

    // 시뮬레이션 버튼 추가
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

    simulateButton.addEventListener("click", () => {
        window.location.href = "http://localhost:8501";
    });

    recommendationContainer.appendChild(simulateButton);
});