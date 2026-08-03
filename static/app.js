document.addEventListener(
    "DOMContentLoaded",
    () => {

        setupPosterEffect();
        setupModeCards();
        setupNicknameCheck();

    }
);


function setupPosterEffect() {

    const poster =
        document.getElementById("poster");

    if (!poster) {
        return;
    }

    const canHover =
        window.matchMedia(
            "(pointer: fine)"
        ).matches;

    if (!canHover) {
        return;
    }

    const posterStage =
        poster.parentElement;


    posterStage.addEventListener(
        "mousemove",
        (event) => {

            const rect =
                posterStage
                    .getBoundingClientRect();

            const x =
                (
                    event.clientX -
                    rect.left
                ) /
                rect.width -
                0.5;

            const y =
                (
                    event.clientY -
                    rect.top
                ) /
                rect.height -
                0.5;

            poster.style.transform = `
                rotateY(${x * 16 - 7}deg)
                rotateX(${-y * 12 + 2}deg)
            `;
        }
    );


    posterStage.addEventListener(
        "mouseleave",
        () => {

            poster.style.transform =
                "rotateY(-7deg) rotateX(2deg)";
        }
    );
}


function setupModeCards() {

    const modeCards =
        document.querySelectorAll(
            ".mode-card"
        );

    modeCards.forEach(
        (card) => {

            card.addEventListener(
                "click",
                () => {

                    modeCards.forEach(
                        (otherCard) => {
                            otherCard.classList
                                .remove("selected");
                        }
                    );

                    card.classList.add(
                        "selected"
                    );

                    const radio =
                        card.querySelector(
                            'input[type="radio"]'
                        );

                    if (radio) {
                        radio.checked = true;
                    }
                }
            );
        }
    );
}


function setupNicknameCheck() {

    const nicknameInput =
        document.getElementById(
            "nickname"
        );

    const checkButton =
        document.getElementById(
            "nickname-check-button"
        );

    const nicknameStatus =
        document.getElementById(
            "nickname-status"
        );

    if (
        !nicknameInput ||
        !checkButton ||
        !nicknameStatus
    ) {
        return;
    }


    checkButton.addEventListener(
        "click",
        async () => {

            const nickname =
                nicknameInput.value.trim();

            if (!nickname) {

                showNicknameStatus(
                    "닉네임을 먼저 입력해 주세요.",
                    false
                );

                return;
            }


            showNicknameStatus(
                "확인 중입니다.",
                null
            );


            try {

                const response =
                    await fetch(
                        `/api/nickname-check?nickname=${
                            encodeURIComponent(
                                nickname
                            )
                        }`
                    );

                const data =
                    await response.json();


                if (
                    response.ok &&
                    data.valid &&
                    !data.exists
                ) {
                    showNicknameStatus(
                        data.message,
                        true
                    );

                } else {
                    showNicknameStatus(
                        data.message ||
                        "사용할 수 없는 닉네임입니다.",
                        false
                    );
                }

            } catch (error) {

                console.error(
                    "닉네임 확인 오류:",
                    error
                );

                showNicknameStatus(
                    "중복 확인에 실패했습니다.",
                    false
                );
            }
        }
    );


    nicknameInput.addEventListener(
        "input",
        () => {

            nicknameStatus.textContent =
                "중복 확인 버튼을 눌러 주세요.";

            nicknameStatus.className =
                "input-help";
        }
    );
}


function showNicknameStatus(
    message,
    isAvailable
) {

    const nicknameStatus =
        document.getElementById(
            "nickname-status"
        );

    nicknameStatus.textContent =
        message;

    nicknameStatus.className =
        "input-help";


    if (isAvailable === true) {

        nicknameStatus.classList.add(
            "status-available"
        );

    } else if (isAvailable === false) {

        nicknameStatus.classList.add(
            "status-unavailable"
        );
    }
}