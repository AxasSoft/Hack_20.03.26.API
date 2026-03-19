
from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    login,
    users,
    hashtag,
    story_attachment,
    story,
    user_report,
    story_report,
    comment,
    page,
    chat,
    verification_code,
    category,
    info,
    subcategory,
    interest_user,
    order,
    promo_order,
    offer,
    # feedback,
    white_tel,
    black_tel,
    service_info,
    counter,
    event,
    event_feedback,
    adv,
    adv_slide,
    achievement,
    event_category,
    # music,
    # movie,
    # book,
    interest_dating,
    sub_interest,
    genre_music_dating,
    sub_genre_music,
    facts_dating,
    sub_facts,
    dating_profile,
    feedback_order,
    test,
    excursion_category,
    excursion,
    excursion_review,
    excursion_group,
    restaurant,
    restaurant_review,
    transfer,
    bookings,
    snowmobile_booking,
    hotel,
    audio_guide,
    short_story,
    gpt,
)

# from otter_mini.endpoints import router as chat_router

api_router = APIRouter()
api_router.include_router(login.router, tags=["Вход"])
api_router.include_router(user_report.router, prefix="")
api_router.include_router(users.router, prefix="")
api_router.include_router(hashtag.router, prefix="")
api_router.include_router(story_report.router, prefix="")
api_router.include_router(story_attachment.router, prefix="")
api_router.include_router(story.router, prefix="")
api_router.include_router(comment.router, prefix="")
api_router.include_router(chat.router, prefix="")
api_router.include_router(verification_code.router, prefix="")
api_router.include_router(category.router, prefix="")
api_router.include_router(info.router, prefix="")
api_router.include_router(subcategory.router, prefix="")
api_router.include_router(order.router, prefix="")
api_router.include_router(feedback_order.router, prefix="")
api_router.include_router(promo_order.router, prefix="")
api_router.include_router(offer.router, prefix="")
# api_router.include_router(feedback.router, prefix="")
api_router.include_router(white_tel.router, prefix="")
api_router.include_router(black_tel.router, prefix="")
api_router.include_router(service_info.router, prefix="")
api_router.include_router(counter.router, prefix="")
api_router.include_router(event.router, prefix="")
api_router.include_router(interest_user.router, prefix="")
api_router.include_router(event_feedback.router, prefix="")
api_router.include_router(adv.router, prefix="")
api_router.include_router(adv_slide.router, prefix="")
api_router.include_router(page.router, prefix="")
api_router.include_router(achievement.router, prefix="")
api_router.include_router(event_category.router, prefix="")
# api_router.include_router(music.router, prefix="")
# api_router.include_router(movie.router, prefix="")
# api_router.include_router(book.router, prefix="")
api_router.include_router(sub_interest.router, prefix="")
api_router.include_router(interest_dating.router, prefix="")
api_router.include_router(facts_dating.router, prefix="")
api_router.include_router(sub_facts.router, prefix="")
api_router.include_router(genre_music_dating.router, prefix="")
api_router.include_router(sub_genre_music.router, prefix="")
api_router.include_router(dating_profile.router, prefix="")
# api_router.include_router(chat_router)
api_router.include_router(test.router)
api_router.include_router(excursion_category.router)
api_router.include_router(excursion.router)
api_router.include_router(excursion_review.router)
api_router.include_router(excursion_group.router)
api_router.include_router(restaurant.router)
api_router.include_router(restaurant_review.router)
api_router.include_router(transfer.router)
api_router.include_router(bookings.router)
api_router.include_router(snowmobile_booking.router)
api_router.include_router(hotel.router)
api_router.include_router(audio_guide.router)
api_router.include_router(short_story.router)
api_router.include_router(gpt.router)