document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("info-form");

    form.addEventListener("submit", (e) => {
        e.preventDefault(); // 기본 제출 동작 방지

        // 필수 입력 필드 선택
        const requiredFields = document.querySelectorAll("#info-form input, #info-form select");
        let isValid = true;
        let firstInvalidField = null;

        requiredFields.forEach((field) => {
            const isDropdown = field.tagName.toLowerCase() === "select";
            const value = field.value.trim();

            if (!value || (isDropdown && value === "선택해주세요")) {
                isValid = false;
                field.style.borderColor = "red"; // 경고 색상 표시
                if (!firstInvalidField) firstInvalidField = field;
            } else {
                field.style.borderColor = "#ccc"; // 정상 색상 복원
            }
        });

        // 유효하지 않은 경우
        if (!isValid) {
            const fieldLabel = firstInvalidField.closest(".form-group").querySelector("label").textContent;
            alert(`"${fieldLabel.trim()}" 항목을 입력하거나 선택해 주세요.`);
            firstInvalidField.focus(); // 첫 번째 잘못된 필드로 포커스 이동
        } else {
            // 모든 값이 올바른 경우 다음 페이지로 이동
            window.location.href = "3.rec.html"; // 페이지 이동
        }
    });
});