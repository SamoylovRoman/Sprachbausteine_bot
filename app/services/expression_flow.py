from app.db.models import Expression, Example, Answer, Category, Level
from app.db.session import SessionLocal
from sqlalchemy.orm import Session
from datetime import datetime

def save_expression(user_id: int, data: dict):
    session: Session = SessionLocal()

    expression = Expression(
        text=data["text"],
        explanation=data["explanation"],
        created_by=user_id,
        created_at=datetime.utcnow()
    )
    session.add(expression)
    session.flush()  # get expression.id

    example = Example(
        expression_id=expression.id,
        sentence=data["sentence"],
        created_by=user_id,
        created_at=datetime.utcnow()
    )
    session.add(example)
    session.flush()

    # Добавление правильного и неправильных вариантов
    correct_answer = Answer(
        example_id=example.id,
        answer_text=data["correct"],
        is_correct=True
    )
    session.add(correct_answer)

    incorrects = [s.strip() for s in data["incorrect"].split(",") if s.strip()]
    for wrong in incorrects:
        session.add(Answer(example_id=example.id, answer_text=wrong, is_correct=False))

    # Категории
    cat_names = [s.strip() for s in data["categories"].split(",")]
    for name in cat_names:
        category = session.query(Category).filter_by(name=name).first()
        if category:
            expression.categories.append(category)

    # Уровни
    lvl_names = [s.strip() for s in data["levels"].split(",")]
    for name in lvl_names:
        level = session.query(Level).filter_by(name=name).first()
        if level:
            expression.levels.append(level)

    session.commit()
    session.close()