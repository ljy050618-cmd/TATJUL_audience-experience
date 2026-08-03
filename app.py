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


# 조사에서 측정하는 네 가지 공동체 성향
SURVEY_DIMENSIONS = {
    "order": {
        "name": "규율",
        "description": "공동체의 기준, 책임, 절차를 중시합니다.",
    },
    "solidarity": {
        "name": "연대",
        "description": "관계, 신뢰, 구성원의 안전을 중시합니다.",
    },
    "autonomy": {
        "name": "자율",
        "description": "개인의 판단, 진실성, 독립성을 중시합니다.",
    },
    "change": {
        "name": "변화",
        "description": "새로운 해결책, 행동, 구조의 변화를 중시합니다.",
    },
}


# 각 문항은 네 선택지로 구성된다.
# 선택지 순서는 항상 규율·연대·자율·변화 순서가 아니다.
SURVEY_QUESTIONS = [
    {
        "situation": "학급에서 중요한 행사를 준비하던 중 역할 분담에 불만이 생겼다.",
        "question": "가장 먼저 해야 할 일은 무엇이라고 생각하는가?",
        "options": [
            {
                "text": "처음 정한 역할과 기준을 다시 확인한다.",
                "dimension": "order",
            },
            {
                "text": "각자가 왜 불만을 느끼는지 차례로 듣는다.",
                "dimension": "solidarity",
            },
            {
                "text": "내 역할은 내가 판단해 필요한 일을 먼저 한다.",
                "dimension": "autonomy",
            },
            {
                "text": "기존 역할 분담을 버리고 새로운 방식을 제안한다.",
                "dimension": "change",
            },
        ],
    },
    {
        "situation": "친한 친구가 규칙을 어긴 사실을 우연히 알게 되었다.",
        "question": "당신은 어떻게 행동하겠는가?",
        "options": [
            {
                "text": "친구라도 정해진 절차에 따라 알려야 한다.",
                "dimension": "order",
            },
            {
                "text": "먼저 친구가 그런 행동을 한 이유를 묻는다.",
                "dimension": "solidarity",
            },
            {
                "text": "다른 사람의 판단보다 내 양심에 따라 결정한다.",
                "dimension": "autonomy",
            },
            {
                "text": "규칙 자체가 타당한지도 함께 문제 제기한다.",
                "dimension": "change",
            },
        ],
    },
    {
        "situation": "회의에서 다수의 의견이 빠르게 하나로 모였다.",
        "question": "당신이 가장 신경 쓰는 부분은 무엇인가?",
        "options": [
            {
                "text": "결정 과정이 정해진 절차를 따랐는가.",
                "dimension": "order",
            },
            {
                "text": "말하지 못한 사람이 소외되지 않았는가.",
                "dimension": "solidarity",
            },
            {
                "text": "다수 의견과 달라도 내 생각을 말할 수 있는가.",
                "dimension": "autonomy",
            },
            {
                "text": "익숙한 결론만 반복하고 있지는 않은가.",
                "dimension": "change",
            },
        ],
    },
    {
        "situation": "팀원이 반복해서 약속 시간에 늦는다.",
        "question": "가장 적절한 대응은 무엇인가?",
        "options": [
            {
                "text": "지각에 대한 명확한 기준과 책임을 적용한다.",
                "dimension": "order",
            },
            {
                "text": "지각할 수밖에 없는 사정이 있는지 살핀다.",
                "dimension": "solidarity",
            },
            {
                "text": "그 사람에게 직접 문제를 말하고 내 경계를 정한다.",
                "dimension": "autonomy",
            },
            {
                "text": "모두가 지키기 쉬운 새로운 시간 운영 방식을 만든다.",
                "dimension": "change",
            },
        ],
    },
    {
        "situation": "학교의 오래된 전통이 일부 학생에게 부담이 되고 있다.",
        "question": "당신의 선택과 가장 가까운 것은?",
        "options": [
            {
                "text": "전통을 유지하되 예외 기준을 명확히 만든다.",
                "dimension": "order",
            },
            {
                "text": "부담을 느끼는 학생들의 경험을 먼저 듣는다.",
                "dimension": "solidarity",
            },
            {
                "text": "참여 여부는 학생 개인이 선택해야 한다.",
                "dimension": "autonomy",
            },
            {
                "text": "현재에 맞지 않는 전통은 과감히 바꿔야 한다.",
                "dimension": "change",
            },
        ],
    },
    {
        "situation": "모둠 과제에서 한 사람이 거의 참여하지 않았다.",
        "question": "평가할 때 어떤 태도를 취하겠는가?",
        "options": [
            {
                "text": "실제 기여도에 따라 정확하게 평가한다.",
                "dimension": "order",
            },
            {
                "text": "참여하지 못한 사정을 먼저 확인한다.",
                "dimension": "solidarity",
            },
            {
                "text": "다른 사람과 상관없이 내가 한 일을 분명히 밝힌다.",
                "dimension": "autonomy",
            },
            {
                "text": "개별 평가가 가능한 과제 방식으로 바꾸자고 제안한다.",
                "dimension": "change",
            },
        ],
    },
    {
        "situation": "소문 때문에 한 학생이 공동체에서 멀어지고 있다.",
        "question": "당신은 무엇을 우선하겠는가?",
        "options": [
            {
                "text": "사실 확인 절차를 만들고 확인되지 않은 말은 금지한다.",
                "dimension": "order",
            },
            {
                "text": "소문으로 상처받은 학생 곁에 먼저 다가간다.",
                "dimension": "solidarity",
            },
            {
                "text": "주변 분위기와 관계없이 내가 확인한 사실만 믿는다.",
                "dimension": "autonomy",
            },
            {
                "text": "소문이 퍼지는 구조와 문화를 공개적으로 문제 삼는다.",
                "dimension": "change",
            },
        ],
    },
    {
        "situation": "학급 대표가 독단적으로 결정을 내렸다.",
        "question": "당신의 반응은?",
        "options": [
            {
                "text": "대표의 권한과 의사결정 규정을 확인한다.",
                "dimension": "order",
            },
            {
                "text": "대표와 구성원 모두의 입장을 조정한다.",
                "dimension": "solidarity",
            },
            {
                "text": "그 결정에 동의하지 않는다는 입장을 분명히 밝힌다.",
                "dimension": "autonomy",
            },
            {
                "text": "대표 한 사람에게 권한이 몰리지 않는 구조를 제안한다.",
                "dimension": "change",
            },
        ],
    },
    {
        "situation": "두 친구가 서로 자신이 옳다며 당신에게 편을 들어 달라고 한다.",
        "question": "어떤 태도를 취하겠는가?",
        "options": [
            {
                "text": "공통으로 적용할 수 있는 기준을 찾아 판단한다.",
                "dimension": "order",
            },
            {
                "text": "두 사람의 감정이 가라앉도록 대화를 돕는다.",
                "dimension": "solidarity",
            },
            {
                "text": "누구의 편도 들지 않고 내 판단을 말한다.",
                "dimension": "autonomy",
            },
            {
                "text": "둘 중 하나를 고르는 방식 자체에서 벗어난 해결책을 찾는다.",
                "dimension": "change",
            },
        ],
    },
    {
        "situation": "공동체 전체를 위해 일부 구성원의 희생이 필요하다는 의견이 나왔다.",
        "question": "당신이 가장 중요하게 보는 것은?",
        "options": [
            {
                "text": "누구에게나 동일한 책임 원칙이 적용되는가.",
                "dimension": "order",
            },
            {
                "text": "희생을 요구받는 사람이 보호받을 수 있는가.",
                "dimension": "solidarity",
            },
            {
                "text": "개인이 희생을 거부할 권리가 있는가.",
                "dimension": "autonomy",
            },
            {
                "text": "희생 없이 해결할 다른 방법은 없는가.",
                "dimension": "change",
            },
        ],
    },
    {
        "situation": "회의 시간이 부족해 충분한 토론 없이 결정을 내려야 한다.",
        "question": "당신의 선택은?",
        "options": [
            {
                "text": "책임자가 정해진 권한에 따라 임시 결정을 내린다.",
                "dimension": "order",
            },
            {
                "text": "최소한 반대 의견을 가진 사람의 말은 듣는다.",
                "dimension": "solidarity",
            },
            {
                "text": "동의하지 않는 결정에는 참여하지 않을 수 있어야 한다.",
                "dimension": "autonomy",
            },
            {
                "text": "결정을 미루고 더 빠른 의견 수렴 방식을 시도한다.",
                "dimension": "change",
            },
        ],
    },
    {
        "situation": "새로 온 학생이 기존 분위기에 적응하지 못하고 있다.",
        "question": "당신이 할 가능성이 가장 높은 행동은?",
        "options": [
            {
                "text": "학교 규칙과 생활 방식을 차근차근 알려 준다.",
                "dimension": "order",
            },
            {
                "text": "먼저 말을 걸고 함께할 사람을 연결해 준다.",
                "dimension": "solidarity",
            },
            {
                "text": "억지로 섞이게 하기보다 스스로 적응할 시간을 준다.",
                "dimension": "autonomy",
            },
            {
                "text": "기존 학생들도 새 학생에게 맞춰 변해야 한다고 말한다.",
                "dimension": "change",
            },
        ],
    },
    {
        "situation": "모두가 따르는 방식이 비효율적이라는 사실을 발견했다.",
        "question": "어떻게 하겠는가?",
        "options": [
            {
                "text": "문제점을 정리해 공식적인 절차로 개선을 요청한다.",
                "dimension": "order",
            },
            {
                "text": "변화로 불편해질 사람들의 의견을 먼저 살핀다.",
                "dimension": "solidarity",
            },
            {
                "text": "내가 맡은 부분부터 더 나은 방식으로 처리한다.",
                "dimension": "autonomy",
            },
            {
                "text": "실패 가능성이 있더라도 새로운 방식을 즉시 시험한다.",
                "dimension": "change",
            },
        ],
    },
    {
        "situation": "친구가 다른 사람에게 상처가 될 말을 했지만 악의는 없었다.",
        "question": "당신의 판단은?",
        "options": [
            {
                "text": "의도와 관계없이 잘못된 행동에 책임을 져야 한다.",
                "dimension": "order",
            },
            {
                "text": "상처받은 사람과 말한 사람 모두의 마음을 살핀다.",
                "dimension": "solidarity",
            },
            {
                "text": "내가 부당하다고 생각하면 친구에게 직접 말한다.",
                "dimension": "autonomy",
            },
            {
                "text": "비슷한 일이 반복되지 않도록 대화 방식을 바꾼다.",
                "dimension": "change",
            },
        ],
    },
    {
        "situation": "공동체를 지키기 위해 어떤 사실을 숨겨야 한다는 주장이 나왔다.",
        "question": "당신과 가장 가까운 입장은?",
        "options": [
            {
                "text": "공개 여부는 정해진 책임자와 규정이 판단해야 한다.",
                "dimension": "order",
            },
            {
                "text": "공개로 인해 다칠 사람들을 먼저 고려해야 한다.",
                "dimension": "solidarity",
            },
            {
                "text": "진실을 말할지는 개인의 양심에 달려 있다.",
                "dimension": "autonomy",
            },
            {
                "text": "사실을 숨겨야 유지되는 공동체라면 구조를 바꿔야 한다.",
                "dimension": "change",
            },
        ],
    },
    {
        "situation": "당신의 의견이 반 전체의 의견과 다르다.",
        "question": "어떻게 하겠는가?",
        "options": [
            {
                "text": "결정 절차가 공정했다면 다수의 결정을 따른다.",
                "dimension": "order",
            },
            {
                "text": "갈등이 커지지 않도록 표현 방식을 조절한다.",
                "dimension": "solidarity",
            },
            {
                "text": "불이익이 있더라도 내 의견을 분명히 말한다.",
                "dimension": "autonomy",
            },
            {
                "text": "모두가 생각하지 못한 새로운 선택지를 제시한다.",
                "dimension": "change",
            },
        ],
    },
    {
        "situation": "공동 프로젝트가 실패할 가능성이 높아졌다.",
        "question": "당신은 무엇을 선택하겠는가?",
        "options": [
            {
                "text": "역할과 책임을 다시 정리하고 계획대로 수습한다.",
                "dimension": "order",
            },
            {
                "text": "팀원들이 지치지 않도록 분위기와 관계를 돌본다.",
                "dimension": "solidarity",
            },
            {
                "text": "내가 책임질 수 있는 부분에 집중한다.",
                "dimension": "autonomy",
            },
            {
                "text": "처음 목표를 포기하고 새로운 목표를 세운다.",
                "dimension": "change",
            },
        ],
    },
    {
        "situation": "누군가 공동체를 비판하자 주변 사람들이 불편해한다.",
        "question": "당신의 반응은?",
        "options": [
            {
                "text": "비판도 정해진 방식과 근거를 갖춰야 한다고 본다.",
                "dimension": "order",
            },
            {
                "text": "비판한 사람과 불편해진 사람 사이의 대화를 돕는다.",
                "dimension": "solidarity",
            },
            {
                "text": "불편함 때문에 비판할 권리가 막혀서는 안 된다고 본다.",
                "dimension": "autonomy",
            },
            {
                "text": "그 비판을 계기로 기존 문화를 다시 검토한다.",
                "dimension": "change",
            },
        ],
    },
    {
        "situation": "규칙을 엄격히 적용하면 공정하지만 한 사람에게 큰 피해가 생긴다.",
        "question": "당신의 선택은?",
        "options": [
            {
                "text": "예외가 반복되지 않도록 원칙대로 처리한다.",
                "dimension": "order",
            },
            {
                "text": "피해를 최소화할 수 있는 배려 방안을 찾는다.",
                "dimension": "solidarity",
            },
            {
                "text": "당사자가 자신의 선택을 직접 결정하도록 한다.",
                "dimension": "autonomy",
            },
            {
                "text": "이런 피해를 만드는 규칙 자체를 고친다.",
                "dimension": "change",
            },
        ],
    },
    {
        "situation": "갈등이 오래 이어져 누구도 먼저 양보하려 하지 않는다.",
        "question": "마지막으로 당신이 선택할 행동은?",
        "options": [
            {
                "text": "합의가 안 되면 정해진 권한과 절차로 결정한다.",
                "dimension": "order",
            },
            {
                "text": "서로가 받아들일 수 있는 최소한의 합의를 찾는다.",
                "dimension": "solidarity",
            },
            {
                "text": "타협보다 내가 옳다고 생각하는 입장을 지킨다.",
                "dimension": "autonomy",
            },
            {
                "text": "현재 논쟁과 전혀 다른 새로운 해결 방식을 제시한다.",
                "dimension": "change",
            },
        ],
    },
]


# 네 단일 성향 + 여섯 조합 = 등장인물 10명
RESULT_PROFILES = {
    "order": {
        "type": "원칙의 수호자형",
        "character": "댄포스",
        "summary": (
            "공동체가 흔들릴수록 명확한 기준과 책임이 "
            "필요하다고 생각하는 유형입니다."
        ),
    },
    "solidarity": {
        "type": "관계의 중재자형",
        "character": "레베카 너스",
        "summary": (
            "갈등 속에서도 사람과 사람 사이의 신뢰를 "
            "회복하는 일을 우선하는 유형입니다."
        ),
    },
    "autonomy": {
        "type": "독립적 판단자형",
        "character": "존 프록터",
        "summary": (
            "다수의 시선보다 자신의 양심과 판단을 "
            "중요하게 여기는 유형입니다."
        ),
    },
    "change": {
        "type": "판을 바꾸는 행동가형",
        "character": "애비게일",
        "summary": (
            "기존 질서에 머물기보다 상황을 움직이고 "
            "새로운 국면을 만드는 유형입니다."
        ),
    },
    "order+solidarity": {
        "type": "책임 있는 조정자형",
        "character": "헤일 목사",
        "summary": (
            "원칙을 존중하면서도 구성원의 목소리를 듣고 "
            "균형점을 찾으려는 유형입니다."
        ),
    },
    "order+autonomy": {
        "type": "냉정한 기준자형",
        "character": "엘리자베스 프록터",
        "summary": (
            "명확한 기준을 지키면서도 최종 판단은 "
            "스스로 내리려는 유형입니다."
        ),
    },
    "order+change": {
        "type": "제도 개혁자형",
        "character": "패리스 목사",
        "summary": (
            "질서를 유지하되 필요하다면 제도와 운영 방식을 "
            "빠르게 바꾸려는 유형입니다."
        ),
    },
    "solidarity+autonomy": {
        "type": "신뢰 기반 대변자형",
        "character": "자일스 코리",
        "summary": (
            "사람에 대한 의리를 지키면서도 부당한 압력에는 "
            "자신의 목소리를 내는 유형입니다."
        ),
    },
    "solidarity+change": {
        "type": "분위기 전환자형",
        "character": "메리 워런",
        "summary": (
            "관계의 흐름을 민감하게 읽고 공동체가 다른 방향으로 "
            "움직이도록 영향을 주는 유형입니다."
        ),
    },
    "autonomy+change": {
        "type": "저항하는 개척자형",
        "character": "티튜바",
        "summary": (
            "주어진 역할에 머물기보다 독자적인 생존 방식과 "
            "새로운 선택지를 찾는 유형입니다."
        ),
    },
}


def clean_nickname(value: str) -> str:
    return " ".join(
        (value or "").strip().split()
    )


def find_participant(nickname: str):
    response = (
        supabase
        .table("participants")
        .select(
            "id, nickname, class_number, "
            "result_type, result_scores, "
            "result_character, survey_completed_at, "
            "created_at, last_seen_at"
        )
        .eq("nickname", nickname)
        .limit(1)
        .execute()
    )

    if not response.data:
        return None

    return response.data[0]


def assign_class() -> int:
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
    nickname = session.get("nickname")

    if not nickname:
        return None

    return find_participant(nickname)


def calculate_survey_result(answers):
    counts = {
        key: 0
        for key in SURVEY_DIMENSIONS
    }

    for dimension in answers:
        if dimension in counts:
            counts[dimension] += 1

    total = sum(counts.values())

    if total == 0:
        raise ValueError(
            "조사 응답이 없습니다."
        )

    percentages = {
        key: round(
            value / total * 100
        )
        for key, value in counts.items()
    }

    # 반올림 오차를 보정해 합계가 100이 되게 한다.
    difference = 100 - sum(
        percentages.values()
    )

    highest_key = max(
        percentages,
        key=percentages.get,
    )

    percentages[highest_key] += difference

    sorted_dimensions = sorted(
        counts,
        key=counts.get,
        reverse=True,
    )

    first = sorted_dimensions[0]
    second = sorted_dimensions[1]

    # 1위와 2위가 세 문항 이상 차이 나면 단일 유형.
    if counts[first] - counts[second] >= 3:
        profile_key = first
    else:
        profile_key = "+".join(
            sorted([first, second])
        )

        # RESULT_PROFILES 키 순서에 맞추기
        pair_keys = {
            frozenset(
                ["order", "solidarity"]
            ): "order+solidarity",
            frozenset(
                ["order", "autonomy"]
            ): "order+autonomy",
            frozenset(
                ["order", "change"]
            ): "order+change",
            frozenset(
                ["solidarity", "autonomy"]
            ): "solidarity+autonomy",
            frozenset(
                ["solidarity", "change"]
            ): "solidarity+change",
            frozenset(
                ["autonomy", "change"]
            ): "autonomy+change",
        }

        profile_key = pair_keys[
            frozenset([first, second])
        ]

    profile = RESULT_PROFILES[
        profile_key
    ]

    return {
        "type": profile["type"],
        "character": profile["character"],
        "summary": profile["summary"],
        "scores": percentages,
    }


@app.route("/health")
def health():
    return "OK", 200


@app.route("/")
def loading():
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
                "result_scores": None,
                "result_character": None,
                "survey_completed_at": None,
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
        dimensions=SURVEY_DIMENSIONS,
    )


@app.route("/survey-intro")
def survey_intro():
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

    if student.get("result_type"):
        return redirect(
            url_for("survey_result")
        )

    session.pop(
        "survey_answers",
        None,
    )

    return render_template(
        "intro.html",
        student=student,
        question_count=len(
            SURVEY_QUESTIONS
        ),
    )


@app.route(
    "/survey/<int:question_number>",
    methods=["GET", "POST"],
)
def survey_question(question_number):
    student = get_current_student()

    if not student:
        return redirect(
            url_for("students")
        )

    if student.get("result_type"):
        return redirect(
            url_for("survey_result")
        )

    total_questions = len(
        SURVEY_QUESTIONS
    )

    if not (
        1
        <= question_number
        <= total_questions
    ):
        return redirect(
            url_for(
                "survey_question",
                question_number=1,
            )
        )

    answers = session.get(
        "survey_answers",
        [],
    )

    if request.method == "POST":
        selected_dimension = (
            request.form.get(
                "answer"
            )
        )

        valid_dimensions = set(
            SURVEY_DIMENSIONS.keys()
        )

        if (
            selected_dimension
            not in valid_dimensions
        ):
            return render_template(
                "survey_question.html",
                student=student,
                question=SURVEY_QUESTIONS[
                    question_number - 1
                ],
                question_number=question_number,
                total_questions=total_questions,
                progress=round(
                    question_number
                    / total_questions
                    * 100
                ),
                error=(
                    "선택지를 하나 골라 주세요."
                ),
            )

        # 이전 문항으로 돌아왔다가 다시 답한 경우를 처리한다.
        answers = answers[
            : question_number - 1
        ]

        answers.append(
            selected_dimension
        )

        session[
            "survey_answers"
        ] = answers

        session.modified = True

        if (
            question_number
            == total_questions
        ):
            return redirect(
                url_for(
                    "complete_survey"
                )
            )

        return redirect(
            url_for(
                "survey_question",
                question_number=(
                    question_number + 1
                ),
            )
        )

    return render_template(
        "survey_question.html",
        student=student,
        question=SURVEY_QUESTIONS[
            question_number - 1
        ],
        question_number=question_number,
        total_questions=total_questions,
        progress=round(
            (question_number - 1)
            / total_questions
            * 100
        ),
        error=None,
    )


@app.route("/survey/complete")
def complete_survey():
    student = get_current_student()

    if not student:
        return redirect(
            url_for("students")
        )

    if student.get("result_type"):
        return redirect(
            url_for("survey_result")
        )

    answers = session.get(
        "survey_answers",
        [],
    )

    if len(answers) != len(
        SURVEY_QUESTIONS
    ):
        return redirect(
            url_for(
                "survey_question",
                question_number=(
                    len(answers) + 1
                ),
            )
        )

    result = calculate_survey_result(
        answers
    )

    (
        supabase
        .table("participants")
        .update({
            "result_type": result["type"],
            "result_character": (
                result["character"]
            ),
            "result_scores": (
                result["scores"]
            ),
            "survey_completed_at": (
                datetime.now(
                    timezone.utc
                ).isoformat()
            ),
        })
        .eq(
            "id",
            student["id"],
        )
        .execute()
    )

    session.pop(
        "survey_answers",
        None,
    )

    return redirect(
        url_for("survey_result")
    )


@app.route("/survey-result")
def survey_result():
    student = get_current_student()

    if not student:
        return redirect(
            url_for("students")
        )

    if not student.get("result_type"):
        return redirect(
            url_for("survey_intro")
        )

    character_summary = None

    all_profiles = []

    for profile_key, profile in RESULT_PROFILES.items():
        profile_data = {
            "key": profile_key,
            "type": profile["type"],
            "character": profile["character"],
            "summary": profile["summary"],
        }

        all_profiles.append(profile_data)

        if (
            profile["character"]
            == student.get("result_character")
        ):
            character_summary = profile[
                "summary"
            ]

    return render_template(
        "survey_result.html",
        student=student,
        dimensions=SURVEY_DIMENSIONS,
        character_summary=character_summary,
        all_profiles=all_profiles,
    )

@app.route("/logout")
def logout():
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