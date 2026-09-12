from app.database import SessionLocal
from app.models import Site, Backbone

db = SessionLocal()

site_names = ["Site 1", "Site 2", "Site 3"]
for name in site_names:
    exists = db.query(Site).filter(Site.name == name).first()
    if not exists:
        db.add(Site(name=name))
        print(f"Créé : {name}")
    else:
        print(f"Déjà présent : {name}")

if not db.query(Backbone).filter(Backbone.name == "Backbone").first():
    db.add(Backbone(name="Backbone"))
    print("Créé : Backbone")
else:
    print("Déjà présent : Backbone")

db.commit()
db.close()