import traceback
from app.database import SessionLocal
from app.models import Admin
from app.security import verify_password

db = SessionLocal()

username = input("Username : ").strip()
password = input("Password : ").strip()

admin = db.query(Admin).filter(Admin.username == username).first()
print("\n--- Résultat ---")
print("Admin trouvé :", admin)

if admin:
    print("Hash en base :", admin.password_hash)
    print("is_active :", admin.is_active)
    try:
        result = verify_password(password, admin.password_hash)
        print("Résultat verify_password :", result)
    except Exception:
        print("\n❌ EXCEPTION dans verify_password :")
        traceback.print_exc()
else:
    print("❌ Aucun admin avec ce username en base — vérifie que ta requête INSERT a bien été exécutée.")

db.close()