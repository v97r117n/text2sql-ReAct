## dropout risk assessment
When analyzing dropout risk, join students with risk_assessments on student_id.
The risk_level column has values: 'low', 'medium', 'high', 'critical'.
The risk_score is a float from 0.0 to 1.0.
The contributing_factors column contains comma-separated factors like: poverty, distance, criminal_history, low_gpa, low_attendance.
Current status of a student is in students.current_status: 'enrolled', 'dropped_out', 'graduated', 'transferred'.

## income and financial analysis
Parent income is in parents.annual_income (in INR).
Family income bracket is in socioeconomic.family_income_bracket: 'below_poverty', 'low', 'middle', 'upper_middle', 'high'.
Join students → parents ON students.parent_id = parents.parent_id.
Join students → socioeconomic ON students.student_id = socioeconomic.student_id.
Also check: socioeconomic.receives_scholarship, socioeconomic.receives_free_meals.

## distance and transportation
Distance from school is in students.distance_from_school_km (in kilometers).
School location type is in school_info.location: 'urban', 'semi-urban', 'rural'.
Join students → school_info ON students.school_id = school_info.school_id.
Check socioeconomic.has_private_transport for transport access (0=No, 1=Yes).

## academic performance
Academic data is in the academics table: gpa (0-10), attendance_pct (0-100), failed_subjects (count), math_score, science_score, language_score, behavior_grade (A-F).
Join students → academics ON students.student_id = academics.student_id.
Filter by academics.academic_year for specific years (e.g., '2025-2026').

## parent criminal history
Criminal history flag is in parents.has_criminal_history (0=No, 1=Yes).
Join students → parents ON students.parent_id = parents.parent_id.
Combine with risk_assessments to see correlation with dropout risk.

## family structure
Family structure is in socioeconomic.lives_with: 'both_parents', 'single_parent', 'guardian', 'hostel'.
Parent marital status is in parents.marital_status: 'married', 'divorced', 'single', 'widowed'.
Number of siblings is in socioeconomic.number_of_siblings.
