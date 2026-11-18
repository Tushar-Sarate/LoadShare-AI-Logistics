import re

INJECTION_PATTERNS = [
    r"ignore (all |any |your |the |previous |above )*(instructions|rules|prompt)",
    r"(reveal|show|print|tell me) (me )?(your |the )?(system )?(prompt|instructions)",
    r"you are now",
    r"developer mode",
    r"jailbreak",
    r"api[_ ]?key",
    r"forget (everything|your rules)",
]

REFUSAL = (
    "Sorry, I can only help with deliveries, orders, payments, "
    "refunds and complaints."
)


def check_input(question: str):
    text = question.lower()

    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, text):
            return REFUSAL

    return None