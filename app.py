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

CLASS_COUNT = 6
MIN_NICKNAME_LENGTH = 2
MAX_NICKNAME_LENGTH = 20


ANONYMOUS_ADJECTIVES = [
    "고요한",
    "느긋한",
    "용감한",
    "신중한",
    "명랑한",
    "졸린",
    "재빠른",
    "차분한",
    "엉뚱한",
    "다정한",
    "수줍은",
    "당당한",
    "호기심 많은",
    "영리한",
    "부지런한",
    "자유로운",
    "낙천적인",
    "침착한",
    "활기찬",
    "온화한",
    "유쾌한",
    "조용한",
    "대담한",
    "기민한",
    "평화로운",
]


ANONYMOUS_ANIMALS = [
    "너구리",
    "하마",
    "수달",
    "판다",
    "여우",
    "늑대",
    "토끼",
    "고슴도치",
    "다람쥐",
    "코알라",
    "기린",
    "코끼리",
    "얼룩말",
    "사슴",
    "알파카",
    "라마",
    "캥거루",
    "펭귄",
    "부엉이",
    "올빼미",
    "참새",
    "까마귀",
    "두루미",
    "돌고래",
    "고래",
    "물개",
    "해달",
    "북극곰",
    "카피바라",
    "미어캣",
]






from supabase import Client, create_client


load_dotenv()


app = Flask(__name__)


app.secret_key = os.environ.get(
    "FLASK_SECRET_KEY",
    "development-secret-key",
)

@app.template_filter("eul_reul")
def josa_eul_reul(word):
    if not word:
        return ""

    last_char = word[-1]

    if "가" <= last_char <= "힣":
        jongseong = (ord(last_char) - ord("가")) % 28
        return "을" if jongseong else "를"

    return "를"


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
    "T": {
        "name": "진실·검증",
        "description": "확인 가능한 사실과 일관성을 얼마나 중시하는지를 나타냅니다.",
    },
    "O": {
        "name": "질서·제도",
        "description": "공식 절차와 규칙, 조직의 정당성을 얼마나 중시하는지를 나타냅니다.",
    },
    "A": {
        "name": "행동·개입",
        "description": "직접 말하고 개입해 상황을 움직이려는 정도를 나타냅니다.",
    },
    "S": {
        "name": "자기보존",
        "description": "자신의 평판, 지위, 관계와 안전을 지키려는 정도를 나타냅니다.",
    },
}

# 각 문항은 네 선택지로 구성된다.
# 선택지 순서는 항상 규율·연대·자율·변화 순서가 아니다.
SURVEY_QUESTIONS = [
    {
        "question": "동아리 회비가 몇 차례 맞지 않아 한 운영진이 사적으로 사용했다는 의혹이 생겼다. 회장은 회계자료를 확인한 뒤 공식적으로 설명하겠다고 한다. 나는?",
        "options": [
            {"label": "A", "text": "공식 조사 결과를 우선 따른다.", "key": "Q1C"},
            {"label": "B", "text": "직접 자료와 당사자 말을 확인한다.", "key": "Q1A"},
            {"label": "C", "text": "평판과 주변 정황으로 스스로 판단한다.", "key": "Q1D"},
            {"label": "D", "text": "공식 절차에서 근거를 확인한 뒤 판단한다.", "key": "Q1B"},
        ],
    },

    {
        "question": "단체 채팅방에서 한 선배가 후배를 비하했다는 캡처가 퍼졌다. 캡처에는 대화 앞뒤가 잘려 있고 원본은 아직 공개되지 않았다. 나는?",
        "options": [
            {"label": "A", "text": "원본을 확인할 때까지 반응하지 않는다.", "key": "Q2B"},
            {"label": "B", "text": "확실하지 않으니 관여하지 않는다.", "key": "Q2D"},
            {"label": "C", "text": "원본을 확인하고, 틀렸다면 바로 정정한다.", "key": "Q2A"},
            {"label": "D", "text": "위험할 수 있으니 우선 주변에 알린다.", "key": "Q2C"},
        ],
    },

    {
        "question": "의과대학 실습 조에서 한 학생이 '무성의한 태도'를 이유로 낮은 평가를 받았다. 나는 평가가 과하다고 느끼지만, 이의를 제기하면 이후 실습평가에 불이익이 생길까 걱정된다. 나는?",
        "options": [
            {"label": "A", "text": "공개적으로 문제 삼지 않고 내 피해를 피한다.", "key": "Q3D"},
            {"label": "B", "text": "절차 안에서 의견을 내되, 결정되면 따른다.", "key": "Q3B"},
            {"label": "C", "text": "부당하다면 따르지 않고 불이익을 감수한다.", "key": "Q3C"},
            {"label": "D", "text": "정식 절차로 이의를 제기하고 불이익을 감수한다.", "key": "Q3A"},
        ],
    },

    {
        "question": "친한 사람이 과제 표절 의혹으로 단체방에서 공개 비판을 받고 있다. 아직 원본 자료는 확인되지 않았고, 그 사람을 돕다 보면 나도 감싸는 사람으로 보일 수 있다. 나는?",
        "options": [
            {"label": "A", "text": "앞장서진 않지만 곁을 지킨다.", "key": "Q4C"},
            {"label": "B", "text": "공개적으로 해명할 기회를 요구한다.", "key": "Q4A"},
            {"label": "C", "text": "상황이 정리될 때까지 거리를 둔다.", "key": "Q4D"},
            {"label": "D", "text": "위험이 적은 방식으로 적극 돕는다.", "key": "Q4B"},
        ],
    },

    {
        "question": "공용 물품이 반복해서 사라진 뒤 여러 사람이 같은 구성원을 의심하기 시작했고 담당자도 그 사람을 따로 불렀다. 하지만 직접적인 증거는 아직 없다. 나는?",
        "options": [
            {"label": "A", "text": "공식 검토의 근거를 확인한 뒤 따른다.", "key": "Q5B"},
            {"label": "B", "text": "다수의 증언과 공식 판단을 우선 믿는다.", "key": "Q5C"},
            {"label": "C", "text": "평소 평판과 정황을 보고 판단한다.", "key": "Q5D"},
            {"label": "D", "text": "자료를 직접 확인해 독립적으로 판단한다.", "key": "Q5A"},
        ],
    },

    {
        "question": "의과대학 증례 토론에서 교수나 선배 의사가 한 진단을 강하게 주장한다. 하지만 내가 찾아본 자료와 환자 정보만으로는 그 결론이 확실하지 않아 보인다. 나는?",
        "options": [
            {"label": "A", "text": "어느 편도 들지 않고 지켜본다.", "key": "Q6D"},
            {"label": "B", "text": "근거를 묻고 반대 자료가 있으면 바로 제시한다.", "key": "Q6A"},
            {"label": "C", "text": "경험을 믿고 그 판단에 맞춰 행동한다.", "key": "Q6C"},
            {"label": "D", "text": "조용히 자료를 더 확인한다.", "key": "Q6B"},
        ],
    },

    {
        "question": "학생회·동아리·직장 행사에서 운영진의 실수로 참가자에게 잘못된 안내가 나갔다. 내부에서는 공식 공지가 나갈 때까지 밖에 이야기하지 말라고 한다. 나는?",
        "options": [
            {"label": "A", "text": "필요하면 밖에 사실을 알리고 불이익을 감수한다.", "key": "Q7C"},
            {"label": "B", "text": "공식 발표 전까지 외부 발언을 삼간다.", "key": "Q7B"},
            {"label": "C", "text": "정식 내부 절차로 끝까지 문제를 제기한다.", "key": "Q7A"},
            {"label": "D", "text": "말하지 않고 내 책임을 피할 기록부터 남긴다.", "key": "Q7D"},
        ],
    },

    {
        "question": "모임 단체방에서 한 사람의 말실수가 반복해서 캡처되며 조롱거리로 번졌다. 나도 그 사람에게 아쉬운 점은 있지만 분위기가 지나치다고 느낀다. 나는?",
        "options": [
            {"label": "A", "text": "분위기를 돌리거나 당사자에게 따로 연락한다.", "key": "Q8B"},
            {"label": "B", "text": "상황에서 거리를 두고 관여하지 않는다.", "key": "Q8D"},
            {"label": "C", "text": "집단과 맞서진 않지만 그 사람 곁에 남는다.", "key": "Q8C"},
            {"label": "D", "text": "그 자리에서 그만하자고 말한다.", "key": "Q8A"},
        ],
    },

    {
        "question": "친구 사이의 갈등에서 내가 알고 있는 사실 하나를 밝히면 현재의 오해를 풀 수 있다. 하지만 그 사실을 말하려면 예전에 내가 했던 잘못도 함께 드러난다. 나는?",
        "options": [
            {"label": "A", "text": "내 피해가 크다면 공개하지 않는다.", "key": "Q9D"},
            {"label": "B", "text": "가까운 사람을 지키기 위해 일부를 숨긴다.", "key": "Q9C"},
            {"label": "C", "text": "내 실수까지 모두 밝히고 결과를 감수한다.", "key": "Q9A"},
            {"label": "D", "text": "익명·비밀보장 방식으로 사실을 알린다.", "key": "Q9B"},
        ],
    },

    {
        "question": "소속 조직이 참석 여부와 상관없이 모든 구성원에게 같은 방식의 의무 활동을 새로 부과했다. 취지는 이해하지만 실제로는 일부 사람에게 지나치게 불리하다고 느낀다. 나는?",
        "options": [
            {"label": "A", "text": "일단 따르며 재검토를 기다린다.", "key": "Q10B"},
            {"label": "B", "text": "정식 통로로 규칙을 바꾸려 적극 움직인다.", "key": "Q10A"},
            {"label": "C", "text": "앞장서지 않고 개인적으로 우회한다.", "key": "Q10D"},
            {"label": "D", "text": "직접 거부하거나 사람을 모아 변화를 만든다.", "key": "Q10C"},
        ],
    },

    {
        "question": "회의나 모임에서 납득하기 어려운 운영 방식이 몇 달째 반복되고 있다. 아직 내게 직접적인 큰 피해는 없지만 계속 불만이 쌓이고 있다. 나는?",
        "options": [
            {"label": "A", "text": "공개석상에서도 문제를 꺼내는 편이다.", "key": "Q11C"},
            {"label": "B", "text": "선을 넘기 전까지는 쉽게 나서지 않는다.", "key": "Q11D"},
            {"label": "C", "text": "영향과 책임을 따져본 뒤 필요하면 말한다.", "key": "Q11B"},
            {"label": "D", "text": "불만이 생기면 비교적 바로 말한다.", "key": "Q11A"},
        ],
    },
]

SCORING_KEY = {
    # Q1 — T / O
    "Q1A": {"T": 1, "O": 0},
    "Q1B": {"T": 1, "O": 1},
    "Q1C": {"T": 0, "O": 1},
    "Q1D": {"T": 0, "O": 0},

    # Q2 — T / A
    "Q2A": {"T": 1, "A": 1},
    "Q2B": {"T": 1, "A": 0},
    "Q2C": {"T": 0, "A": 1},
    "Q2D": {"T": 0, "A": 0},

    # Q3 — O / S
    "Q3A": {"O": 1, "S": 0},
    "Q3B": {"O": 1, "S": 1},
    "Q3C": {"O": 0, "S": 0},
    "Q3D": {"O": 0, "S": 1},

    # Q4 — A / S
    "Q4A": {"A": 1, "S": 0},
    "Q4B": {"A": 1, "S": 1},
    "Q4C": {"A": 0, "S": 0},
    "Q4D": {"A": 0, "S": 1},

    # Q5 — T / O
    "Q5A": {"T": 1, "O": 0},
    "Q5B": {"T": 1, "O": 1},
    "Q5C": {"T": 0, "O": 1},
    "Q5D": {"T": 0, "O": 0},

    # Q6 — T / A
    "Q6A": {"T": 1, "A": 1},
    "Q6B": {"T": 1, "A": 0},
    "Q6C": {"T": 0, "A": 1},
    "Q6D": {"T": 0, "A": 0},

    # Q7 — O / S
    "Q7A": {"O": 1, "S": 0},
    "Q7B": {"O": 1, "S": 1},
    "Q7C": {"O": 0, "S": 0},
    "Q7D": {"O": 0, "S": 1},

    # Q8 — A / S
    "Q8A": {"A": 1, "S": 0},
    "Q8B": {"A": 1, "S": 1},
    "Q8C": {"A": 0, "S": 0},
    "Q8D": {"A": 0, "S": 1},

    # Q9 — T / S
    "Q9A": {"T": 1, "S": 0},
    "Q9B": {"T": 1, "S": 1},
    "Q9C": {"T": 0, "S": 0},
    "Q9D": {"T": 0, "S": 1},

    # Q10 — O / A
    "Q10A": {"O": 1, "A": 1},
    "Q10B": {"O": 1, "A": 0},
    "Q10C": {"O": 0, "A": 1},
    "Q10D": {"O": 0, "A": 0},
}



# 네 단일 성향 + 여섯 조합 = 등장인물 10명







def generate_random_nickname():
    response = (
        supabase
        .table("participants")
        .select("nickname")
        .execute()
    )

    used_nicknames = {
        participant["nickname"]
        for participant in (response.data or [])
        if participant.get("nickname")
    }

    available_nicknames = [
        f"익명의 {adjective} {animal}"
        for adjective in ANONYMOUS_ADJECTIVES
        for animal in ANONYMOUS_ANIMALS
        if f"익명의 {adjective} {animal}"
        not in used_nicknames
    ]

    if not available_nicknames:
        raise RuntimeError(
            "사용 가능한 랜덤 닉네임이 모두 소진되었습니다."
        )

    return random.choice(
        available_nicknames
    )


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


RESULT_PROFILES = {
    "proctor": {
        "type": "갈등하는 저항자형",
        "character": "프록터",
        "summary": (
            "당신은 자신을 정의로운 사람이라고 쉽게 믿지 않습니다. 자신의 잘못과 모순을 알고 있기에, 누군가를 비판하거나 진실을 말하려 할 때조차 ‘내가 그럴 자격이 있는가’를 먼저 묻게 됩니다.하지만 침묵이 계속될수록, 아무것도 하지 않는 선택 역시 하나의 선택이라는 사실과 마주하게 됩니다. 결국 당신에게 중요한 것은 완벽한 사람이 되는 것이 아니라, 자신의 잘못을 인정한 뒤에도 무엇을 옳다고 선택할 것인가입니다."
        ),
        "one_line": (
            "옳다고 믿는 것을 지키고 싶지만, 그 선택이 가져올 대가까지 깊이 고민합니다."
        ),
        "strength": (
            "끝까지 남아 있는 양심과 자기 판단"
        ),
        "shaken": (
            "진실을 말하려면 가장 숨기고 싶은 자신의 모습까지 인정해야 할 때"
        ),
        "fear": (
            "살아남기 위해 스스로를 배반하게 되는 것"
        ),
        "watch": (
            "프록터가 누구를 지키려 하는지만 보지 마세요.그가 왜 스스로를 쉽게 용서하지 못하는지, 그리고 언제부터 바깥의 마녀사냥과 싸우는 일이 자기 자신과의 싸움으로 바뀌는지 지켜보세요."
            "마침내 자신의 목소리를 내는 순간을 비교해 보세요."
        ),
        
    },

    "giles": {
        "type": "거침없는 저항자형",
        "character": "자일스",
        "summary": (
            "당신은 주변의 분위기만으로 누군가를 단정하기보다, 실제로 무엇이 벌어졌는지 직접 확인하려 합니다. 의심이 생기면 사람들을 찾아다니며 증언과 근거를 모으고, 자신의 판단이 서면 권위 있는 사람 앞에서도 물러서지 않습니다. 마녀사냥 속에서 당신은 불만을 속으로 삼키기보다 밖으로 드러내고, 잘못된 흐름을 멈추기 위해 사람들을 설득하며 맞서는 사람입니다."
        ),
        "one_line": (
            "문제가 있다고 느끼면 오래 망설이기보다 "
            "직접 말하고 부딪히는 편입니다."
        ),
        "strength": (
            "부당함을 그냥 넘기지 않고, 직접 확인한 뒤 행동으로 옮기는 추진력"
        ),
        "shaken": (
            "자신의 직설적인 행동이 예상보다 큰 결과를 만들었을 때"
        ),
        "fear": (
            "알고도 아무 말 하지 못한 채 지나치는 것"
        ),
        "watch": (
            "자일스가 단순히 목소리 큰 반항아인지, 아니면 의심을 직접 확인하고 확신이 생기면 끝까지 밀어붙이는 사람인지 지켜보세요. 그리고 그 적극성이 언제 힘이 되고, 언제 자신과 주변 사람에게 또 다른 위험이 되는지도 함께 보세요."
        ),
        
    },

    "abigail": {
        "type": "판을 바꾸는 설계자형",
        "character": "애비게일",
        "summary": (
            "당신은 처음부터 누군가를 공격하기 위해 움직이는 사람은 아닙니다. 오히려 위험이 자신을 향하지 않을 때에는 상황을 살피며 최대한 눈에 띄지 않으려 합니다. 하지만 책임이 자신에게 돌아오거나 통제권을 잃을 것 같아지면, 빠르게 상황을 재해석하고 다른 사람들의 시선을 움직여 자신이 공격받는 위치에서 벗어나려 합니다. 마녀사냥 속에서 당신은 단순히 군중에 휩쓸리는 사람이 아니라, 두려움을 이용해 새로운 흐름을 만들고 그 흐름의 중심에 서는 사람이 될 수 있습니다."
        ),
        "one_line": (
            "상황이 자신에게 불리하게 흘러가더라도 "
            "빠르게 판을 바꾸고 주도권을 잡으려 합니다."
        ),
        "strength": (
            "위기의 흐름을 빠르게 읽고, 주도권을 되찾는 힘"
        ),
        "shaken": (
            "상황의 통제권이 자신에게서 벗어나고, 책임이 자신을 향하기 시작할 때"
        ),
        "fear": (
            "모든 선택권을 잃은 채, 다른 사람의 판단에 자신을 맡겨야 하는 것"
        ),
        "watch": (
            "애비게일이 언제부터 상황에 끌려가는 사람이 아니라 상황을 움직이는 사람으로 바뀌는지 보세요. 그리고 그 과정에서 두려움, 자기보호, 욕망이 어떻게 다른 사람을 지목하는 행동으로 이어지는지 지켜보세요."
        ),
        
    },

    "elizabeth": {
        "type": "곁을 지키는 조력자형",
        "character": "엘리자베스",
        "summary": (
            "당신은 근거 없는 비난에 쉽게 동조하지 않고, 스스로도 책잡힐 일을 만들지 않으려 합니다. 사건이 자신과 직접 관련되지 않았을 때에는 앞장서 문제를 제기하기보다 거리를 두고 자신의 자리를 지키는 편입니다. 하지만 누군가 중요한 선택의 갈림길에 섰을 때에는 대신 결정하려 하지 않고, 그 사람이 자기 기준으로 선택할 수 있도록 버팀목이 되어 줍니다."
        ),
        "one_line": (
            "큰 목소리를 내기보다 자신이 믿는 사람과 원칙을 "
            "조용히 지키는 편입니다."
        ),
        "strength": (
            "감정에 휩쓸리지 않고, 끝까지 곁을 지키는 힘"
        ),
        "shaken": (
            "진실을 말하는 것이 오히려 가까운 사람을 해칠 수 있을 때"
        ),
        "fear": (
            "자신의 판단이 사랑하는 사람에게 상처를 남기는 것"
        ),
        "watch": (
            "엘리자베스가 직접 싸움의 중심에 서는 인물은 아니라는 점에 주목해 보세요. 자신이 상처받은 상황에서도 상대의 선택을 대신하지 않고, 어떤 순간에 다시 그 사람을 지지하기로 하는지 지켜보세요."
        ),
        
    },

    "mary": {
        "type": "흔들리는 양심형",
        "character": "메어리",
        "summary": (
            "당신은 분위기에 휩쓸리고 있으면서도, 어느 순간 지금 벌어지는 일이 잘못되었다는 것을 알아차릴 수 있습니다. 그리고 그 불편함을 외면하지 못해 진실을 말하려고도 합니다. 하지만 그 선택 때문에 집단 전체의 의심과 압박이 자신에게 향하기 시작하면, 옳고 그름보다 혼자 남아 감당해야 할 대가가 훨씬 크게 느껴집니다. 결국 마녀사냥 속에서 당신은 진실을 몰라서가 아니라, 진실을 지키는 데 필요한 용기를 끝까지 유지하지 못해 다시 군중 속으로 돌아갈 수 있는 사람입니다. 대본에서도 메어리는 자신에게 증언과 의심이 집중되자 점점 압도되고, 애비게일 무리의 집단 행동 속에서 자신의 판단을 잃어간다."
        ),
        "one_line": (
            "무엇이 옳은지는 알지만, "
            "혼자 그 선택을 감당해야 할 때 쉽게 흔들립니다."
        ),
        "strength": (
            "잘못을 알아차리고 되돌리려는 양심"
        ),
        "shaken": (
            "다수의 시선과 압박이 자신에게 집중될 때"
        ),
        "fear": (
            "혼자 남겨지거나 집단에서 배제되는 것"
        ),
        "watch": (
            "메어리가 처음 자기 목소리를 내려고 하는 순간과, 주변의 모든 시선이 자신에게 향하기 시작한 순간을 비교해 보세요. 진실을 알고 있는 것과 그 진실을 끝까지 지키는 것이 얼마나 다른 일인지 메어리의 변화를 따라가며 보세요."
        ),
        
    },

    "parris": {
        "type": "자기보존형",
        "character": "패리스",
        "summary": (
            "당신은 혼란이 생겼을 때 진실을 밝히는 것보다, 우선 상황이 자신에게 불리하게 번지지 않도록 관리하려 합니다. 그래서 필요하다면 문제를 축소하거나 외면하고, 반대로 강한 권위에 기대어 색출과 처벌에 힘을 보탤 수도 있습니다. 당신의 선택을 결정하는 것은 일관된 신념보다 지금 무엇이 자신의 위치와 안전을 지켜줄 것인가이며, 사태가 자신까지 위협하기 시작하면 다시 그것을 멈추려 할 수 있습니다."
        ),
        "one_line": (
            "옳고 그름보다, 상황이 자신에게 어떤 책임과 손해를 남길지를 먼저 생각합니다."
        ),
        "strength": (
            "위험의 방향을 빠르게 읽고, 변화한 상황에 자신을 맞추는 감각"
        ),
        "shaken": (
            "자신의 지위나 평판이 직접적으로 위협받을 때"
        ),
        "fear": (
            "쌓아온 지위와 신뢰를 잃고, 모든 책임의 중심에 서는 것"
        ),
        "watch": (
            "패리스가 매 순간 무엇을 옳다고 말하는지보다, 무엇을 잃을까 두려워하는지 보세요. 같은 인물이 사건을 덮으려 하고, 확대하는 데 가담하고, 다시 멈추려 하는 이유가 어디에서 바뀌는지 따라가면 패리스의 역할이 선명해집니다."
        ),
        
    },

    "cheever_herrick": {
        "type": "평범한 집행자형",
        "character": "치버&헤릭",
        "summary": (
            "당신은 질서가 무너지는 상황에서 누군가는 정해진 역할을 수행해야 한다고 생각합니다. 개인적인 감정이나 의심보다 공식적인 권한과 절차를 따르는 것이 오히려 공정하고 책임 있는 태도라고 느낄 수 있습니다. 하지만 그 절차가 잘못된 방향으로 흘러가고 있음을 느끼기 시작해도, 이미 맡은 역할과 책임에서 벗어나 자기 판단으로 멈추는 일은 생각보다 어렵습니다."
        ),
        "one_line": (
            "혼란이 커질수록 자신의 판단보다 맡은 역할과 정해진 절차를 믿고 행동합니다."
        ),
        "strength": (
            "감정에 휩쓸리지 않고, 맡은 일을 끝까지 수행하는 책임감"
        ),
        "shaken": (
            "절차대로 했던 일이 오히려 누군가를 해치고 있음을 깨달을 때"
        ),
        "fear": (
            "정해진 역할에서 벗어나, 결과에 대한 책임을 온전히 스스로 져야 하는 것"
        ),
        "watch": (
            "두 사람이 똑같이 명령을 집행하더라도 왜 그 일을 계속하는지는 같지 않습니다. 절차 자체를 옳다고 믿는 치버와, 학생을 보호하려던 행동에 의문과 죄책감을 느끼면서도 멈추지 못하는 헤릭의 차이를 비교해 보세요."
        ),
        
    },

    "danforth": {
        "type": "권위의 수호자형",
        "character": "댄포스",
        "summary": (
            "당신은 혼란이 커질수록 분명한 기준과 강한 결정이 필요하다고 생각합니다. 판단이 흔들리기 시작하면 지금까지 내려진 결정과 그것을 집행해 온 체계 전체가 무너질 수 있다고 보기 때문입니다. 그래서 반대되는 증언이나 새로운 의혹이 나타나도 그것을 단순한 정보가 아니라 기존 판단과 제도의 정당성을 시험하는 도전으로 받아들일 수 있습니다. 당신은 개인적인 이익을 위해 권위를 지키는 사람이라기보다, 이미 세워진 질서를 무너뜨리지 않는 것이 더 큰 혼란을 막는 길이라고 믿기에 끝까지 자신의 판단을 밀어붙이는 사람입니다."
        ),
        "one_line": (
            "한번 옳다고 판단한 기준은 쉽게 뒤집지 않으며, 개인의 의심보다 전체 질서의 일관성을 지키려 합니다."
        ),
        "strength": (
            "원칙과 기준을 끝까지 유지하는 결단력"
        ),
        "shaken": (
            "자신이 믿어 온 제도의 정당성이 의심받기 시작할 때"
        ),
        "fear": (
            "한 번의 예외가 전체 질서를 무너뜨리는 것"
        ),
        "watch": (
            "댄포스가 단순히 사람들의 말을 듣지 않는 인물이라고 생각하지 말고 보세요. 그에게 한 사람의 의심이 언제 ‘제도 전체에 대한 위협’으로 바뀌는지, 그리고 진실을 확인하는 일보다 자신이 내린 판단의 일관성을 지키는 일이 더 중요해지는 순간이 언제인지 지켜보세요. 프록터에게 공개적이고 완결된 형태의 증거를 요구하는 후반부 행동에서도 이러한 태도가 드러납니다."
        ),
        
    },

    "hale": {
        "type": "각성한 판단자형",
        "character": "헤일",
        "summary": (
            "당신은 불안과 소문이 커질수록 감정보다 근거를 확인하려 하고, 충분한 정보를 바탕으로 판단하려 합니다.처음에는 자신이 믿는 기준과 절차가 문제를 바로잡을 수 있다고 생각해 적극적으로 개입하지만, 그 판단 역시 틀릴 수 있다는 가능성을 닫아두지는 않습니다.새로운 사실이 기존의 확신과 충돌한다면 체면이나 일관성을 지키기보다, 자신의 오류를 인정하고 잘못된 흐름을 바로잡는 쪽을 선택합니다."
        ),
        "one_line": (
            "처음에는 제도와 기준을 믿지만, "
            "모순을 발견하면 자신의 판단을 다시 돌아봅니다."
        ),
        "strength": (
            "확신에 매달리지 않고 판단을 수정할 수 있는 성찰"
        ),
        "shaken": (
            "자신의 전문성과 확신이 오히려 다른 사람을 위험에 빠뜨릴 때"
        ),
        "fear": (
            "틀린 판단을 옳다고 믿은 채 누군가에게 돌이킬 수 없는 피해를 주는 것"
        ),
        "watch": (
            "헤일이 무엇을 근거로 사람들을 판단하는지, 그리고 자신이 믿었던 기준에 의문을 품기 시작하는 순간 무엇이 달라지는지 지켜보세요.확신을 버리는 일이 그에게 후퇴인지, 또 다른 책임의 시작인지 생각해 보세요."
        ),
        
    },

    "rebecca": {
        "type": "흔들리지 않는 온정가형",
        "character": "레베카",
        "summary": (
            "당신은 누군가의 실수나 이상한 행동을 곧바로 악의나 위험의 증거로 받아들이지 않습니다. 사람은 흔들릴 수 있고, 잘못할 수도 있으며, 충분히 기다리고 이해할 여지가 있다고 생각합니다. 그래서 마녀사냥 속에서 당신은 사람을 쉽게 악인으로 규정하지 않는 태도와, 근거 없는 판단에 끝까지 동조하지 않는 원칙으로 집단의 광기에 맞섭니다."
        ),
        "one_line": (
            "사람을 쉽게 의심하지 않으면서도, 모두가 한쪽으로 몰려갈 때는 자신의 기준을 끝까지 지킵니다."
        ),
        "strength": (
            "사람을 쉽게 단정하지 않으면서도, 자신의 기준은 놓지 않는 단단함"
        ),
        "shaken": (
            "선의를 믿고 기다린 태도가 오히려 상황을 막지 못했다는 생각이 들 때"
        ),
        "fear": (
            "두려움 때문에 사람을 이해하려는 마음까지 잃어버리는 것"
        ),
        "watch": (
            "레베카가 단순히 “틀린 말을 믿지 않는 사람”이라고만 생각하지 말고 보세요. 다른 사람들이 사람을 의심하고 분류하기 시작할 때, 레베카가 끝까지 사람을 바라보는 방식과 자신의 원칙을 어떻게 함께 지키는지 지켜보세요."
        ),
    },
    
}


RESULT_CODE_MAP = {
    "+++-": "hale",
    "++++": "hale",

    "++--": "elizabeth",
    "++-+": "elizabeth",

    "+-++": "proctor",

    "--+-": "giles",

    "---+": "mary",
    "+--+": "mary",

    "-+-+": "cheever_herrick",
    "-+--": "cheever_herrick",

    "+---": "rebecca",
    "----": "rebecca",

    "--++": "abigail",

    "-+++": "parris",

    "-++-": "danforth",
}




def calculate_survey_result(answers):
    if len(answers) < 11:
        raise ValueError(
            "모든 문항에 응답해야 합니다."
        )

    # Q1~Q10만 본 채점에 사용
    main_answers = answers[:10]

    # Q11은 보너스 분기용
    bonus_answer = answers[10]

    scores = {
        "T": 0,
        "O": 0,
        "A": 0,
        "S": 0,
    }

    # Q1~Q10 점수 합산
    for answer_key in main_answers:
        scoring = SCORING_KEY.get(
            answer_key
        )

        if scoring is None:
            raise ValueError(
                f"잘못된 응답입니다: {answer_key}"
            )

        for dimension, point in scoring.items():
            scores[dimension] += point

    # 각 축은 5회 측정:
    # 3~5점 = +
    # 0~2점 = -
    signs = {
        dimension: (
            "+"
            if score >= 3
            else "-"
        )
        for dimension, score
        in scores.items()
    }

    # 반드시 T-O-A-S 순서
    result_code = (
        signs["T"]
        + signs["O"]
        + signs["A"]
        + signs["S"]
    )

    # +-+-만 Q11로 분기
    if result_code == "+-+-":
        if bonus_answer in {
            "Q11A",
            "Q11C",
        }:
            profile_key = "giles"

        elif bonus_answer in {
            "Q11B",
            "Q11D",
        }:
            profile_key = "proctor"

        else:
            raise ValueError(
                "Q11 응답이 올바르지 않습니다."
            )

    else:
        profile_key = RESULT_CODE_MAP.get(
            result_code
        )

    # 현재 엑셀에서 아직 배정되지 않은 6개 조합
    if profile_key is None:
        return {
            "type": "미분류",
            "character": "미분류",
            "summary": (
                "현재 설계안에서 이 조합의 "
                "결과지는 아직 확정되지 않았습니다."
            ),
            "scores": scores,
            "code": result_code,
        }

    profile = RESULT_PROFILES[
        profile_key
    ]

    return {
        "type": profile["type"],
        "character": profile["character"],
        "summary": profile["summary"],
        "scores": scores,
        "code": result_code,
    }

   

@app.route("/health")
def health():
    return "OK", 200


@app.route("/")
def loading():
    return redirect(
        url_for("students")
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

    suggested_nickname = generate_random_nickname()

    return render_template(
        "students.html",
        students=participants,
        student_names=student_names,
        student_count=len(participants),
        suggested_nickname=suggested_nickname,
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
                    "기존 학생 로그인을 이용하거나 새로고침해 주세요."
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
        url_for("survey_question")
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

@app.route("/roster")
def roster():
    student = get_current_student()

    if not student:
        return redirect(
            url_for(
                "students",
                error="먼저 로그인해 주세요.",
            )
        )

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

    classes = {
        number: []
        for number in range(
            1,
            CLASS_COUNT + 1
        )
    }

    for participant in participants:
        class_number = participant.get(
            "class_number"
        )

        if class_number in classes:
            classes[class_number].append(
                participant
            )

    return render_template(
        "roster.html",
        student=student,
        classes=classes,
        student_count=len(participants),
    )

@app.route("/survey-stats")
def survey_stats():
    student = get_current_student()

    if not student:
        return redirect(
            url_for("students")
        )

    response = (
        supabase
        .table("participants")
        .select("result_type")
        .execute()
    )

    participants = response.data or []

    type_counts = {
        profile["type"]: 0
        for profile in RESULT_PROFILES.values()
    }

    completed_count = 0

    for participant in participants:
        result_type = participant.get("result_type")

        if result_type in type_counts:
            type_counts[result_type] += 1
            completed_count += 1

    statistics = []

    for profile in RESULT_PROFILES.values():
        type_name = profile["type"]
        count = type_counts[type_name]

        percentage = (
            round(count / completed_count * 100, 1)
            if completed_count > 0
            else 0
        )

        statistics.append({
            "type": type_name,
            "character": profile["character"],
            "count": count,
            "percentage": percentage,
        })

    statistics.sort(
        key=lambda item: item["count"],
        reverse=True,
    )

    return render_template(
        "survey_stats.html",
        student=student,
        statistics=statistics,
        completed_count=completed_count,
    )




@app.route(
    "/survey",
    methods=["GET", "POST"],
)
def survey_question():
    student = get_current_student()

    if not student:
        return redirect(
            url_for("students")
        )

    if student.get("result_type"):
        return redirect(
            url_for("survey_result")
        )

    if request.method == "POST":
        answers = []

        for index in range(
            len(SURVEY_QUESTIONS)
        ):
            selected_answer = request.form.get(
                f"answer_{index}"
            )

            if not selected_answer:
                return render_template(
                    "survey_question.html",
                    student=student,
                    questions=SURVEY_QUESTIONS,
                    error="모든 문항에 응답해 주세요.",
                )

            answers.append(
                selected_answer
            )

        session["survey_answers"] = answers
        session.modified = True

        return redirect(
            url_for("complete_survey")
        )

    return render_template(
        "survey_question.html",
        student=student,
        questions=SURVEY_QUESTIONS,
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
    result_profile = None

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
            character_summary = profile["summary"]
            result_profile = profile



    all_profiles = list(RESULT_PROFILES.values())
    
    return render_template(
        "survey_result.html",
        student=student,
        dimensions=SURVEY_DIMENSIONS,
        character_summary=character_summary,
        result_profile=result_profile,
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
