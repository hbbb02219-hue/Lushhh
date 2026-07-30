from datetime import datetime
from typing import Optional

coupledb: dict[int, dict] = {}


def _init_chat(cid: int) -> None:
    """Chat ka data structure ready karo agar exist nahi karta"""
    if cid not in coupledb:
        coupledb[cid] = {
            "couple": {},      # date -> couple dict
            "img": "",         # latest couple ki image
            "history": [],     # sabhi couples ka record (chronological)
        }


async def _get_lovers(cid: int) -> dict:
    """Is chat ke saare couples (date-wise) return karo 💌"""
    chat_data = coupledb.get(cid, {})
    return chat_data.get("couple", {})


async def get_image(cid: int) -> str:
    """Latest couple ki image URL/file_id fetch karo 🖼️"""
    chat_data = coupledb.get(cid, {})
    return chat_data.get("img", "")


async def get_couple(cid: int, date: str) -> dict | bool:
    """Kisi specific date ka couple nikaalo, warna False 🔍"""
    lovers = await _get_lovers(cid)
    return lovers.get(date, False)


async def save_couple(cid: int, date: str, couple: dict, img: str) -> None:
    """Aaj ka couple save karo, saath hi history bhi maintain karo 💘"""
    _init_chat(cid)
    coupledb[cid]["couple"][date] = couple
    coupledb[cid]["img"] = img
    coupledb[cid]["history"].append({
        "date": date,
        "couple": couple,
        "saved_at": datetime.now().isoformat(timespec="seconds"),
    })


async def get_couple_history(cid: int, limit: int = 10) -> list[dict]:
    """Is chat ke last N couples ki history do (most recent last) 📜"""
    chat_data = coupledb.get(cid, {})
    return chat_data.get("history", [])[-limit:]


async def get_couple_count(cid: int) -> int:
    """Ab tak total kitne couples bane is chat mein — bragging rights ke liye 🏆"""
    return len(coupledb.get(cid, {}).get("couple", {}))