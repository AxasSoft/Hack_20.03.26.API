from datetime import datetime

from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float, Table
from sqlalchemy.orm import relationship

from app.db.base_class import Base
from app.schemas.user import Gender

def get_full_name(user):
    return (" ".join([item for item in [user.first_name, user.patronymic, user.last_name] if item is not None])).strip()


class User(Base):
    id = Column(Integer, primary_key=True, index=True)
    created = Column(DateTime, nullable=True, default=datetime.utcnow, index=True)
    deleted = Column(DateTime(), nullable=True, index=True)

    first_name = Column(String, index=True)
    patronymic = Column(String, index=True)
    last_name = Column(String, index=True)
    email = Column(String, unique=True, index=True, nullable=True)
    tel = Column(String, unique=True, index=True, nullable=True)
    shadow_tel = Column(String, unique=True, index=True, nullable=True)
    birthtime = Column(DateTime, nullable=True)
    shadow_email = Column(String, nullable=True)
    hashed_password = Column(String, nullable=True)
    is_active = Column(Boolean(), default=True, index=True)
    is_superuser = Column(Boolean(), default=False, index=True)
    avatar = Column(String, nullable=True)
    profile_cover = Column(String, nullable=True)
    gender = Column(Enum(Gender), nullable=True, index=True)
    last_visited = Column(DateTime(), nullable=True, default=None)
    location = Column(String(), nullable=True, default=None)
    tg = Column(String, nullable=True)
    is_servicer = Column(Boolean, nullable=True, default=False)
    show_tel = Column(Boolean, nullable=True, server_default='true')
    is_business = Column(Boolean, nullable=False, server_default='false')
    in_blacklist = Column(Boolean, nullable=False, server_default='false')
    in_whitelist = Column(Boolean, nullable=False, server_default='false')
    region = Column(String, nullable=True, default=None)
    site = Column(String, nullable=True, default=None)
    experience = Column(String, nullable=True, default=None)
    company_info = Column(String, nullable=True, default=None)
    status = Column(String, nullable=True, default=None)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)
    country = Column(String, nullable=True, default=None)
    is_compatriot = Column(Boolean, nullable=True)
    is_dating_profile = Column(Boolean, nullable=False, server_default='false', default=False)
    # dating_profile_id = Column(Integer(), ForeignKey('datingprofile.id'), nullable=True)

    is_editor = Column(Boolean, nullable=False, server_default='false')
    is_support = Column(Boolean, nullable=False, server_default='false')
    hidden_geo = Column(Boolean, nullable=False, server_default='false')

    category_id = Column(Integer(), ForeignKey('category.id'), nullable=True)

    rating = Column(Integer, nullable=False, default=0, server_default='0')
    count_feedback_order = Column(Integer(), nullable=False, default=0, server_default='0')
    created_orders_count = Column(Integer, nullable=False, default=0)
    completed_orders_count = Column(Integer, nullable=False, default=0)
    my_offers_count = Column(Integer, nullable=True, default=0, server_default='0')
    subscriptions_count = Column(Integer, nullable=False, server_default='0')
    subscribers_count = Column(Integer, nullable=False, server_default='0')

    category = relationship('Category', back_populates="users")
    devices = relationship("Device", cascade="all, delete-orphan", back_populates="user", lazy="dynamic")
    stories = relationship("Story", cascade="all, delete-orphan", back_populates="user", lazy="dynamic")
    stories_attachments = relationship("StoryAttachment", cascade="all, delete-orphan", back_populates="user")
    views = relationship("View", cascade="all, delete-orphan", back_populates="user")
    hugs = relationship("Hug", cascade="all, delete-orphan", back_populates="user")
    favorite_stories = relationship("FavoriteStory", cascade="all, delete-orphan", back_populates="user")
    comments = relationship("Comment", cascade="all, delete-orphan", back_populates="user", lazy='dynamic')
    notifications = relationship('Notification', back_populates='user', passive_deletes=True, cascade="all, delete-orphan")

    subject_user_reports = relationship('UserReport', cascade="all, delete-orphan", back_populates="subject",
                                        lazy="dynamic", foreign_keys='UserReport.subject_id')
    object_user_reports = relationship('UserReport', cascade="all, delete-orphan", back_populates="object_",
                                       lazy="dynamic", foreign_keys='UserReport.object_id')
    subject_user_blocks = relationship('UserBlock', cascade="all, delete-orphan", back_populates="subject",
                                       lazy="dynamic", foreign_keys='UserBlock.subject_id')
    object_user_blocks = relationship('UserBlock', cascade="all, delete-orphan", back_populates="object_",
                                      lazy="dynamic", foreign_keys='UserBlock.object_id')
    subject_story_reports = relationship('StoryReport', cascade="all, delete-orphan", back_populates="subject",
                                         lazy="dynamic")
    story_hidings = relationship('StoryHiding', cascade="all, delete-orphan", back_populates="user", lazy="dynamic")
    orders = relationship('Order', cascade="all, delete-orphan", back_populates="user", lazy="dynamic")
    offers = relationship('Offer', cascade="all, delete-orphan", back_populates="user",)

    subject_feedbacks = relationship('Feedback', cascade="all, delete-orphan", back_populates="subject",
                                         foreign_keys='Feedback.subject_id')
    object_feedbacks = relationship('Feedback', cascade="all, delete-orphan", back_populates="object_",
                                    foreign_keys='Feedback.object_id')

    subject_subscriptions = relationship('Subscription', cascade="all, delete-orphan", back_populates="subject",
                                         foreign_keys='Subscription.subject_id', lazy='dynamic')
    object_subscriptions = relationship('Subscription', cascade="all, delete-orphan", back_populates="object_",
                                        lazy="joined", foreign_keys='Subscription.object_id')
    infos = relationship("Info", back_populates="user")
    events = relationship("Event", cascade="all, delete-orphan", back_populates="user", lazy='dynamic')
    event_members = relationship("EventMember", cascade="all, delete-orphan", back_populates="user")
    favorite_orders = relationship("FavoriteOrder", cascade="all, delete-orphan", back_populates="user")
    user_achievements = relationship("UserAchievement", cascade="all, delete-orphan", back_populates="user")
    event_feedbacks = relationship('EventFeedback', cascade="all, delete-orphan", back_populates="user")
    user_interests = relationship("UserInterest", cascade="all, delete-orphan", back_populates="user", lazy='joined')

    creator_feedback = relationship("FeedbackOrder", cascade="all, delete-orphan", back_populates="creator", 
                                    foreign_keys='FeedbackOrder.creator_id', lazy='joined')
    owner_order_feedback = relationship("FeedbackOrder", cascade="all, delete-orphan", back_populates="owner_order", 
                                    foreign_keys='FeedbackOrder.owner_order_id', lazy='joined')
    dating_profile = relationship("DatingProfile", back_populates="user", uselist=False)

    views_order = relationship('OrderView', back_populates='user', foreign_keys='OrderView.user_id')

    member = relationship('Member', back_populates='user', foreign_keys='Member.user_id', cascade="all, delete-orphan")