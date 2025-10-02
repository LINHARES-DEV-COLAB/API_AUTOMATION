from datetime import datetime
from APP.extensions import db 

class Sector(db.Model):
    __tablename__ = "sectors"
    id   = db.Column(db.String(50), primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(80), nullable=False, unique=True)

class Automation(db.Model):
    __tablename__ = "automations"
    id        = db.Column(db.String(80), primary_key=True)
    name      = db.Column(db.String(160), nullable=False)
    sector_id = db.Column(db.String(50), db.ForeignKey("sectors.id"), nullable=False)
    description = db.Column(db.Text)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)

class AutomationInput(db.Model):
    __tablename__ = "automation_inputs"
    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    automation_id = db.Column(db.String(80), db.ForeignKey("automations.id"), nullable=False)
    key           = db.Column(db.String(80), nullable=False)
    label         = db.Column(db.String(160), nullable=False)
    type          = db.Column(db.String(20), nullable=False)  # text|number|textarea|json
    required      = db.Column(db.Boolean, default=False, nullable=False)
    placeholder   = db.Column(db.String(255))

class AutomationTag(db.Model):
    __tablename__ = "automation_tags"
    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    automation_id = db.Column(db.String(80), db.ForeignKey("automations.id"), nullable=False)
    tag           = db.Column(db.String(60), nullable=False)

class Run(db.Model):
    __tablename__ = "runs"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    automation_id = db.Column(db.String(80), nullable=False)
    status = db.Column(db.String(20), default="running")
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime)
    output = db.Column(db.Text)    

def sector_to_dict(s: Sector):
    return {"id": s.id, "name": s.name, "slug": s.slug}

def automation_input_to_dict(i: AutomationInput):
    return {
        "key": i.key, "label": i.label, "type": i.type,
        "required": i.required, "placeholder": i.placeholder,
    }

def automation_to_dict(a: Automation):
    # se tiver relationships configuradas, inclua aqui (inputs, tags)
    return {
        "id": a.id,
        "name": a.name,
        "sectorId": a.sector_id,
        "description": a.description,
        "inputs": [],  # preencha se já tiver relationship
        "tags":   [],
    }

