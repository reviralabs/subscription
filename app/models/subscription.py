from sqlalchemy import Column, String, Integer, DateTime
from app.db.database import Base


class Subscription(Base):
    __tablename__ = "subscriptions"

    user_id = Column(String, primary_key=True, index=True)
    subscription_id = Column(String)
    plan = Column(String)
    subscription_status = Column(String)
    monthly_character_limit = Column(Integer)
    renews_at = Column(DateTime)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
