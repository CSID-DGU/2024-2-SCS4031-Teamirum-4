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
            // 모든 값이 올바른 경우 JSON 데이터 생성
            /*
            const jsonData = {
                기본정보: {
                    이름: document.getElementById("first-name").value,
                    성별: document.getElementById("gender").value,
                    생년월일: document.getElementById("dob").value
                },
                건강관련정보: {
                    "신장(cm)": document.getElementById("height").value,
                    "체중(kg)": document.getElementById("weight").value,
                    흡연여부: document.getElementById("smoking").value,
                    음주빈도: document.getElementById("drinking").value,
                    운동빈도: document.getElementById("exercise").value
                },
                재정상태및부양책임: {
                    부양가족여부: document.getElementById("dependents").value,
                    "연소득(만원)": document.getElementById("income").value
                },
                가입목적및개인선호: {
                    가입목적: document.getElementById("purpose").value,
                    선호보장기간: document.getElementById("coverage-period").value,
                    보험료납입주기: document.getElementById("payment-frequency").value
                }
            };

            console.log("JSON 데이터:", JSON.stringify(jsonData, null, 2)); // JSON 출력

            // 서버에 데이터 전송
            fetch("https://example.com/api/submit", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(jsonData)
            })
                .then((response) => {
                    if (!response.ok) {
                        throw new Error("서버 응답 에러");
                    }
                    return response.json();
                })
                .then((data) => {
                    console.log("서버 응답:", data);
                    // 성공적으로 전송된 경우 다음 페이지로 이동
                    window.location.href = "3.rec.html";
                })
                .catch((error) => {
                    console.error("전송 에러:", error);
                    alert("데이터 전송 중 오류가 발생했습니다. 다시 시도해주세요.");
                });
              */
             // 임시로 다음 페이지로 이동
            window.location.href = "3.rec.html";  
        }
    });
});


