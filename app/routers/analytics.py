import math
from collections import defaultdict
from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.models.complaint import Complaint
from app.models.delivery_partner import DeliveryPartner
from app.models.order import Order, OrderStatus
from app.models.order_item import OrderItem
from app.models.restaurant import Restaurant
from app.models.tracking import Tracking

from app.security.dependencies import get_current_user
from app.services.demand_service import forecast_next_hours, _predict_many
from app.services.rating_service import rating_map


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)

WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


def admin_only(current_user: User = Depends(get_current_user)):

    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin only")

    return current_user


def _total(o: Order) -> float:
    return float(o.delivery_charge or 0) + float(o.items_total or 0)


def _local(dt):
    return dt.astimezone() if dt else None


def _local_date(o: Order):
    return o.created_at.astimezone().date() if o.created_at else None


def _hour_label(h: int) -> str:
    return f"{h % 12 or 12} {'AM' if h < 12 else 'PM'}"


def _week_start(d: date) -> date:
    return d - timedelta(days=d.weekday())


def _months_back(n: int):
    today = date.today()
    y, m = today.year, today.month
    out = []
    for _ in range(n):
        out.append((y, m))
        m -= 1
        if m == 0:
            m = 12
            y -= 1
    return out[::-1]


def _pearson(a, b):
    n = len(a)
    if n < 2:
        return None
    ma, mb = sum(a) / n, sum(b) / n
    num = sum((x - ma) * (y - mb) for x, y in zip(a, b))
    da = math.sqrt(sum((x - ma) ** 2 for x in a))
    db = math.sqrt(sum((y - mb) ** 2 for y in b))
    return round(num / (da * db), 2) if da and db else None


# Numbers and charts for the admin overview
@router.get("/summary")
def summary(
    db: Session = Depends(get_db),
    admin: User = Depends(admin_only)
):

    orders = db.query(Order).all()

    delivered = [o for o in orders if o.order_status == OrderStatus.delivered]
    cancelled = [o for o in orders if o.order_status == OrderStatus.cancelled]
    pending = [o for o in orders if o.order_status == OrderStatus.pending]
    active = [
        o for o in orders
        if o.order_status in (
            OrderStatus.assigned, OrderStatus.picked_up, OrderStatus.in_transit
        )
    ]

    revenue = sum(_total(o) for o in delivered)

    open_complaints = db.query(Complaint).filter(
        Complaint.status != "Resolved"
    ).count()

    by_status = {s.value: 0 for s in OrderStatus}
    for o in orders:
        by_status[o.order_status.value] += 1

    today = datetime.now().date()
    days = [today - timedelta(days=i) for i in range(13, -1, -1)]
    day_orders = defaultdict(int)
    day_revenue = defaultdict(float)

    for o in orders:
        d = _local_date(o)
        if d is None:
            continue
        day_orders[d] += 1
        if o.order_status == OrderStatus.delivered:
            day_revenue[d] += _total(o)

    daily = [
        {
            "date": f"{d.day} {d:%b}",
            "orders": day_orders[d],
            "revenue": round(day_revenue[d], 2),
        }
        for d in days
    ]

    restaurants = {r.id: r for r in db.query(Restaurant).all()}
    perf = defaultdict(lambda: {"orders": 0, "delivered": 0, "revenue": 0.0})

    for o in orders:
        if o.restaurant_id is None or o.order_status == OrderStatus.cancelled:
            continue
        p = perf[o.restaurant_id]
        p["orders"] += 1
        if o.order_status == OrderStatus.delivered:
            p["delivered"] += 1
            p["revenue"] += float(o.items_total or 0)

    rest_rows = sorted(
        [
            {
                "name": restaurants[rid].name,
                "city": restaurants[rid].city,
                "orders": v["orders"],
                "delivered": v["delivered"],
                "revenue": round(v["revenue"], 2),
            }
            for rid, v in perf.items() if rid in restaurants
        ],
        key=lambda r: -r["orders"]
    )

    item_rows = (
        db.query(OrderItem.item_name, func.sum(OrderItem.quantity))
        .join(Order, Order.id == OrderItem.order_id)
        .filter(Order.order_status != OrderStatus.cancelled)
        .group_by(OrderItem.item_name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(8)
        .all()
    )

    partners = []
    for p in db.query(DeliveryPartner).all():
        mine = [o for o in orders if o.delivery_partner_id == p.id]
        done = [o for o in mine if o.order_status == OrderStatus.delivered]
        kms = [float(o.distance_km) for o in done if o.distance_km is not None]

        partners.append({
            "id": p.id,
            "name": p.user.full_name if p.user else f"Partner {p.id}",
            "city": p.city,
            "vehicle": f"{p.vehicle_type} {p.vehicle_number}",
            "available": p.is_available,
            "delivered": len(done),
            "active": len([
                o for o in mine
                if o.order_status in (
                    OrderStatus.assigned, OrderStatus.picked_up, OrderStatus.in_transit
                )
            ]),
            "earnings": round(sum(float(o.delivery_charge or 0) for o in done), 2),
            "avg_km": round(sum(kms) / len(kms), 2) if kms else 0,
        })

    partners.sort(key=lambda p: -p["delivered"])

    return {
        "totals": {
            "orders": len(orders),
            "delivered": len(delivered),
            "cancelled": len(cancelled),
            "pending": len(pending),
            "active": len(active),
            "revenue": round(revenue, 2),
            "avg_order_value": round(revenue / len(delivered), 2) if delivered else 0,
            "open_complaints": open_complaints,
        },
        "by_status": by_status,
        "daily": daily,
        "restaurants": rest_rows[:8],
        "all_restaurants": rest_rows,
        "top_items": [{"name": n, "qty": int(q)} for n, q in item_rows],
        "partners": partners,
    }


# Demand forecast and popular dishes
@router.get("/demand")
def demand(
    db: Session = Depends(get_db),
    admin: User = Depends(admin_only)
):

    forecast = forecast_next_hours(24)

    top = sorted(forecast, key=lambda f: -f["expected"])[:3]
    peak_hours = [f["label"] for f in sorted(top, key=lambda f: forecast.index(f))]

    actual = [0] * 24
    for o in db.query(Order).filter(Order.order_status != OrderStatus.cancelled).all():
        if o.created_at:
            actual[o.created_at.astimezone().hour] += 1

    rows = (
        db.query(OrderItem.item_name, Restaurant.name, func.sum(OrderItem.quantity))
        .join(Order, Order.id == OrderItem.order_id)
        .join(Restaurant, Restaurant.id == Order.restaurant_id)
        .filter(Order.order_status != OrderStatus.cancelled)
        .group_by(OrderItem.item_name, Restaurant.name)
        .order_by(func.sum(OrderItem.quantity).desc())
        .limit(10)
        .all()
    )

    total_qty = sum(int(q) for _, _, q in rows) or 1

    items = [
        {
            "name": name,
            "restaurant": rest,
            "qty": int(q),
            "share": round(int(q) / total_qty * 100, 1),
        }
        for name, rest, q in rows
    ]

    return {
        "forecast": forecast,
        "peak_hours": peak_hours,
        "actual_by_hour": actual,
        "items": items,
    }


# All seven business analytics in one call
@router.get("/insights")
def insights(
    db: Session = Depends(get_db),
    admin: User = Depends(admin_only)
):

    orders = db.query(Order).all()
    placed = [o for o in orders if o.order_status != OrderStatus.cancelled]
    delivered = [o for o in orders if o.order_status == OrderStatus.delivered]
    cancelled = [o for o in orders if o.order_status == OrderStatus.cancelled]

    # when was each order assigned and delivered (from the tracking history)
    assigned_at, delivered_at, ever_assigned = {}, {}, set()
    rows = db.query(Tracking.order_id, Tracking.status, Tracking.created_at).all()

    for oid, st, ts in rows:
        if st == OrderStatus.assigned:
            ever_assigned.add(oid)
            if oid not in assigned_at or ts < assigned_at[oid]:
                assigned_at[oid] = ts
        elif st == OrderStatus.delivered:
            if oid not in delivered_at or ts < delivered_at[oid]:
                delivered_at[oid] = ts

    today = datetime.now().date()

    # ---------- 1. Daily, weekly and monthly revenue ----------
    def trend(keys, key_of, label_of):
        n = defaultdict(int)
        rev = defaultdict(float)
        for o in orders:
            d = _local_date(o)
            if d is None:
                continue
            k = key_of(d)
            if o.order_status != OrderStatus.cancelled:
                n[k] += 1
            if o.order_status == OrderStatus.delivered:
                rev[k] += _total(o)
        return [
            {"label": label_of(k), "orders": n[k], "revenue": round(rev[k], 2)}
            for k in keys
        ]

    daily_keys = [today - timedelta(days=i) for i in range(29, -1, -1)]
    week_keys = [_week_start(today) - timedelta(weeks=i) for i in range(11, -1, -1)]
    month_keys = _months_back(12)

    daily = trend(daily_keys, lambda d: d, lambda d: f"{d.day} {d:%b}")
    weekly = trend(week_keys, _week_start, lambda d: f"Wk {d.day} {d:%b}")
    monthly = trend(
        month_keys,
        lambda d: (d.year, d.month),
        lambda k: f"{date(k[0], k[1], 1):%b %Y}"
    )

    cur_week, prev_week = weekly[-1]["revenue"], weekly[-2]["revenue"]
    growth = round((cur_week - prev_week) / prev_week * 100) if prev_week else None

    revenue = {
        "daily": daily,
        "weekly": weekly,
        "monthly": monthly,
        "totals": {
            "today": daily[-1]["revenue"],
            "week": cur_week,
            "month": monthly[-1]["revenue"],
            "all_time": round(sum(_total(o) for o in delivered), 2),
            "week_growth_pct": growth,
        },
    }

    # ---------- 2. Customer retention ----------
    by_customer = defaultdict(list)
    for o in placed:
        if o.created_at:
            by_customer[o.customer_id].append(_local(o.created_at))
    for v in by_customer.values():
        v.sort()

    total_customers = len(by_customer)
    repeat_customers = sum(1 for v in by_customer.values() if len(v) >= 2)

    distribution = {"1 order": 0, "2 orders": 0, "3 orders": 0, "4+ orders": 0}
    for v in by_customer.values():
        n = len(v)
        key = "1 order" if n == 1 else "2 orders" if n == 2 else "3 orders" if n == 3 else "4+ orders"
        distribution[key] += 1

    months6 = _months_back(6)
    new_m, ret_m = defaultdict(int), defaultdict(int)

    for times in by_customer.values():
        first_key = (times[0].year, times[0].month)
        seen = set()
        for t in times:
            k = (t.year, t.month)
            if k in seen:
                continue
            seen.add(k)
            if k == first_key:
                new_m[k] += 1
            else:
                ret_m[k] += 1

    now = datetime.now().astimezone()
    eligible = kept = 0
    for times in by_customer.values():
        first = times[0]
        if now - first >= timedelta(days=30):
            eligible += 1
            if any(timedelta(0) < t - first <= timedelta(days=30) for t in times[1:]):
                kept += 1

    retention = {
        "customers": total_customers,
        "repeat_customers": repeat_customers,
        "repeat_rate": round(repeat_customers / total_customers * 100, 1) if total_customers else 0,
        "eligible_30d": eligible,
        "retention_30d": round(kept / eligible * 100, 1) if eligible else None,
        "distribution": distribution,
        "monthly": [
            {
                "label": f"{date(k[0], k[1], 1):%b %Y}",
                "new": new_m[k],
                "returning": ret_m[k],
            }
            for k in months6
        ],
    }

    # ---------- 3. Restaurant-wise revenue comparison ----------
    names = {r.id: r for r in db.query(Restaurant).all()}
    ratings = rating_map(db)
    agg = defaultdict(lambda: {"orders": 0, "delivered": 0, "cancelled": 0, "sales": 0.0})

    for o in orders:
        if o.restaurant_id is None:
            continue
        a = agg[o.restaurant_id]
        if o.order_status == OrderStatus.cancelled:
            a["cancelled"] += 1
        else:
            a["orders"] += 1
        if o.order_status == OrderStatus.delivered:
            a["delivered"] += 1
            a["sales"] += float(o.items_total or 0)

    restaurants = []
    for rid, a in agg.items():
        r = names.get(rid)
        if not r:
            continue
        total = a["orders"] + a["cancelled"]
        avg, cnt = ratings.get(rid, (None, 0))
        restaurants.append({
            "name": r.name,
            "city": r.city,
            "orders": a["orders"],
            "delivered": a["delivered"],
            "cancelled": a["cancelled"],
            "cancel_rate": round(a["cancelled"] / total * 100, 1) if total else 0,
            "sales": round(a["sales"], 2),
            "avg_order_value": round(a["sales"] / a["delivered"], 2) if a["delivered"] else 0,
            "rating": avg,
            "rating_count": cnt,
        })
    restaurants.sort(key=lambda x: -x["sales"])

    # ---------- 4. Peak ordering hours ----------
    by_hour = [0] * 24
    by_weekday = [0] * 7
    for o in placed:
        if o.created_at:
            t = _local(o.created_at)
            by_hour[t.hour] += 1
            by_weekday[t.weekday()] += 1

    top_hours = sorted(range(24), key=lambda h: -by_hour[h])[:3]
    peak_hours = {
        "by_hour": by_hour,
        "by_weekday": by_weekday,
        "weekday_labels": WEEKDAYS,
        "top": [_hour_label(h) for h in top_hours if by_hour[h] > 0],
    }

    # ---------- 5. Delivery partner performance ----------
    partners = []
    for p in db.query(DeliveryPartner).all():
        mine = [o for o in orders if o.delivery_partner_id == p.id]
        done = [o for o in mine if o.order_status == OrderStatus.delivered]
        canc = [o for o in mine if o.order_status == OrderStatus.cancelled]

        minutes, on_time, timed = [], 0, 0
        for o in done:
            a, d = assigned_at.get(o.id), delivered_at.get(o.id)
            if a and d:
                minutes.append((d - a).total_seconds() / 60)
            if d and o.created_at and o.eta_minutes:
                timed += 1
                if (d - o.created_at).total_seconds() / 60 <= o.eta_minutes + 10:
                    on_time += 1

        kms = [float(o.distance_km) for o in done if o.distance_km is not None]
        finished = len(done) + len(canc)

        partners.append({
            "name": p.user.full_name if p.user else f"Partner {p.id}",
            "city": p.city,
            "delivered": len(done),
            "cancelled": len(canc),
            "completion_rate": round(len(done) / finished * 100) if finished else None,
            "avg_delivery_min": round(sum(minutes) / len(minutes), 1) if minutes else None,
            "on_time_pct": round(on_time / timed * 100) if timed else None,
            "total_km": round(sum(kms), 1),
            "earnings": round(sum(float(o.delivery_charge or 0) for o in done), 2),
        })
    partners.sort(key=lambda x: -x["delivered"])

    # ---------- 6. Order cancellation rate ----------
    days14 = daily_keys[-14:]
    placed_d, canc_d = defaultdict(int), defaultdict(int)
    for o in orders:
        d = _local_date(o)
        if d is None:
            continue
        placed_d[d] += 1
        if o.order_status == OrderStatus.cancelled:
            canc_d[d] += 1

    before_assign = sum(1 for o in cancelled if o.id not in ever_assigned)

    cancellation = {
        "total_orders": len(orders),
        "cancelled": len(cancelled),
        "rate": round(len(cancelled) / len(orders) * 100, 1) if orders else 0,
        "before_assignment": before_assign,
        "after_assignment": len(cancelled) - before_assign,
        "daily": [
            {
                "label": f"{d.day} {d:%b}",
                "rate": round(canc_d[d] / placed_d[d] * 100, 1) if placed_d[d] else 0,
                "cancelled": canc_d[d],
            }
            for d in days14
        ],
    }

    # ---------- 7. Actual vs predicted demand ----------
    # the model gives expected orders per hour for a typical city, so both
    # curves are compared as a share of the day (the shape of demand)
    table = _predict_many([(h, d) for d in range(7) for h in range(24)])
    pred_hour = [sum(table[d * 24 + h] for d in range(7)) / 7 for h in range(24)]

    total_actual = sum(by_hour)
    pred_sum = sum(pred_hour) or 1.0

    actual_share = [round(v / total_actual * 100, 2) if total_actual else 0 for v in by_hour]
    pred_share = [round(v / pred_sum * 100, 2) for v in pred_hour]

    actual_day = defaultdict(int)
    for o in placed:
        d = _local_date(o)
        if d is not None:
            actual_day[d] += 1

    pred_day = [sum(table[d.weekday() * 24 + h] for h in range(24)) for d in days14]
    actual_14 = [actual_day[d] for d in days14]
    scale = (sum(actual_14) / sum(pred_day)) if sum(actual_14) and sum(pred_day) else 1.0
    pred_scaled = [round(v * scale, 1) for v in pred_day]

    demand_compare = {
        "hour_labels": [_hour_label(h) for h in range(24)],
        "actual_share": actual_share,
        "predicted_share": pred_share,
        "correlation": _pearson(actual_share, pred_share) if total_actual >= 5 else None,
        "orders_used": total_actual,
        "day_labels": [f"{d.day} {d:%b}" for d in days14],
        "actual_daily": actual_14,
        "predicted_daily": pred_scaled,
        "daily_mae": round(
            sum(abs(a - p) for a, p in zip(actual_14, pred_scaled)) / len(actual_14), 2
        ),
    }

    return {
        "revenue": revenue,
        "retention": retention,
        "restaurants": restaurants,
        "peak_hours": peak_hours,
        "partners": partners,
        "cancellation": cancellation,
        "demand_compare": demand_compare,
    }