document.addEventListener("DOMContentLoaded", () => {
    const recommendationContainer = document.querySelector(".insurance-list");
    const recommendationData = JSON.parse(localStorage.getItem("recommendationData"));

    if (recommendationData) {
        recommendationData.forEach((item) => {
            const insuranceItem = document.createElement("div");
            insuranceItem.classList.add("insurance-item");

            insuranceItem.innerHTML = `
                <div class="insurance-image" style="background-image: url('${item.image_url}');"></div>
                <div class="insurance-info">
                    <h2 class="insurance-title">${item.title}</h2>
                    <p class="insurance-description">${item.description}</p>
                    <a class="btn btn-primary" href="#">챗봇으로 시뮬레이션 돌려보기</a>
                </div>
            `;
            recommendationContainer.appendChild(insuranceItem);
        });
    } else {
        recommendationContainer.innerHTML = "<p>추천 데이터를 불러올 수 없습니다.</p>";
    }
});