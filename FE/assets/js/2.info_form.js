document.addEventListener("DOMContentLoaded", () => {
    console.log("2.info_form.js 실행됨");

    const form = document.getElementById("info-form");
    const submitButton = document.querySelector('button[type="submit"]');

    // 버튼 호버 및 클릭 효과 추가
    if (submitButton) {
        // 호버 효과
        submitButton.addEventListener("mouseover", () => {
            submitButton.style.backgroundColor = "#405767"; // 호버 색상
            submitButton.style.transform = "scale(1.05)"; // 크기 확대
            submitButton.style.boxShadow = "0px 4px 6px rgba(0, 0, 0, 0.2)"; // 그림자
        });
        submitButton.addEventListener("mouseout", () => {
            submitButton.style.backgroundColor = "#606b77"; // 기본 색상 복구
            submitButton.style.transform = "scale(1)";
            submitButton.style.boxShadow = "none";
        });

        // 클릭 효과
        submitButton.addEventListener("mousedown", () => {
            submitButton.style.transform = "scale(0.95)"; // 크기 축소
        });
        submitButton.addEventListener("mouseup", () => {
            submitButton.style.transform = "scale(1.05)"; // 크기 복구
        });
    }


    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        console.log("폼 제출 이벤트 실행됨");

        const requiredFields = document.querySelectorAll("#info-form input, #info-form select");
        let isValid = true;

        // 필드 유효성 검사
        requiredFields.forEach((field) => {
            const isDropdown = field.tagName.toLowerCase() === "select";
            const value = field.value.trim();

            if (!value || (isDropdown && value === "선택해주세요")) {
                isValid = false;
                field.style.borderColor = "red";
            } else {
                field.style.borderColor = "#ccc";
            }
        });

        if (!isValid) {
            alert("모든 필드를 올바르게 입력해주세요.");
            return;
        }

        console.log("폼 데이터 유효성 검사 통과");

        // JSON 데이터 생성
        const jsonData = {
            "기본정보": {
                "이름": getValue("first-name"),
                "성별": convertToKorean("gender", {
                    male: "남성",
                    female: "여성",
                    other: "기타"
                }),
                "생년월일": getValue("dob"),
            },
            "건강관련정보": {
                "신장(cm)": parseInt(getValue("height"), 10),
                "체중(kg)": parseInt(getValue("weight"), 10),
                "흡연여부": convertToKorean("smoking", { yes: "예", no: "아니오" }),
                "음주빈도": convertToKorean("drinking", {
                    never: "없음",
                    occasionally: "가끔",
                    frequently: "자주"
                }),
                "운동빈도": convertToKorean("exercise", {
                    never: "없음",
                    occasionally: "가끔",
                    frequently: "자주"
                }),
            },
            "재정상태및부양책임": {
                "부양가족여부": convertToKorean("dependents", { yes: "있음", no: "없음" }),
                "연소득(만원)": parseInt(getValue("income"), 10),
            },
            "가입목적및개인선호": {
                "카테고리": getValue("category"),
                "선호보장기간": convertToKorean("coverage-period", {
                    short: "10년 이하",
                    medium: "10~20년",
                    long: "20년 이상"
                }),
                "보험료납입주기": convertToKorean("payment-frequency", {
                    monthly: "월납",
                    quarterly: "분기납",
                    annually: "연납"
                }),
            },
        };

        console.log("JSON 데이터 생성 완료:", jsonData);

        // 팝업창 생성
        const popup = document.createElement("div");
        popup.innerText = "추천 데이터를 처리 중입니다. 잠시만 기다려주세요...⏳";
        popup.style.position = "fixed";
        popup.style.top = "50%";
        popup.style.left = "50%";
        popup.style.transform = "translate(-50%, -50%)";
        popup.style.padding = "20px";
        popup.style.backgroundColor = "#ffffff";
        popup.style.boxShadow = "0px 4px 6px rgba(0, 0, 0, 0.1)";
        popup.style.borderRadius = "8px";
        popup.style.zIndex = "1000";
        document.body.appendChild(popup);


        try {
            console.log("서버로 데이터 전송 시작");
            const response = await fetch("http://127.0.0.1:8000/api/v1/suggestion/suggest", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(jsonData),
            });

            const responseBody = await response.json();
            console.log("서버 응답 본문:", responseBody);

            if (!response.ok || responseBody.status !== "success") {
                throw new Error(responseBody.message || "추천 데이터를 불러오는 중 문제가 발생했습니다.");
            }

            //로컬 저장소에 이름 저장
            localStorage.setItem("userName", jsonData.기본정보.이름);
            
            //로컬 저장소에 입력 정보 모두 저장
            localStorage.setItem("userInfo", JSON.stringify(jsonData)); // 유저 정보 저장

            // 로컬 저장소에 추천 데이터 저장
            localStorage.setItem("recommendationData", JSON.stringify(responseBody));
            console.log("추천 데이터 저장 성공");

            // 페이지 이동 테스트 코드
            console.log("현재 URL:", window.location.href);
            console.log("이동할 URL:", "3.rec.html");

            console.log("window.location.href 호출 시도...");
            setTimeout(() => {
                console.log("Navigating to 3.rec.html");
                window.location.href = "3.rec.html";
            }, 0);
            console.log("window.location.href 호출 완료.");
            document.body.removeChild(popup); // 팝업창 제거

        } catch (error) {
            console.error("서버 요청 중 오류 발생:", error.message);
            alert("서버와 통신 중 문제가 발생했습니다. 다시 시도해주세요.");
            document.body.removeChild(popup); // 팝업창 제거
        }
    });

    // 헬퍼 함수: 필드 값 가져오기
    function getValue(id) {
        return document.getElementById(id).value.trim();
    }

    function convertToKorean(id, mapping) {
        return mapping[getValue(id)] || "알 수 없음";
    }
});