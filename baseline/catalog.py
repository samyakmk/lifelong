from dataclasses import dataclass


@dataclass(frozen=True)
class Plan:
    code: str = "baseline-panel"
    name: str = "Baseline Panel"
    amount_cents: int = 14900
    draw_center_code: str = "alder"
    draw_center: str = "Alder Draw Center"

    @property
    def price(self):
        return f"${self.amount_cents // 100}"


PLAN = Plan()
DRAW_ADDRESS = "184 Alder Way, Oakland, CA (demo)"
DRAW_TIMEZONE = "America/Los_Angeles"
DRAW_PREP = "Bring your appointment confirmation and follow the draw center’s visit instructions."
CONSENT_VERSION = "demo-v1"
CONSENT_TEXT = (
    "I agree to store the fictional details I enter in this local demo "
    "and to create a simulated purchase and lab order."
)
INTAKE_QUESTIONS = {
    "goal": (
        "What brings you to Baseline?",
        {
            "establish_baseline": "Establish a first baseline",
            "track_changes": "Track changes over time",
            "explore_demo": "Explore the demo",
        },
    ),
    "prior_testing": (
        "Have you done routine bloodwork in the past year?",
        {"yes": "Yes", "no": "No", "unsure": "Not sure"},
    ),
    "draw_time": (
        "When would a draw usually work best?",
        {"morning": "Morning", "afternoon": "Afternoon", "flexible": "Either works"},
    ),
}

TEST_GROUPS = (
    ("heart", "Heart health", "Total cholesterol, LDL, HDL and triglycerides"),
    ("metabolic", "Blood sugar", "Glucose and hemoglobin A1c"),
    ("organ", "Liver & kidney", "ALT, AST, creatinine and eGFR"),
    ("blood", "Blood & iron", "Complete blood count and ferritin"),
    ("thyroid", "Thyroid & nutrients", "TSH and vitamin D"),
)
