"""Task suite: code-generation tasks with real executable verifiers.

Each task bundles:
- description: natural-language spec given to the model
- correct: a known-correct reference implementation (what mock "succeeds" with)
- buggy: typical failure modes, each with a stable id / signature / fix hint
- tests: unittest code executed in a subprocess for real verification

Signature contract (verified empirically by scripts/verify_tasks.py):
- signature MUST appear in the variant's own real failure output
- signature MUST NOT appear in any other variant's failure output
  (also must not appear in the correct solution's output)
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class BugVariant:
    id: str
    signature: str  # substring expected in the real failure output
    cause: str
    fix: str
    code: str


@dataclass(frozen=True)
class Task:
    id: str
    description: str
    correct: str
    tests: str
    buggy: tuple[BugVariant, ...] = field(default_factory=tuple)
    base_p: float = 0.35  # P(mock generates correct code on a fresh attempt)


_TEST_HEADER = """\
import unittest

"""


def _tests(body: str) -> str:
    return _TEST_HEADER + body + "\n\nif __name__ == '__main__':\n    unittest.main(verbosity=2)\n"


SAFE_DIVIDE = Task(
    id="safe_divide",
    description=(
        "Write a function `safe_divide(a, b, default=None)` that returns a / b, "
        "and returns `default` when b == 0. "
        "Examples: safe_divide(10, 2) == 5.0; safe_divide(1, 0) is None; safe_divide(1, 0, 0) == 0."
    ),
    correct=(
        "def safe_divide(a, b, default=None):\n"
        "    if b == 0:\n"
        "        return default\n"
        "    return a / b\n"
    ),
    tests=_tests(
        "from solution import safe_divide\n\n"
        "class TestSafeDivide(unittest.TestCase):\n"
        "    def test_normal(self):\n"
        "        self.assertEqual(safe_divide(10, 2), 5.0)\n"
        "    def test_zero_default(self):\n"
        "        self.assertIsNone(safe_divide(1, 0))\n"
        "    def test_zero_custom_default(self):\n"
        "        self.assertEqual(safe_divide(1, 0, 0), 0)\n"
    ),
    buggy=(
        BugVariant(
            id="no_zero_check",
            signature="ZeroDivisionError",
            cause="b == 0 is not handled",
            fix="check b == 0 and return the default value",
            code=(
                "def safe_divide(a, b, default=None):\n"
                "    return a / b\n"
            ),
        ),
        BugVariant(
            id="wrong_default",
            signature="0 is not None",
            cause="returns 0 instead of the default argument when b == 0",
            fix="return `default` (not 0) when b == 0",
            code=(
                "def safe_divide(a, b, default=None):\n"
                "    if b == 0:\n"
                "        return 0\n"
                "    return a / b\n"
            ),
        ),
    ),
    base_p=0.40,
)


IS_PALINDROME = Task(
    id="is_palindrome",
    description=(
        "Write a function `is_palindrome(s)` that returns True if `s` reads the same "
        "forwards and backwards, ignoring case, spaces and punctuation. "
        "Examples: is_palindrome('a man, a plan, a canal: panama') is True; "
        "is_palindrome('race a car') is False; is_palindrome('Aa') is True; is_palindrome('') is True."
    ),
    correct=(
        "import re\n\n"
        "def is_palindrome(s):\n"
        "    cleaned = re.sub(r'[^a-z0-9]', '', s.lower())\n"
        "    return cleaned == cleaned[::-1]\n"
    ),
    tests=_tests(
        "from solution import is_palindrome\n\n"
        "class TestPalindrome(unittest.TestCase):\n"
        "    def test_panama(self):\n"
        "        self.assertTrue(is_palindrome('a man, a plan, a canal: panama'))\n"
        "    def test_not_palindrome(self):\n"
        "        self.assertFalse(is_palindrome('race a car'))\n"
        "    def test_empty(self):\n"
        "        self.assertTrue(is_palindrome(''))\n"
        "    def test_case_insensitive(self):\n"
        "        self.assertTrue(is_palindrome('Aa'))\n"
    ),
    buggy=(
        BugVariant(
            id="no_lowercase",
            signature="FAIL: test_case_insensitive",
            cause="case is not normalized before comparing",
            fix="lower() the string before comparing",
            code=(
                "import re\n\n"
                "def is_palindrome(s):\n"
                "    cleaned = re.sub(r'[^a-zA-Z0-9]', '', s)\n"
                "    return cleaned == cleaned[::-1]\n"
            ),
        ),
        BugVariant(
            id="no_punctuation_strip",
            signature="FAIL: test_panama",
            cause="punctuation and spaces are not removed",
            fix="strip non-alphanumeric characters before comparing",
            code=(
                "def is_palindrome(s):\n"
                "    cleaned = s.lower()\n"
                "    return cleaned == cleaned[::-1]\n"
            ),
        ),
    ),
    base_p=0.40,
)


PARSE_DURATION = Task(
    id="parse_duration",
    description=(
        "Write a function `parse_duration(s)` that parses a duration string into total seconds. "
        "Segments are number+unit where unit is h, m or s, e.g. '1h30m' -> 5400, '45s' -> 45, "
        "'2h' -> 7200, '1h30m15s' -> 5415. Assume only these units appear."
    ),
    correct=(
        "import re\n\n"
        "def parse_duration(s):\n"
        "    total = 0\n"
        "    for value, unit in re.findall(r'(\\d+)([hms])', s):\n"
        "        total += int(value) * {'h': 3600, 'm': 60, 's': 1}[unit]\n"
        "    return total\n"
    ),
    tests=_tests(
        "from solution import parse_duration\n\n"
        "class TestParseDuration(unittest.TestCase):\n"
        "    def test_hours_minutes(self):\n"
        "        self.assertEqual(parse_duration('1h30m'), 5400)\n"
        "    def test_seconds_only(self):\n"
        "        self.assertEqual(parse_duration('45s'), 45)\n"
        "    def test_hours_only(self):\n"
        "        self.assertEqual(parse_duration('2h'), 7200)\n"
        "    def test_all_units(self):\n"
        "        self.assertEqual(parse_duration('1h30m15s'), 5415)\n"
    ),
    buggy=(
        BugVariant(
            id="single_segment",
            signature="3600 != 5400",
            cause="only the first segment is parsed",
            fix="iterate over every number+unit match, not just the first",
            code=(
                "import re\n\n"
                "def parse_duration(s):\n"
                "    m = re.search(r'(\\d+)([hms])', s)\n"
                "    if not m:\n"
                "        return 0\n"
                "    return int(m.group(1)) * {'h': 3600, 'm': 60, 's': 1}[m.group(2)]\n"
            ),
        ),
        BugVariant(
            id="minutes_multiplier",
            signature="3630 != 5400",
            cause="minutes are multiplied by the wrong factor",
            fix="multiply 'm' by 60 (not 1 or 3600)",
            code=(
                "import re\n\n"
                "def parse_duration(s):\n"
                "    total = 0\n"
                "    for value, unit in re.findall(r'(\\d+)([hms])', s):\n"
                "        total += int(value) * {'h': 3600, 'm': 1, 's': 1}[unit]\n"
                "    return total\n"
            ),
        ),
        BugVariant(
            id="no_bare_seconds",
            signature="0 != 45",
            cause="a trailing number without unit is not treated as seconds",
            fix="treat a bare trailing number as seconds",
            code=(
                "import re\n\n"
                "def parse_duration(s):\n"
                "    total = 0\n"
                "    for value, unit in re.findall(r'(\\d+)([hm])', s):\n"
                "        total += int(value) * {'h': 3600, 'm': 60}[unit]\n"
                "    return total\n"
            ),
        ),
    ),
    base_p=0.30,
)


MERGE_INTERVALS = Task(
    id="merge_intervals",
    description=(
        "Write a function `merge_intervals(intervals)` that merges overlapping intervals. "
        "Input is a list of (start, end) tuples in arbitrary order. "
        "Return a list of merged (start, end) tuples sorted by start. "
        "Touching intervals merge: (1,2) and (2,3) -> (1,3). Empty input -> []."
    ),
    correct=(
        "def merge_intervals(intervals):\n"
        "    if not intervals:\n"
        "        return []\n"
        "    ordered = sorted(intervals)\n"
        "    out = [list(ordered[0])]\n"
        "    for start, end in ordered[1:]:\n"
        "        if start <= out[-1][1]:\n"
        "            out[-1][1] = max(out[-1][1], end)\n"
        "        else:\n"
        "            out.append([start, end])\n"
        "    return [tuple(pair) for pair in out]\n"
    ),
    tests=_tests(
        "from solution import merge_intervals\n\n"
        "class TestMergeIntervals(unittest.TestCase):\n"
        "    def test_empty(self):\n"
        "        self.assertEqual(merge_intervals([]), [])\n"
        "    def test_overlap(self):\n"
        "        self.assertEqual(merge_intervals([(1, 3), (2, 6), (8, 10)]), [(1, 6), (8, 10)])\n"
        "    def test_unsorted_input(self):\n"
        "        self.assertEqual(merge_intervals([(8, 10), (1, 3)]), [(1, 3), (8, 10)])\n"
        "    def test_touching(self):\n"
        "        self.assertEqual(merge_intervals([(1, 2), (2, 3)]), [(1, 3)])\n"
        "    def test_nested(self):\n"
        "        self.assertEqual(merge_intervals([(1, 10), (2, 3)]), [(1, 10)])\n"
    ),
    buggy=(
        BugVariant(
            id="no_sort",
            signature="FAIL: test_unsorted_input",
            cause="input is assumed to be sorted",
            fix="sort the intervals by start before merging",
            code=(
                "def merge_intervals(intervals):\n"
                "    if not intervals:\n"
                "        return []\n"
                "    out = [list(intervals[0])]\n"
                "    for start, end in intervals[1:]:\n"
                "        if start <= out[-1][1]:\n"
                "            out[-1][1] = max(out[-1][1], end)\n"
                "        else:\n"
                "            out.append([start, end])\n"
                "    return [tuple(pair) for pair in out]\n"
            ),
        ),
        BugVariant(
            id="no_max_on_merge",
            signature="FAIL: test_nested",
            cause="end is overwritten instead of taking the maximum",
            fix="use max(current_end, new_end) when merging nested intervals",
            code=(
                "def merge_intervals(intervals):\n"
                "    if not intervals:\n"
                "        return []\n"
                "    ordered = sorted(intervals)\n"
                "    out = [list(ordered[0])]\n"
                "    for start, end in ordered[1:]:\n"
                "        if start <= out[-1][1]:\n"
                "            out[-1][1] = end\n"
                "        else:\n"
                "            out.append([start, end])\n"
                "    return [tuple(pair) for pair in out]\n"
            ),
        ),
        BugVariant(
            id="strict_overlap",
            signature="FAIL: test_touching",
            cause="touching intervals (end == start) are treated as disjoint",
            fix="merge when start <= current_end, not only when start < current_end",
            code=(
                "def merge_intervals(intervals):\n"
                "    if not intervals:\n"
                "        return []\n"
                "    ordered = sorted(intervals)\n"
                "    out = [list(ordered[0])]\n"
                "    for start, end in ordered[1:]:\n"
                "        if start < out[-1][1]:\n"
                "            out[-1][1] = max(out[-1][1], end)\n"
                "        else:\n"
                "            out.append([start, end])\n"
                "    return [tuple(pair) for pair in out]\n"
            ),
        ),
    ),
    base_p=0.30,
)


FIB = Task(
    id="fib",
    description=(
        "Write a function `fib(n)` returning the n-th Fibonacci number iteratively, "
        "with fib(0) == 0 and fib(1) == 1. Examples: fib(0) == 0; fib(1) == 1; fib(10) == 55."
    ),
    correct=(
        "def fib(n):\n"
        "    a, b = 0, 1\n"
        "    for _ in range(n):\n"
        "        a, b = b, a + b\n"
        "    return a\n"
    ),
    tests=_tests(
        "from solution import fib\n\n"
        "class TestFib(unittest.TestCase):\n"
        "    def test_zero(self):\n"
        "        self.assertEqual(fib(0), 0)\n"
        "    def test_one(self):\n"
        "        self.assertEqual(fib(1), 1)\n"
        "    def test_ten(self):\n"
        "        self.assertEqual(fib(10), 55)\n"
    ),
    buggy=(
        BugVariant(
            id="off_by_one",
            signature="34 != 55",
            cause="the loop runs one iteration short",
            fix="loop exactly n times (range(n)) starting from a, b = 0, 1",
            code=(
                "def fib(n):\n"
                "    a, b = 0, 1\n"
                "    for _ in range(n - 1):\n"
                "        a, b = b, a + b\n"
                "    return a\n"
            ),
        ),
        BugVariant(
            id="starts_one_one",
            signature="1 != 0",
            cause="the sequence starts at 1, 1 instead of 0, 1",
            fix="the sequence must start a, b = 0, 1 so fib(0) == 0",
            code=(
                "def fib(n):\n"
                "    a, b = 1, 1\n"
                "    for _ in range(n):\n"
                "        a, b = b, a + b\n"
                "    return a\n"
            ),
        ),
    ),
    base_p=0.45,
)


WORD_FREQ = Task(
    id="word_freq",
    description=(
        "Write a function `word_freq(text, k)` that returns the top-k most frequent words "
        "in `text`, lowercased, with punctuation stripped. Words are compared by count "
        "(descending); ties are broken alphabetically (ascending). "
        "Return a list of (word, count) tuples of length min(k, number of distinct words). "
        "Example: word_freq('b a b c a b', 2) -> [('b', 3), ('a', 2)]."
    ),
    correct=(
        "import re\n"
        "from collections import Counter\n\n"
        "def word_freq(text, k):\n"
        "    words = re.findall(r'[a-z0-9]+', text.lower())\n"
        "    counts = Counter(words)\n"
        "    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))\n"
        "    return ranked[:k]\n"
    ),
    tests=_tests(
        "from solution import word_freq\n\n"
        "class TestWordFreq(unittest.TestCase):\n"
        "    def test_basic(self):\n"
        "        self.assertEqual(word_freq('b a b c a b', 2), [('b', 3), ('a', 2)])\n"
        "    def test_tie_break_alphabetical(self):\n"
        "        self.assertEqual(word_freq('d c b a', 3), [('a', 1), ('b', 1), ('c', 1)])\n"
        "    def test_case_and_punctuation(self):\n"
        "        self.assertEqual(word_freq('Hello, hello! World.', 1), [('hello', 2)])\n"
        "    def test_k_larger_than_vocab(self):\n"
        "        self.assertEqual(word_freq('one two', 5), [('one', 1), ('two', 1)])\n"
    ),
    buggy=(
        BugVariant(
            id="no_tie_break",
            signature="[('d', 1), ('c', 1), ('b', 1)]",
            cause="ties are not broken alphabetically (insertion order used)",
            fix="sort by (-count, word) so ties resolve alphabetically",
            code=(
                "import re\n"
                "from collections import Counter\n\n"
                "def word_freq(text, k):\n"
                "    words = re.findall(r'[a-z0-9]+', text.lower())\n"
                "    counts = Counter(words)\n"
                "    ranked = sorted(counts.items(), key=lambda item: -item[1])\n"
                "    return ranked[:k]\n"
            ),
        ),
        BugVariant(
            id="no_punct_strip",
            signature="[('hello!', 1)]",
            cause="punctuation is not stripped from words",
            fix="extract words with a regex like [a-z0-9]+ after lowercasing",
            code=(
                "from collections import Counter\n\n"
                "def word_freq(text, k):\n"
                "    words = text.lower().split()\n"
                "    counts = Counter(words)\n"
                "    ranked = sorted(counts.items(), key=lambda item: (-item[1], item[0]))\n"
                "    return ranked[:k]\n"
            ),
        ),
        BugVariant(
            id="no_k_limit",
            signature="[('b', 3), ('a', 2), ('c', 1)]",
            cause="k is ignored: all distinct words are returned",
            fix="return only the first k entries of the ranking",
            code=(
                "import re\n"
                "from collections import Counter\n\n"
                "def word_freq(text, k):\n"
                "    words = re.findall(r'[a-z0-9]+', text.lower())\n"
                "    counts = Counter(words)\n"
                "    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))\n"
            ),
        ),
    ),
    base_p=0.30,
)


FLATTEN = Task(
    id="flatten",
    description=(
        "Write a function `flatten(nested)` that deeply flattens arbitrarily nested lists "
        "into a single list of non-list elements, preserving order. "
        "Example: flatten([1, [2, [3, [4]], 5]]) -> [1, 2, 3, 4, 5]; flatten([]) -> []."
    ),
    correct=(
        "def flatten(nested):\n"
        "    out = []\n"
        "    for item in nested:\n"
        "        if isinstance(item, list):\n"
        "            out.extend(flatten(item))\n"
        "        else:\n"
        "            out.append(item)\n"
        "    return out\n"
    ),
    tests=_tests(
        "from solution import flatten\n\n"
        "class TestFlatten(unittest.TestCase):\n"
        "    def test_deep(self):\n"
        "        self.assertEqual(flatten([1, [2, [3, [4]], 5]]), [1, 2, 3, 4, 5])\n"
        "    def test_empty(self):\n"
        "        self.assertEqual(flatten([]), [])\n"
        "    def test_already_flat(self):\n"
        "        self.assertEqual(flatten([1, 2, 3]), [1, 2, 3])\n"
    ),
    buggy=(
        BugVariant(
            id="one_level_only",
            signature="FAIL: test_deep",
            cause="only one level of nesting is flattened",
            fix="recurse into nested lists instead of a single extend",
            code=(
                "def flatten(nested):\n"
                "    out = []\n"
                "    for item in nested:\n"
                "        if isinstance(item, list):\n"
                "            out.extend(item)\n"
                "        else:\n"
                "            out.append(item)\n"
                "    return out\n"
            ),
        ),
        BugVariant(
            id="empty_raises",
            signature="ValueError: empty list not supported",
            cause="empty input raises instead of returning []",
            fix="no special case needed: an empty input naturally yields []",
            code=(
                "def flatten(nested):\n"
                "    if not nested:\n"
                "        raise ValueError('empty list not supported')\n"
                "    out = []\n"
                "    for item in nested:\n"
                "        if isinstance(item, list):\n"
                "            out.extend(flatten(item))\n"
                "        else:\n"
                "            out.append(item)\n"
                "    return out\n"
            ),
        ),
    ),
    base_p=0.35,
)


CHUNK_LIST = Task(
    id="chunk_list",
    description=(
        "Write a function `chunk_list(items, size)` that splits a list into consecutive "
        "chunks of length `size`; the final chunk may be shorter. "
        "chunk_list([], 3) -> []; chunk_list([1,2,3,4,5], 2) -> [[1,2],[3,4],[5]]. "
        "Assume size >= 1."
    ),
    correct=(
        "def chunk_list(items, size):\n"
        "    return [items[i:i + size] for i in range(0, len(items), size)]\n"
    ),
    tests=_tests(
        "from solution import chunk_list\n\n"
        "class TestChunkList(unittest.TestCase):\n"
        "    def test_empty(self):\n"
        "        self.assertEqual(chunk_list([], 3), [])\n"
        "    def test_remainder(self):\n"
        "        self.assertEqual(chunk_list([1, 2, 3, 4, 5], 2), [[1, 2], [3, 4], [5]])\n"
        "    def test_exact(self):\n"
        "        self.assertEqual(chunk_list([1, 2, 3, 4], 2), [[1, 2], [3, 4]])\n"
    ),
    buggy=(
        BugVariant(
            id="drops_remainder",
            signature="[[1, 2], [3, 4]] !=",
            cause="the final short chunk is dropped",
            fix="include the trailing slice even when it is shorter than size",
            code=(
                "def chunk_list(items, size):\n"
                "    return [items[i:i + size] for i in range(0, len(items) - size + 1, size)]\n"
            ),
        ),
        BugVariant(
            id="pads_last_chunk",
            signature="[5, 0]",
            cause="the final chunk is padded instead of left short",
            fix="do not pad: slicing already yields the shorter tail",
            code=(
                "def chunk_list(items, size):\n"
                "    out = []\n"
                "    for i in range(0, len(items), size):\n"
                "        chunk = list(items[i:i + size])\n"
                "        while len(chunk) < size:\n"
                "            chunk = chunk + [0]\n"
                "        out.append(chunk)\n"
                "    return out\n"
            ),
        ),
    ),
    base_p=0.40,
)


TASKS: tuple[Task, ...] = (
    SAFE_DIVIDE,
    IS_PALINDROME,
    PARSE_DURATION,
    MERGE_INTERVALS,
    FIB,
    WORD_FREQ,
    FLATTEN,
    CHUNK_LIST,
)

TASKS_BY_ID = {t.id: t for t in TASKS}
