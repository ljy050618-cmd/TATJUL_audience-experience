document.addEventListener("DOMContentLoaded", () => {
    setupNicknameCheck();
    setupStudentWall();
});


function setupNicknameCheck() {
    const input =
        document.getElementById("nickname");

    const button =
        document.getElementById(
            "check-nickname-button"
        );

    const status =
        document.getElementById(
            "nickname-status"
        );

    if (!input || !button || !status) {
        return;
    }

    button.addEventListener("click", async () => {
        const nickname = input.value.trim();

        status.textContent = "";
        status.className = "nickname-status";

        if (nickname.length < 2) {
            showStatus(
                "닉네임은 2자 이상 입력해 주세요.",
                false
            );
            return;
        }

        button.disabled = true;
        button.textContent = "확인 중";

        try {
            const query = new URLSearchParams({
                nickname,
            });

            const response = await fetch(
                `/check-nickname?${query.toString()}`
            );

            if (!response.ok) {
                throw new Error("중복 확인 실패");
            }

            const result = await response.json();

            showStatus(
                result.message,
                result.available
            );
        } catch (error) {
            showStatus(
                "중복 확인 중 오류가 발생했습니다.",
                false
            );
        } finally {
            button.disabled = false;
            button.textContent = "중복 확인";
        }
    });

    input.addEventListener("input", () => {
        status.textContent = "";
        status.className = "nickname-status";
    });

    function showStatus(message, available) {
        status.textContent = message;

        status.className = available
            ? "nickname-status status-available"
            : "nickname-status status-unavailable";
    }
}


function setupStudentWall() {
    const stage =
        document.getElementById(
            "student-name-stage"
        );

    const dataElement =
        document.getElementById(
            "student-data"
        );

    if (!stage || !dataElement) {
        return;
    }

    let names;

    try {
        names = JSON.parse(
            dataElement.textContent.trim()
        );
    } catch (error) {
        console.error(
            "학생 명부 데이터를 읽지 못했습니다.",
            error
        );
        return;
    }

    if (!Array.isArray(names) || names.length === 0) {
        return;
    }

    const activeElements = new Set();
    let previousName = null;

    function selectRandomName() {
        if (names.length === 1) {
            return names[0];
        }

        let selected;

        do {
            selected =
                names[
                    Math.floor(
                        Math.random() * names.length
                    )
                ];
        } while (selected === previousName);

        previousName = selected;

        return selected;
    }

    function writeNameOnWall() {
        if (
            document.hidden ||
            activeElements.size >= 9
        ) {
            return;
        }

        const nickname = selectRandomName();

        const wrapper =
            document.createElement("span");

        wrapper.className =
            "wall-student-name";

        const left =
            5 + Math.random() * 72;

        const top =
            8 + Math.random() * 73;

        const angle =
            -9 + Math.random() * 18;

        const size =
            20 + Math.random() * 19;

        const lifetime =
            6200 + Math.random() * 2800;

        wrapper.style.left = `${left}%`;
        wrapper.style.top = `${top}%`;
        wrapper.style.fontSize = `${size}px`;
        wrapper.style.setProperty(
            "--wall-angle",
            `${angle}deg`
        );

        Array.from(nickname).forEach(
            (character, index) => {
                const letter =
                    document.createElement("span");

                letter.className =
                    "wall-name-letter";

                letter.textContent = character;

                letter.style.animationDelay =
                    `${index * 0.14}s`;

                wrapper.appendChild(letter);
            }
        );

        stage.appendChild(wrapper);
        activeElements.add(wrapper);

        window.setTimeout(() => {
            wrapper.classList.add(
                "wall-name-erasing"
            );
        }, lifetime - 1800);

        window.setTimeout(() => {
            activeElements.delete(wrapper);
            wrapper.remove();
        }, lifetime);
    }

    const initialCount =
        Math.min(names.length, 6);

    for (
        let index = 0;
        index < initialCount;
        index += 1
    ) {
        window.setTimeout(
            writeNameOnWall,
            450 + index * 600
        );
    }

    window.setInterval(
        writeNameOnWall,
        1450
    );
}