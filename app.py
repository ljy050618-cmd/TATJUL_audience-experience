import os
import re
from datetime import datetime, timezone

from dotenv import load_dotenv
from flask import (
    Flask,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)
from supabase import Client, create_client


# Codespace의 .env 파일을 읽습니다.
load_dotenv()


app = Flask(__name__)

# Flask 세션 쿠키를 보호하는 비밀키입니다.
app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "temporary-local-development-key",
)


SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get(
    "SUPABASE_SERVICE_ROLE_KEY"
)


def get_supabase() -> Client:
    """
    Supabase 연결을 반환합니다.
    환경변수가 없으면 이해하기 쉬운 오류를 냅니다.
    """

    if not SUPABASE_URL:
        raise RuntimeError(
            "SUPABASE_URL이 설정되지 않았습니다. "
            ".env 파일을 확인해 주세요."
        )

    if not SUPABASE_SERVICE_ROLE_KEY:
        raise RuntimeError(
            "SUPABASE_SERVICE_ROLE_KEY가 설정되지 않았습니다. "
            ".env 파일을 확인해 주세요."
        )

    return create_client(
        SUPABASE_URL,
        SUPABASE_SERVICE_ROLE_KEY,
    )


def normalize_nickname(raw_nickname: str) -> str:
    """
    닉네임의 앞뒤 공백과 연속 공백을 정리하고
    사용할 수 있는 문자인지 검사합니다.
    """

    nickname = re.sub(
        r"\s+",
        " ",
        (raw_nickname or "").strip(),
    )

    if len(nickname) < 2:
        raise ValueError(
            "닉네임은 두 글자 이상 입력해 주세요."
        )

    if len(nickname) > 16:
        raise ValueError(
            "닉네임은 16자 이하로 입력해 주세요."
        )

    allowed_pattern = (
        r"^[가-힣ㄱ-ㅎㅏ-ㅣA-Za-z0-9 _-]+$"
    )

    if not re.fullmatch(
        allowed_pattern,
        nickname,
    ):
        raise ValueError(
            "닉네임에는 한글, 영문, 숫자, "
            "공백, -, _만 사용할 수 있습니다."
        )

    return nickname


def find_participant(nickname: str):
    """
    Supabase에서 같은 닉네임의 참가자를 찾습니다.
    없으면 None을 반환합니다.
    """

    supabase = get_supabase()

    response = (
        supabase.table("participants")
        .select("id,nickname")
        .eq("nickname", nickname)
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]

    return None


@app.route("/")
def intro():
    return render_template("intro.html")


@app.route("/home")
def index():
    return render_template("index.html")


@app.route(
    "/enter",
    methods=["GET", "POST"],
)
def enter():
    """닉네임 신규 등록 또는 기존 닉네임 입장"""

    if request.method == "GET":
        return render_template("enter.html")

    raw_nickname = request.form.get(
        "nickname",
        "",
    )

    mode = request.form.get(
        "mode",
        "new",
    )

    try:
        nickname = normalize_nickname(
            raw_nickname
        )

    except ValueError as error:
        return render_template(
            "enter.html",
            error=str(error),
            nickname=raw_nickname,
        ), 400

    try:
        participant = find_participant(
            nickname
        )

    except Exception as error:
        print(
            "Supabase 조회 오류:",
            error,
        )

        return render_template(
            "enter.html",
            error=(
                "데이터베이스 연결에 실패했습니다. "
                ".env와 Supabase 설정을 확인해 주세요."
            ),
            nickname=nickname,
        ), 500

    # 새 닉네임 등록
    if mode == "new":

        if participant:
            return render_template(
                "enter.html",
                error=(
                    "이미 사용 중인 닉네임입니다. "
                    "처음 참여하는 경우 다른 닉네임을 "
                    "입력해 주세요."
                ),
                nickname=nickname,
            ), 409

        try:
            supabase = get_supabase()

            response = (
                supabase.table("participants")
                .insert(
                    {
                        "nickname": nickname,
                    }
                )
                .execute()
            )

            participant = response.data[0]

        except Exception as error:
            print(
                "닉네임 등록 오류:",
                error,
            )

            # 두 사람이 동시에 같은 닉네임을
            # 등록한 경우에도 여기서 걸립니다.
            return render_template(
                "enter.html",
                error=(
                    "이미 사용 중인 닉네임이거나 "
                    "등록에 실패했습니다."
                ),
                nickname=nickname,
            ), 409

    # 기존 닉네임으로 재접속
    elif mode == "return":

        if not participant:
            return render_template(
                "enter.html",
                error=(
                    "등록되지 않은 닉네임입니다. "
                    "처음 참여한다면 "
                    "‘새 닉네임 만들기’를 선택해 주세요."
                ),
                nickname=nickname,
            ), 404

    else:
        return render_template(
            "enter.html",
            error="잘못된 입장 방식입니다.",
            nickname=nickname,
        ), 400

    # 닉네임 정보를 Flask 세션에 저장합니다.
    session.clear()

    session["participant_id"] = participant["id"]
    session["nickname"] = participant["nickname"]

    try:
        supabase = get_supabase()

        (
            supabase.table("participants")
            .update(
                {
                    "last_seen_at": (
                        datetime.now(
                            timezone.utc
                        ).isoformat()
                    )
                }
            )
            .eq(
                "id",
                participant["id"],
            )
            .execute()
        )

    except Exception as error:
        # 마지막 접속 시각 업데이트 실패는
        # 입장을 막을 정도의 오류는 아닙니다.
        print(
            "접속 시각 업데이트 오류:",
            error,
        )

    return redirect(
        url_for("welcome")
    )


@app.route("/api/nickname-check")
def nickname_check():
    """JavaScript에서 사용하는 닉네임 중복 확인 API"""

    raw_nickname = request.args.get(
        "nickname",
        "",
    )

    try:
        nickname = normalize_nickname(
            raw_nickname
        )

    except ValueError as error:
        return jsonify(
            {
                "valid": False,
                "exists": False,
                "message": str(error),
            }
        ), 400

    try:
        exists = (
            find_participant(nickname)
            is not None
        )

    except Exception as error:
        print(
            "닉네임 확인 오류:",
            error,
        )

        return jsonify(
            {
                "valid": False,
                "exists": False,
                "message": (
                    "데이터베이스 연결에 실패했습니다."
                ),
            }
        ), 500

    if exists:
        message = (
            "이미 사용 중인 닉네임입니다."
        )
    else:
        message = (
            "사용 가능한 닉네임입니다."
        )

    return jsonify(
        {
            "valid": True,
            "exists": exists,
            "message": message,
        }
    )


@app.route("/welcome")
def welcome():
    """닉네임 등록 후 임시 입장 완료 페이지"""

    nickname = session.get("nickname")

    if not nickname:
        return redirect(
            url_for("enter")
        )

    return render_template(
        "welcome.html",
        nickname=nickname,
    )

@app.route("/result")
def result():
    nickname = session.get("nickname")

    if not nickname:
        return redirect(
            url_for("enter")
        )

    return render_template(
        "result.html",
        nickname=nickname,
    )


@app.route(
    "/logout",
    methods=["POST"],
)
def logout():
    """현재 브라우저의 세션을 지웁니다."""

    session.clear()

    return redirect(
        url_for("index")
    )


@app.route("/health")
def health():
    """Render에서 서버 상태를 확인할 수 있는 주소"""

    return jsonify(
        {
            "status": "ok",
        }
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
    )