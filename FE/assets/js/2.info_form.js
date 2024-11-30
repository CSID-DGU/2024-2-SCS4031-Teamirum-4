document.addEventListener("DOMContentLoaded", () => {
    console.log("DOMContentLoaded 실행됨");

    const form = document.getElementById("info-form");

    form.addEventListener("submit", async (e) => {
        console.log("폼 제출 이벤트 실행됨");
        e.preventDefault();

        const requiredFields = document.querySelectorAll("#info-form input, #info-form select");
        let isValid = true;
        let firstInvalidField = null;

        requiredFields.forEach((field) => {
            const isDropdown = field.tagName.toLowerCase() === "select";
            const value = field.value.trim();

            console.log(`필드 ${field.id} 값: ${value}`);

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
            console.log(`유효하지 않은 필드: ${firstInvalidField.id}`);
            firstInvalidField.focus();
            return;
        }

        console.log("폼 데이터 유효성 검사 통과");

        // JSON 데이터 생성
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

        console.log("JSON 데이터 생성 완료:", jsonData);

        const loadingMessage = document.getElementById("loading-message");
        loadingMessage.textContent = "고객님 정보 기반의 추천 제품을 찾고 있습니다. 잠시만 기다려 주세요...⏳";
        loadingMessage.style.display = "block";

        // 페이지 강제 이동
        setTimeout(() => {
            console.log("페이지 이동 시작");
            location.href = "http://127.0.0.1:5500/2024-2-SCS4031-Teamirum-4/Frontend/pages/3.rec.html"; // 상대 경로 또는 절대 경로 사용
            console.log("페이지 이동 실행 완료");
        }, 10000); // 3초 후 실행
        
        try {
            console.log("서버로 요청 시작");
            const response = await fetch("http://127.0.0.1:8000/api/v1/suggestion/suggest", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(jsonData),
                cache: "no-store", // 캐싱 방지
            });

            console.log("서버 응답 상태 코드:", response.status);
            const responseBody = await response.text();
            console.log("서버 응답 본문:", responseBody);

            if (!response.ok) {
                console.error("서버 응답 실패. 상태 코드:", response.status);
                throw new Error(`서버 응답 에러: ${responseBody}`);
            }

            const data = JSON.parse(responseBody); // 서버 응답 데이터 파싱
            console.log("서버 응답 데이터:", data);

            // 로컬스토리지에 서버 응답 데이터 저장
            localStorage.setItem("recommendationData", JSON.stringify(data));
            console.log("로컬스토리지 저장 성공");

            
        } catch (error) {
            console.error("Fetch 요청 실패:", error.message);
            alert("서버와 통신 중 문제가 발생했습니다. 다시 시도해주세요.");
        } finally {
            loadingMessage.style.display = "none";
        }

        console.log("폼 제출 핸들러 종료");
    });
});