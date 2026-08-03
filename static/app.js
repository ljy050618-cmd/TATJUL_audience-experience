document.addEventListener(
    "DOMContentLoaded",
    () => {

        setupPosterEffect();
        setupModeCards();
        setupNicknameCheck();
        setupResultShare();
        setupResultSave();

    }
);




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

function setupResultShare() {

    const shareButton =
        document.getElementById(
            "share-result-button"
        );

    const resultCard =
        document.getElementById(
            "result-card"
        );

    const shareStatus =
        document.getElementById(
            "share-status"
        );

    if (
        !shareButton ||
        !resultCard
    ) {
        return;
    }


    shareButton.addEventListener(
        "click",
        async () => {

            const originalText =
                shareButton.textContent;

            shareButton.disabled = true;

            shareButton.textContent =
                "결과 이미지 만드는 중...";


            try {

                const file =
                    await createResultImageFile(
                        resultCard
                    );


                const canShareFile =
                    navigator.share &&
                    navigator.canShare &&
                    navigator.canShare({
                        files: [file],
                    });


                if (canShareFile) {

                    await navigator.share({
                        title:
                            "오늘의 세일럼 결과",

                        text:
                            "나의 세일럼 관객 유형 결과",

                        files: [file],
                    });


                    showShareStatus(
                        shareStatus,
                        "공유창을 열었습니다.",
                        true
                    );

                } else {

                    downloadFile(file);

                    showShareStatus(
                        shareStatus,
                        "이 브라우저에서는 이미지 공유가 지원되지 않아 파일을 저장했습니다.",
                        true
                    );
                }

            } catch (error) {

                if (
                    error.name ===
                    "AbortError"
                ) {

                    showShareStatus(
                        shareStatus,
                        "공유를 취소했습니다.",
                        null
                    );

                } else {

                    console.error(
                        "결과 공유 오류:",
                        error
                    );

                    showShareStatus(
                        shareStatus,
                        "결과 이미지 공유에 실패했습니다.",
                        false
                    );
                }

            } finally {

                shareButton.disabled =
                    false;

                shareButton.textContent =
                    originalText;
            }
        }
    );
}


function setupResultSave() {

    const saveButton =
        document.getElementById(
            "save-result-button"
        );

    const resultCard =
        document.getElementById(
            "result-card"
        );

    const shareStatus =
        document.getElementById(
            "share-status"
        );

    if (
        !saveButton ||
        !resultCard
    ) {
        return;
    }


    saveButton.addEventListener(
        "click",
        async () => {

            const originalText =
                saveButton.textContent;

            saveButton.disabled = true;

            saveButton.textContent =
                "이미지 저장 중...";


            try {

                const file =
                    await createResultImageFile(
                        resultCard
                    );

                downloadFile(file);

                showShareStatus(
                    shareStatus,
                    "결과 이미지를 저장했습니다.",
                    true
                );

            } catch (error) {

                console.error(
                    "결과 저장 오류:",
                    error
                );

                showShareStatus(
                    shareStatus,
                    "결과 이미지 저장에 실패했습니다.",
                    false
                );

            } finally {

                saveButton.disabled =
                    false;

                saveButton.textContent =
                    originalText;
            }
        }
    );
}


async function createResultImageFile(
    resultCard
) {

    if (
        typeof html2canvas ===
        "undefined"
    ) {
        throw new Error(
            "html2canvas가 로드되지 않았습니다."
        );
    }


    const canvas =
        await html2canvas(
            resultCard,
            {
                scale: 2,
                backgroundColor:
                    "#100d13",

                useCORS: true,
                logging: false,
            }
        );


    const blob =
        await new Promise(
            (
                resolve,
                reject
            ) => {

                canvas.toBlob(
                    (
                        createdBlob
                    ) => {

                        if (
                            createdBlob
                        ) {
                            resolve(
                                createdBlob
                            );

                        } else {

                            reject(
                                new Error(
                                    "이미지 파일을 만들지 못했습니다."
                                )
                            );
                        }
                    },

                    "image/png",
                    1
                );
            }
        );


    return new File(
        [blob],
        "today-salem-result.png",
        {
            type: "image/png",
        }
    );
}


function downloadFile(file) {

    const fileUrl =
        URL.createObjectURL(file);

    const downloadLink =
        document.createElement("a");

    downloadLink.href =
        fileUrl;

    downloadLink.download =
        file.name;

    document.body.appendChild(
        downloadLink
    );

    downloadLink.click();

    downloadLink.remove();


    setTimeout(
        () => {
            URL.revokeObjectURL(
                fileUrl
            );
        },
        1000
    );
}


function showShareStatus(
    element,
    message,
    success
) {

    if (!element) {
        return;
    }

    element.textContent =
        message;

    element.className =
        "input-help share-status";


    if (success === true) {

        element.classList.add(
            "status-available"
        );

    } else if (
        success === false
    ) {

        element.classList.add(
            "status-unavailable"
        );
    }
}