from sqlalchemy import ForeignKey, Column, Integer, DateTime, Boolean, JSON, func, BigInteger, UniqueConstraint, \
    Index, String, Float

from src.postgres.base import Base


class TgUserQuestion(Base):
    __tablename__ = 'tg_user_question'

    id = Column(Integer, primary_key=True, autoincrement=True)

    user_id = Column(BigInteger, ForeignKey('tg_user.id', ondelete='CASCADE'), primary_key=True)
    question_id = Column(ForeignKey('question.id'), primary_key=True)

    status = Column(Boolean, default=False)
    start_timestamp = Column(DateTime, default=func.now())
    send_feedback_timestamp = Column(DateTime)
    is_liked = Column(Boolean)
    user_answer_json = Column(JSON)
    user_result_json = Column(JSON)

    current_result_status = Column(String, default='In queue')

    premium_queue = Column(Boolean, default=False, nullable=True)

    __table_args__ = (
        UniqueConstraint('user_id', 'question_id', name='uq_user_question'),
        Index('uq_tg_user_question_id', 'id', unique=True)
    )


class TgUserQuestionMetric(Base):
    __tablename__ = 'tg_user_question_metric'

    id = Column(Integer, primary_key=True, autoincrement=True)

    uq_id = Column(BigInteger, ForeignKey('tg_user_question.id', ondelete='CASCADE'))
    metric_id = Column(String)
    value = Column(Float)
    details = Column(String, nullable=True)
