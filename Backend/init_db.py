from app import app, db

def init_database():
    with app.app_context():
        # Create all tables
        db.create_all()
        print("✅ Database tables created successfully!")
        print("📋 Created tables:")
        print("   - User (id, username, email, password)")
        print("   - UserQuery (id, user_id, query)")

if __name__ == "__main__":
    init_database()
