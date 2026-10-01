"""GAIA-style task suite: tasks that humans find simple but AI finds difficult.

Based on the GAIA benchmark (arXiv: 2311.12983), these tasks test:
- Basic reasoning (math, logic, common sense)
- Multi-step problem solving
- Tool use and information retrieval
- Temporal and spatial reasoning

The key insight: these tasks are conceptually simple for humans but challenging for AI.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class GAIALikeTask:
    id: str
    question: str
    expected_answer: str
    reasoning_steps: list[str] = field(default_factory=list)
    difficulty: str = "easy"  # easy, medium, hard
    category: str = "math"  # math, logic, common_sense, temporal, spatial


# Math reasoning tasks
MATH_TASKS = (
    GAIALikeTask(
        id="math_apples",
        question="If I have 5 apples, eat 2, and buy 3 more, how many apples do I have now?",
        expected_answer="6",
        reasoning_steps=["Start with 5", "Eat 2: 5-2=3", "Buy 3 more: 3+3=6"],
        category="math",
        difficulty="easy",
    ),
    GAIALikeTask(
        id="math_price",
        question="A shirt costs $25. If I buy 3 shirts and pay with a $100 bill, how much change do I get?",
        expected_answer="25",
        reasoning_steps=["3 shirts × $25 = $75", "$100 - $75 = $25 change"],
        category="math",
        difficulty="easy",
    ),
    GAIALikeTask(
        id="math_percentage",
        question="What is 20% of 150?",
        expected_answer="30",
        reasoning_steps=["20% = 0.20", "0.20 × 150 = 30"],
        category="math",
        difficulty="easy",
    ),
    GAIALikeTask(
        id="math_age",
        question="Alice is 30 years old. Bob is 5 years younger than Alice. How old is Bob?",
        expected_answer="25",
        reasoning_steps=["Alice is 30", "Bob is 5 years younger", "30 - 5 = 25"],
        category="math",
        difficulty="easy",
    ),
    GAIALikeTask(
        id="math_distance",
        question="If I walk at 5 km/h for 2 hours, how far do I travel?",
        expected_answer="10",
        reasoning_steps=["Speed = 5 km/h", "Time = 2 hours", "Distance = speed × time = 5 × 2 = 10 km"],
        category="math",
        difficulty="easy",
    ),
)

# Logic reasoning tasks
LOGIC_TASKS = (
    GAIALikeTask(
        id="logic_cats",
        question="All cats are animals. Some animals are pets. Are all cats pets?",
        expected_answer="No",
        reasoning_steps=["All cats are animals", "Some animals are pets", "But not all animals are pets", "So we cannot conclude all cats are pets"],
        category="logic",
        difficulty="medium",
    ),
    GAIALikeTask(
        id="logic_rain",
        question="If it rains, the ground is wet. The ground is wet. Did it rain?",
        expected_answer="Not necessarily",
        reasoning_steps=["If it rains, ground is wet", "Ground is wet", "But ground could be wet for other reasons (sprinkler, etc.)", "Cannot conclude it rained"],
        category="logic",
        difficulty="medium",
    ),
    GAIALikeTask(
        id="logic_syllogism",
        question="All dogs are mammals. All mammals have fur. Do all dogs have fur?",
        expected_answer="Yes",
        reasoning_steps=["All dogs are mammals", "All mammals have fur", "Therefore all dogs have fur"],
        category="logic",
        difficulty="easy",
    ),
    GAIALikeTask(
        id="logic_sequence",
        question="What comes next in the sequence: 2, 4, 6, 8, ?",
        expected_answer="10",
        reasoning_steps=["Sequence increases by 2", "8 + 2 = 10"],
        category="logic",
        difficulty="easy",
    ),
    GAIALikeTask(
        id="logic_comparison",
        question="A is taller than B. B is taller than C. Is A taller than C?",
        expected_answer="Yes",
        reasoning_steps=["A > B (A taller than B)", "B > C (B taller than C)", "Therefore A > C (A taller than C)"],
        category="logic",
        difficulty="easy",
    ),
)

# Common sense tasks
COMMON_SENSE_TASKS = (
    GAIALikeTask(
        id="cs_umbrella",
        question="If it's raining outside, should I bring an umbrella or sunglasses?",
        expected_answer="Umbrella",
        reasoning_steps=["It's raining", "Umbrella protects from rain", "Sunglasses are for sun", "Bring umbrella"],
        category="common_sense",
        difficulty="easy",
    ),
    GAIALikeTask(
        id="cs_hot",
        question="If I touch a hot stove, will I feel cold or pain?",
        expected_answer="Pain",
        reasoning_steps=["Hot stove is dangerous", "Touching it causes injury", "Injury causes pain"],
        category="common_sense",
        difficulty="easy",
    ),
    GAIALikeTask(
        id="cs_food",
        question="Can I eat a rock? Yes or no?",
        expected_answer="No",
        reasoning_steps=["Rocks are not food", "Rocks are hard and inedible", "Cannot eat rocks"],
        category="common_sense",
        difficulty="easy",
    ),
    GAIALikeTask(
        id="cs_time",
        question="Do I wear a swimsuit to the beach or to a funeral?",
        expected_answer="Beach",
        reasoning_steps=["Swimsuit is for swimming", "Beach is for swimming", "Funeral is formal"],
        category="common_sense",
        difficulty="easy",
    ),
    GAIALikeTask(
        id="cs_tool",
        question="What tool do I use to cut paper: scissors or hammer?",
        expected_answer="Scissors",
        reasoning_steps=["Scissors are for cutting", "Hammer is for hitting", "Use scissors for paper"],
        category="common_sense",
        difficulty="easy",
    ),
)

# Temporal reasoning tasks
TEMPORAL_TASKS = (
    GAIALikeTask(
        id="temp_3hours",
        question="If it's 10:00 AM now, what time will it be in 3 hours?",
        expected_answer="1:00 PM",
        reasoning_steps=["Current time: 10:00 AM", "Add 3 hours", "10 + 3 = 13", "13:00 = 1:00 PM"],
        category="temporal",
        difficulty="easy",
    ),
    GAIALikeTask(
        id="temp_yesterday",
        question="If today is Wednesday, what day was yesterday?",
        expected_answer="Tuesday",
        reasoning_steps=["Today is Wednesday", "Yesterday is the day before", "Wednesday - 1 = Tuesday"],
        category="temporal",
        difficulty="easy",
    ),
    GAIALikeTask(
        id="temp_days",
        question="How many days are in a week?",
        expected_answer="7",
        reasoning_steps=["A week has 7 days", "Monday, Tuesday, Wednesday, Thursday, Friday, Saturday, Sunday"],
        category="temporal",
        difficulty="easy",
    ),
    GAIALikeTask(
        id="temp_months",
        question="How many months are in a year?",
        expected_answer="12",
        reasoning_steps=["A year has 12 months", "January through December"],
        category="temporal",
        difficulty="easy",
    ),
    GAIALikeTask(
        id="temp_duration",
        question="If a movie starts at 7:00 PM and lasts 2 hours, what time does it end?",
        expected_answer="9:00 PM",
        reasoning_steps=["Start time: 7:00 PM", "Duration: 2 hours", "7 + 2 = 9", "End time: 9:00 PM"],
        category="temporal",
        difficulty="easy",
    ),
)

# Spatial reasoning tasks
SPATIAL_TASKS = (
    GAIALikeTask(
        id="spatial_room",
        question="If a room has 4 walls and each wall has 2 windows, how many windows are there in total?",
        expected_answer="8",
        reasoning_steps=["4 walls", "2 windows per wall", "4 × 2 = 8 windows"],
        category="spatial",
        difficulty="easy",
    ),
    GAIALikeTask(
        id="spatial_direction",
        question="If I face north and turn right, which direction am I facing?",
        expected_answer="East",
        reasoning_steps=["Facing north", "Turn right (clockwise)", "North → East"],
        category="spatial",
        difficulty="easy",
    ),
    GAIALikeTask(
        id="spatial_opposite",
        question="What is the opposite of 'up'?",
        expected_answer="Down",
        reasoning_steps=["Up is one direction", "Opposite is down"],
        category="spatial",
        difficulty="easy",
    ),
    GAIALikeTask(
        id="spatial_shape",
        question="How many sides does a triangle have?",
        expected_answer="3",
        reasoning_steps=["Triangle means 3 angles", "3 angles means 3 sides"],
        category="spatial",
        difficulty="easy",
    ),
    GAIALikeTask(
        id="spatial_corners",
        question="How many corners does a cube have?",
        expected_answer="8",
        reasoning_steps=["A cube has 6 faces", "Each face is a square with 4 corners", "But corners are shared", "A cube has 8 corners"],
        category="spatial",
        difficulty="medium",
    ),
)

# Combine all tasks
GAIA_TASKS = MATH_TASKS + LOGIC_TASKS + COMMON_SENSE_TASKS + TEMPORAL_TASKS + SPATIAL_TASKS

GAIA_TASKS_BY_ID = {t.id: t for t in GAIA_TASKS}
