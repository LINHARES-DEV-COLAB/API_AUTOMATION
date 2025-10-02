# APP/Services/catalog.py
from APP.Models.models import Automation, Sector, automation_to_dict, sector_to_dict

def list_sectors():
    return [sector_to_dict(s) for s in Sector.query.order_by(Sector.name).all()]

def list_automations(sector_id=None):
    q = Automation.query
    if sector_id:
        q = q.filter_by(sector_id=sector_id)
    return [automation_to_dict(a) for a in q.order_by(Automation.name).all()]

def get_automation(automation_id: str) -> dict | None:
    # busca UMA automação pelo id
    a = Automation.query.get(automation_id)
    return automation_to_dict(a) if a else None