from sqlalchemy import Boolean, Column, Integer, String, Enum, ForeignKey, DateTime, Float, Enum
from sqlalchemy.orm import relationship, backref
import enum
from app.db.base_class import Base
from app.enums.relationship_type_dating import RelationshipType

# class RelationshipType(enum.Enum):
#     FRIENDSHIP = 0
#     ROMANTIC = 1
#     LOVE = 2

# relationship_type_translations = {
#     RelationshipType.FRIENDSHIP: "Дружеские отношения",
#     RelationshipType.ROMANTIC: "Романтические отношения",
#     RelationshipType.LOVE: "Любовные отношения"
# }

class DatingProfile(Base):
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id", ondelete='CASCADE'))

  
    films = Column(String, nullable=True)
    book = Column(String, nullable=True)
    about = Column(String, nullable=True)
    education = Column(String, nullable=True)
    work = Column(String, nullable=True)
    relationship_type = Column(Enum(RelationshipType), nullable=True)  #Добавляем поле с типом отношений / обз пустым 
    

    # Relationshipss
    user = relationship("User", back_populates="dating_profile")
    # Relationship to fact, avatars, music, interes
    profile_facts = relationship("ProfileFacts", back_populates="dating_profile", cascade="all, delete-orphan")
    avatars = relationship("ProfileAvatar", back_populates="dating_profile", cascade="all, delete-orphan")
    profile_genre_music = relationship("ProfileGenreMusic", back_populates="dating_profile", cascade="all, delete-orphan")
    profile_interests = relationship("ProfileInterests", back_populates="dating_profile", primaryjoin="DatingProfile.id==ProfileInterests.dating_profile_id", cascade="all, delete-orphan" )
    # Relationship to likes
    sent_likes = relationship("ProfileLike", foreign_keys="[ProfileLike.liker_dating_profile_id]", back_populates="liker_profile")
    received_likes = relationship("ProfileLike", foreign_keys="[ProfileLike.liked_dating_profile_id]", back_populates="liked_profile")
    # Relationship to rating
    rating_user = relationship("RatingWeights", back_populates='user', foreign_keys='RatingWeights.user_id', cascade="all, delete-orphan")
    rating_profile = relationship("RatingWeights", back_populates='profile', foreign_keys='RatingWeights.profile_id', cascade="all, delete-orphan")
