document.addEventListener("DOMContentLoaded", () => {
    localStorage.removeItem("recommendationData");

    const form = document.getElementById("info-form");

    form.addEventListener("submit", (e) => {
        e.preventDefault();

        const requiredFields = document.querySelectorAll("#info-form input, #info-form select");
        let isValid = true;
        let firstInvalidField = null;

        requiredFields.forEach((field) => {
            const isDropdown = field.tagName.toLowerCase() === "select";
            const value = field.value.trim();

            if (!value || (isDropdown && value === "선택해주세요")) {
                isValid = false;
                field.style.borderColor = "red";
                if (!firstInvalidField) firstInvalidField = field;
            } else {
                field.style.borderColor = "#ccc";
            }
        });

        if (!isValid) {
            const fieldLabel = firstInvalidField.closest(".form-group").querySelector("label").textContent;
            alert(`"${fieldLabel.trim()}" 항목을 입력하거나 선택해 주세요.`);
            firstInvalidField.focus();
            return;
        }

        const jsonData = {
            기본정보: {
                이름: document.getElementById("first-name").value,
                성별: document.getElementById("gender").value,
                생년월일: document.getElementById("dob").value,
            },
            건강관련정보: {
                "신장(cm)": document.getElementById("height").value,
                "체중(kg)": document.getElementById("weight").value,
                흡연여부: document.getElementById("smoking").value,
                음주빈도: document.getElementById("drinking").value,
                운동빈도: document.getElementById("exercise").value,
            },
            재정상태및부양책임: {
                부양가족여부: document.getElementById("dependents").value,
                "연소득(만원)": document.getElementById("income").value,
            },
            가입목적및개인선호: {
                카테고리: document.getElementById("category").value,
                선호보장기간: document.getElementById("coverage-period").value,
                보험료납입주기: document.getElementById("payment-frequency").value,
            },
        };

        console.log("JSON 데이터:", JSON.stringify(jsonData, null, 2));

        const loadingMessage = document.getElementById("loading-message");
        loadingMessage.textContent = "고객님 정보 기반의 추천 제품을 찾고 있습니다. 잠시만 기다려 주세요...⏳";
        loadingMessage.style.display = "block";

        fetch("http://127.0.0.1:8000/api/v1/suggestion/suggest", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(jsonData),
        })
            .then((response) => {
                console.log("Server Response:", response);
                if (!response.ok) {
                    return response.json().then((err) => {
                        console.error("Error details:", err);
                        throw new Error("서버 응답 에러");
                    });
                }
                return response.json();
            })
            .then((data) => {
                console.log("서버로부터 데이터 가져오는 중:", data);
                localStorage.setItem("recommendationData", JSON.stringify(data));
                console.log("추천페이지로 이동");
                window.location.href = "3.rec.html";
            })
            .catch((error) => {
                console.error("Fetch Error:", error.message);
                alert("데이터 전송 중 오류가 발생했습니다. 다시 시도해주세요.");
            })
            .finally(() => {
                loadingMessage.style.display = "none";
            });
    });
});