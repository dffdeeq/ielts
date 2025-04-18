from sqlalchemy import Integer, Column, JSON, ForeignKey, BigInteger, DateTime, func, Text, String

from src.postgres.base import Base


class PollFeedback(Base):
    __tablename__ = 'poll_feedback'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('tg_user.id', ondelete='CASCADE'))
    feedback_json = Column(JSON)
    poll_type = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), default=func.now())


class TgUserReview(Base):
    __tablename__ = 'tg_user_review'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey('tg_user.id', ondelete='CASCADE'))

    rating = Column(Integer)
    text = Column(Text)
    created_at = Column(DateTime(timezone=True), default=func.now())
