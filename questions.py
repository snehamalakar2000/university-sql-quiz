"""The 5 quiz questions (20 points total), with hints: expected SQL + expected result.

Expected results were produced by running each hint SQL against seed.sql.
"""

QUESTIONS = [
    {
        "id": 1,
        "title": "Old private universities",
        "level": "Easy",
        "points": 4,
        "prompt": (
            "List the **private** universities founded **before 1850**. "
            "Show `name` and `founded`, oldest first."
        ),
        "sql": """SELECT name, founded
FROM universities
WHERE type = 'Private' AND founded < 1850
ORDER BY founded;""",
        "expected_columns": ["name", "founded"],
        "expected_rows": [
            ["Harvard University", 1636],
            ["Columbia University", 1754],
            ["NYU", 1831],
            ["Wake Forest University", 1834],
            ["Duke University", 1838],
            ["Boston University", 1839],
        ],
    },
    {
        "id": 2,
        "title": "Big states",
        "level": "Easy-Medium",
        "points": 4,
        "prompt": (
            "For states with **at least 3** universities, show `state`, the number of "
            "universities, and the total enrollment. Sort by total enrollment, largest first."
        ),
        "sql": """SELECT state, COUNT(*) AS num_universities, SUM(enrollment) AS total_enrollment
FROM universities
GROUP BY state
HAVING COUNT(*) >= 3
ORDER BY total_enrollment DESC;""",
        "expected_columns": ["state", "num_universities", "total_enrollment"],
        "expected_rows": [
            ["CA", 4, 156300],
            ["NY", 4, 153000],
            ["NC", 4, 95600],
            ["MA", 3, 73900],
        ],
    },
    {
        "id": 3,
        "title": "Hardest to get into",
        "level": "Medium",
        "points": 4,
        "prompt": (
            "Show the **5** universities with the lowest **2025** acceptance rate. "
            "Show `name` and the acceptance rate as a percentage rounded to 1 decimal, lowest first.\n\n"
            "Acceptance rate = admitted / applicants × 100."
        ),
        "sql": """SELECT u.name, ROUND(100.0 * a.admitted / a.applicants, 1) AS acceptance_rate
FROM admissions a
JOIN universities u ON a.university_id = u.id
WHERE a.year = 2025
ORDER BY acceptance_rate
LIMIT 5;""",
        "expected_columns": ["name", "acceptance_rate"],
        "expected_rows": [
            ["Harvard University", 3.6],
            ["Stanford University", 3.7],
            ["Columbia University", 3.9],
            ["MIT", 4.6],
            ["Duke University", 5.8],
        ],
    },
    {
        "id": 4,
        "title": "Program counts (CTE)",
        "level": "Easy CTE",
        "points": 4,
        "prompt": (
            "Using a **CTE**, count the programs at each university. "
            "Show `name` and the number of programs for universities with **3 or more** programs, "
            "sorted by name."
        ),
        "sql": """WITH program_counts AS (
    SELECT university_id, COUNT(*) AS num_programs
    FROM programs
    GROUP BY university_id
)
SELECT u.name, pc.num_programs
FROM program_counts pc
JOIN universities u ON u.id = pc.university_id
WHERE pc.num_programs >= 3
ORDER BY u.name;""",
        "expected_columns": ["name", "num_programs"],
        "expected_rows": [
            ["Duke University", 3],
            ["Stanford University", 3],
        ],
    },
    {
        "id": 5,
        "title": "Fastest-growing applications (CTE)",
        "level": "Medium CTE",
        "points": 4,
        "prompt": (
            "Using a **CTE**, find the **3** universities whose number of applicants grew the most "
            "(in %) from **2024 to 2025**. Show `name`, 2024 applicants, 2025 applicants, and the "
            "% change rounded to 1 decimal, largest growth first."
        ),
        "sql": """WITH y24 AS (
    SELECT university_id, applicants FROM admissions WHERE year = 2024
),
y25 AS (
    SELECT university_id, applicants FROM admissions WHERE year = 2025
)
SELECT u.name,
       y24.applicants AS apps_2024,
       y25.applicants AS apps_2025,
       ROUND(100.0 * (y25.applicants - y24.applicants) / y24.applicants, 1) AS pct_change
FROM y24
JOIN y25 ON y24.university_id = y25.university_id
JOIN universities u ON u.id = y24.university_id
ORDER BY pct_change DESC
LIMIT 3;""",
        "expected_columns": ["name", "apps_2024", "apps_2025", "pct_change"],
        "expected_rows": [
            ["Georgia Tech", 50000, 55000, 10.0],
            ["UT Austin", 66000, 72000, 9.1],
            ["Wake Forest University", 17000, 18000, 5.9],
        ],
    },
]

TOTAL_POINTS = sum(q["points"] for q in QUESTIONS)
assert TOTAL_POINTS == 20, f"Points must sum to 20, got {TOTAL_POINTS}"
