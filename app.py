import os
import random
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


load_dotenv()


app = Flask(__name__)

app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "development-secret-key",
)


SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SERVICE_ROLE_KEY = os.environ.get(
    "SUPABASE_SERVICE_ROLE_KEY"
)


if not SUPABASE_URL:
    raise RuntimeError(
        "SUPABASE_URL 환경변수가 없습니다."
    )

if not SUPABASE_SERVICE_ROLE_KEY:
    raise RuntimeError(
        "SUPABASE_SERVICE_ROLE_KEY 환경변수가 없습니다."
    )


supabase: Client = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY,
)


CLASS_COUNT = 6
MIN_NICKNAME_LENGTH = 2
MAX_NICKNAME_LENGTH = 20


def clean_nickname(value: str) -> str:
    """
    앞뒤 공백과 연속된 공백을 정리한다.
    """
    return " ".join(
        (value or "").strip().split()
    )


def find_participant(nickname: str):
    """
    닉네임으로 학생 한 명을 조회한다.
    """
    response = (
        supabase
        .table("participants")
        .select(
            "id, nickname, class_number, "
            "result_type, created_at, last_seen_at"
        )
        .eq("nickname", nickname)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def assign_class() -> int:
    """
    인원이 가장 적은 반들 중 하나를
    무작위로 선택한다.
    """
    response = (
        supabase
        .table("participants")
        .select("class_number")
        .execute()
    )

    class_counts = {
        number: 0
        for number in range(
            1,
            CLASS_COUNT + 1,
        )
    }

    for participant in response.data or []:
        class_number = participant.get(
            "class_number"
        )

        if class_number in class_counts:
            class_counts[class_number] += 1

    minimum_count = min(
        class_counts.values()
    )

    candidate_classes = [
        number
        for number, count
        in class_counts.items()
        if count == minimum_count
    ]

    return random.choice(
        candidate_classes
    )


def get_current_student():
    """
    현재 로그인된 학생을 조회한다.
    """
    nickname = session.get("nickname")

    if not nickname:
        return None

    return find_participant(nickname)


@app.route("/health")
def health():
    return "OK", 200

@app.route("/")
def loading():
    """
    QR 접속 직후 로고와 학칙을 보여주는
    짧은 로딩 화면.
    """
    return render_template(
        "loading.html"
    )


@app.route("/students")
def students():
    response = (
        supabase
        .table("participants")
        .select(
            "nickname, class_number, created_at"
        )
        .order(
            "created_at",
            desc=False,
        )
        .execute()
    )

    participants = response.data or []

    student_names = [
        participant["nickname"]
        for participant in participants
    ]

    return render_template(
        "students.html",
        students=participants,
        student_names=student_names,
        student_count=len(participants),
        error=request.args.get("error"),
        message=request.args.get("message"),
    )

@app.route("/check-nickname")
def check_nickname():
    """
    닉네임 중복 확인.
    """
    nickname = clean_nickname(
        request.args.get(
            "nickname",
            "",
        )
    )

    if len(nickname) < MIN_NICKNAME_LENGTH:
        return jsonify({
            "available": False,
            "message": (
                "닉네임은 2자 이상 "
                "입력해 주세요."
            ),
        })

    if len(nickname) > MAX_NICKNAME_LENGTH:
        return jsonify({
            "available": False,
            "message": (
                "닉네임은 20자 이하로 "
                "입력해 주세요."
            ),
        })

    participant = find_participant(
        nickname
    )

    if participant:
        return jsonify({
            "available": False,
            "message": (
                "이미 재학생 명부에 "
                "등록된 이름입니다."
            ),
        })

    return jsonify({
        "available": True,
        "message": (
            "사용 가능한 닉네임입니다."
        ),
    })


@app.route(
    "/register",
    methods=["POST"],
)
def register():
    """
    새로운 학생으로 가입한다.
    """
    nickname = clean_nickname(
        request.form.get(
            "nickname",
            "",
        )
    )

    if not (
        MIN_NICKNAME_LENGTH
        <= len(nickname)
        <= MAX_NICKNAME_LENGTH
    ):
        return redirect(
            url_for(
                "students",
                error=(
                    "닉네임은 2자 이상 "
                    "20자 이하로 입력해 주세요."
                ),
            )
        )

    existing_student = find_participant(
        nickname
    )

    if existing_student:
        return redirect(
            url_for(
                "students",
                error=(
                    "이미 등록된 닉네임입니다. "
                    "기존 학생 로그인을 이용해 주세요."
                ),
            )
        )

    class_number = assign_class()

    try:
        response = (
            supabase
            .table("participants")
            .insert({
                "nickname": nickname,
                "class_number": class_number,
                "result_type": None,
            })
            .execute()
        )
    except Exception:
        return redirect(
            url_for(
                "students",
                error=(
                    "학생 등록에 실패했습니다. "
                    "닉네임을 다시 확인해 주세요."
                ),
            )
        )

    if not response.data:
        return redirect(
            url_for(
                "students",
                error=(
                    "학생 정보를 저장하지 "
                    "못했습니다."
                ),
            )
        )

    student = response.data[0]

    session.clear()
    session["nickname"] = student[
        "nickname"
    ]

    return redirect(
        url_for("record")
    )


@app.route(
    "/login",
    methods=["POST"],
)
def login():
    """
    기존 닉네임으로 로그인한다.
    """
    nickname = clean_nickname(
        request.form.get(
            "nickname",
            "",
        )
    )

    if not nickname:
        return redirect(
            url_for(
                "students",
                error=(
                    "닉네임을 입력해 주세요."
                ),
            )
        )

    student = find_participant(
        nickname
    )

    if not student:
        return redirect(
            url_for(
                "students",
                error=(
                    "재학생 명부에 없는 이름입니다. "
                    "새로운 학생으로 가입해 주세요."
                ),
            )
        )

    (
        supabase
        .table("participants")
        .update({
            "last_seen_at": datetime.now(
                timezone.utc
            ).isoformat(),
        })
        .eq(
            "id",
            student["id"],
        )
        .execute()
    )

    session.clear()
    session["nickname"] = student[
        "nickname"
    ]

    return redirect(
        url_for("record")
    )


@app.route("/record")
def record():
    """
    학생 개인 기록지.
    """
    student = get_current_student()

    if not student:
        session.clear()

        return redirect(
            url_for(
                "students",
                error=(
                    "먼저 가입하거나 "
                    "로그인해 주세요."
                ),
            )
        )

    return render_template(
        "record.html",
        student=student,
    )


@app.route("/survey-intro")
def survey_intro():
    """
    조사 시작 전 어두운 인트로.
    """
    student = get_current_student()

    if not student:
        return redirect(
            url_for(
                "students",
                error=(
                    "먼저 가입하거나 "
                    "로그인해 주세요."
                ),
            )
        )

    return render_template(
        "intro.html",
        student=student,
    )


@app.route("/logout")
def logout():
    """
    현재 로그인 세션 종료.
    """
    session.clear()

    return redirect(
        url_for(
            "students",
            message=(
                "학생 기록 열람이 "
                "종료되었습니다."
            ),
        )
    )


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000,
        debug=True,
    )