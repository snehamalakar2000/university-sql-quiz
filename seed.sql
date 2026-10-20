-- University SQL Quiz: schema + seed data
-- Note: tuition, enrollment and admissions values are illustrative, not official figures.

DROP TABLE IF EXISTS admissions;
DROP TABLE IF EXISTS programs;
DROP TABLE IF EXISTS universities;

CREATE TABLE universities (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    state       CHAR(2) NOT NULL,
    type        TEXT NOT NULL CHECK (type IN ('Public', 'Private')),
    founded     INT NOT NULL,
    enrollment  INT NOT NULL
);

CREATE TABLE programs (
    id              SERIAL PRIMARY KEY,
    university_id   INT NOT NULL REFERENCES universities(id),
    program_name    TEXT NOT NULL,
    degree          TEXT NOT NULL,
    annual_tuition  INT NOT NULL
);

CREATE TABLE admissions (
    id              SERIAL PRIMARY KEY,
    university_id   INT NOT NULL REFERENCES universities(id),
    year            INT NOT NULL,
    applicants      INT NOT NULL,
    admitted        INT NOT NULL
);

INSERT INTO universities (name, state, type, founded, enrollment) VALUES
('Duke University',          'NC', 'Private', 1838, 17600),  -- 1
('UNC Chapel Hill',          'NC', 'Public',  1789, 32000),  -- 2
('NC State University',      'NC', 'Public',  1887, 37000),  -- 3
('Wake Forest University',   'NC', 'Private', 1834,  9000),  -- 4
('Stanford University',      'CA', 'Private', 1885, 18300),  -- 5
('UC Berkeley',              'CA', 'Public',  1868, 45000),  -- 6
('UCLA',                     'CA', 'Public',  1919, 46000),  -- 7
('USC',                      'CA', 'Private', 1880, 47000),  -- 8
('MIT',                      'MA', 'Private', 1861, 11900),  -- 9
('Harvard University',       'MA', 'Private', 1636, 25000),  -- 10
('Boston University',        'MA', 'Private', 1839, 37000),  -- 11
('University of Michigan',   'MI', 'Public',  1817, 52000),  -- 12
('Columbia University',      'NY', 'Private', 1754, 36000),  -- 13
('NYU',                      'NY', 'Private', 1831, 59000),  -- 14
('Cornell University',       'NY', 'Private', 1865, 26000),  -- 15
('University at Buffalo',    'NY', 'Public',  1846, 32000),  -- 16
('Georgia Tech',             'GA', 'Public',  1885, 45000),  -- 17
('UT Austin',                'TX', 'Public',  1883, 53000);  -- 18

INSERT INTO programs (university_id, program_name, degree, annual_tuition) VALUES
(1,  'Interdisciplinary Data Science', 'MS',  62000),
(1,  'Statistical Science',            'MS',  60000),
(1,  'Business Administration',        'MBA', 78000),
(2,  'Data Science',                   'MS',  30000),
(2,  'Business Administration',        'MBA', 60000),
(3,  'Analytics',                      'MS',  25000),
(3,  'Computer Science',               'MS',  28000),
(4,  'Business Analytics',             'MS',  52000),
(5,  'Statistics',                     'MS',  65000),
(5,  'Computer Science',               'MS',  66000),
(5,  'Business Administration',        'MBA', 82000),
(6,  'Information and Data Science',   'MS',  55000),
(6,  'Business Administration',        'MBA', 70000),
(7,  'Business Analytics',             'MS',  68000),
(7,  'Statistics',                     'MS',  35000),
(8,  'Applied Data Science',           'MS',  62000),
(8,  'Business Analytics',             'MS',  60000),
(9,  'Business Analytics',             'MS',  88000),
(9,  'Computer Science',               'MS',  61000),
(10, 'Data Science',                   'MS',  58000),
(10, 'Business Administration',        'MBA', 76000),
(11, 'Statistical Practice',           'MS',  64000),
(12, 'Data Science',                   'MS',  40000),
(12, 'Business Administration',        'MBA', 72000),
(13, 'Data Science',                   'MS',  70000),
(13, 'Business Analytics',             'MS',  74000),
(14, 'Data Science',                   'MS',  66000),
(14, 'Business Administration',        'MBA', 80000),
(15, 'Data Science',                   'MS',  67000),
(16, 'Data Science',                   'MS',  24000),
(17, 'Analytics',                      'MS',  35000),
(17, 'Computer Science',               'MS',  32000),
(18, 'Data Science',                   'MS',  30000),
(18, 'Business Administration',        'MBA', 58000);

INSERT INTO admissions (university_id, year, applicants, admitted) VALUES
(1,  2024,  49000,  2950), (1,  2025,  50000,  2900),
(2,  2024,  64000, 11200), (2,  2025,  65000, 10900),
(3,  2024,  38000, 16100), (3,  2025,  40000, 16000),
(4,  2024,  17000,  3600), (4,  2025,  18000,  3500),
(5,  2024,  56000,  2150), (5,  2025,  57000,  2100),
(6,  2024, 125000, 14600), (6,  2025, 125000, 14400),
(7,  2024, 145000, 12900), (7,  2025, 150000, 12800),
(8,  2024,  80000,  7900), (8,  2025,  82000,  7800),
(9,  2024,  27000,  1300), (9,  2025,  28000,  1300),
(10, 2024,  56000,  1950), (10, 2025,  54000,  1950),
(11, 2024,  80000,  8800), (11, 2025,  81000,  8700),
(12, 2024,  96000, 17500), (12, 2025,  98000, 17000),
(13, 2024,  60000,  2300), (13, 2025,  59000,  2300),
(14, 2024, 118000, 10100), (14, 2025, 120000,  9900),
(15, 2024,  65000,  5200), (15, 2025,  67000,  5100),
(16, 2024,  33000, 22000), (16, 2025,  34000, 22500),
(17, 2024,  50000,  8500), (17, 2025,  55000,  8400),
(18, 2024,  66000, 19000), (18, 2025,  72000, 19500);
