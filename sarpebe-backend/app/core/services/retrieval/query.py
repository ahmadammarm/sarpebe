from app.utils.fase import fase_for_grade


def build_query(topic: str, grade_level: str, subject: str) -> str:
    """
    The text that gets embedded for the vector search. A bare topic ("Ekonomi") is ambiguous;
    adding the subject, grade and phase puts the query in the same space as the contextual
    header each chunk was embedded with: "IPS kelas 9 (Fase D): Ekonomi Indonesia".
    """
    fase = fase_for_grade(grade_level)
    grade = f"kelas {grade_level.strip()}" + (f" (Fase {fase.code})" if fase else "")
    return f"{subject.strip()} {grade}: {topic.strip()}"
