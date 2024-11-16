document.addEventListener("DOMContentLoaded", () => {
    const headerText = document.querySelector(".content-container h1");
    const descriptionText = document.querySelector(".content-container p");
    const button = document.querySelector("#simulation-btn");

    // 애니메이션 실행
    setTimeout(() => {
        headerText.style.animation = "fadeInUp 1s ease forwards";
    }, 300);

    setTimeout(() => {
        descriptionText.style.animation = "fadeInUp 1s ease forwards";
    }, 600);

    setTimeout(() => {
        button.style.animation = "fadeInUp 1s ease forwards";
    }, 900);

    // 버튼 클릭 이벤트 - 페이지 이동
    button.addEventListener("click", () => {
        window.location.href = "../pages/2.info_form.html";
    });
});