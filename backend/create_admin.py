import getpass
from app.database import SessionLocal
from app.models import Admin
from app.security import hash_password

db = SessionLocal()

username = input("Nom d'utilisateur admin : ").strip()
email = input("Email (optionnel, Entrée pour passer) : ").strip() or None
password = getpass.getpass("Mot de passe : ")
password_confirm = getpass.getpass("Confirme le mot de passe : ")

if password != password_confirm:
    print("❌ Les mots de passe ne correspondent pas.")
    exit(1)

existing = db.query(Admin).filter(Admin.username == username).first()
if existing:
    print("❌ Ce nom d'utilisateur existe déjà.")
    exit(1)

admin = Admin(
    username=username,
    email=email,
    password_hash=hash_password(password),
    is_active=True,
)
db.add(admin)
db.commit()
print(f"✅ Admin '{username}' créé (id={admin.id})")