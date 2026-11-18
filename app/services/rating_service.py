from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.review import Review


def rating_map(db: Session) -> dict:
    """restaurant_id -> (average rating, number of reviews)"""

    rows = db.query(
        Review.restaurant_id,
        func.avg(Review.rating),
        func.count(Review.id)
    ).group_by(Review.restaurant_id).all()

    return {rid: (round(float(avg), 1), int(cnt)) for rid, avg, cnt in rows}


def attach_ratings(db: Session, restaurants: list) -> list:
    """Put rating and rating_count on each restaurant object."""

    ratings = rating_map(db)

    for r in restaurants:
        avg, cnt = ratings.get(r.id, (None, 0))
        r.rating = avg
        r.rating_count = cnt

    return restaurants