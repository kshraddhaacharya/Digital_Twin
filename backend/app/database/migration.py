import sqlite3
import os

def run_migrations(db_path: str = "patient_twin.db"):
    """
    Safely adds missing columns to existing SQLite tables without dropping tables
    or overwriting existing patient records.
    """
    if not os.path.exists(db_path):
        return

    con = sqlite3.connect(db_path)
    cur = con.cursor()

    def get_columns(table: str):
        try:
            return [info[1] for info in cur.execute(f"PRAGMA table_info({table})").fetchall()]
        except Exception:
            return []

    # 1. Migrations for patients table
    patient_cols = get_columns("patients")
    if patient_cols:
        if "height_cm" not in patient_cols:
            cur.execute("ALTER TABLE patients ADD COLUMN height_cm REAL")
        if "weight_kg" not in patient_cols:
            cur.execute("ALTER TABLE patients ADD COLUMN weight_kg REAL")
        if "profile_version" not in patient_cols:
            cur.execute("ALTER TABLE patients ADD COLUMN profile_version INTEGER NOT NULL DEFAULT 1")

    # 2. Migrations for measurements table
    measurement_cols = get_columns("measurements")
    if measurement_cols:
        if "context" not in measurement_cols:
            cur.execute("ALTER TABLE measurements ADD COLUMN context VARCHAR(32) NOT NULL DEFAULT 'resting'")
        if "data_quality" not in measurement_cols:
            cur.execute("ALTER TABLE measurements ADD COLUMN data_quality VARCHAR(32) NOT NULL DEFAULT 'valid'")

    # 3. Migrations for twin_states table
    twin_cols = get_columns("twin_states")
    if twin_cols:
        if "measurement_context" not in twin_cols:
            cur.execute("ALTER TABLE twin_states ADD COLUMN measurement_context VARCHAR(32) NOT NULL DEFAULT 'resting'")
        if "model_version" not in twin_cols:
            cur.execute("ALTER TABLE twin_states ADD COLUMN model_version VARCHAR(32) NOT NULL DEFAULT '1.0.0'")
        if "data_quality_status" not in twin_cols:
            cur.execute("ALTER TABLE twin_states ADD COLUMN data_quality_status VARCHAR(64) NOT NULL DEFAULT 'good'")
        if "attestation_status" not in twin_cols:
            cur.execute("ALTER TABLE twin_states ADD COLUMN attestation_status VARCHAR(32) NOT NULL DEFAULT 'PENDING'")
        if "previous_state_hash" not in twin_cols:
            cur.execute("ALTER TABLE twin_states ADD COLUMN previous_state_hash VARCHAR(64)")
        if "latest_forecast_time" not in twin_cols:
            cur.execute("ALTER TABLE twin_states ADD COLUMN latest_forecast_time TIMESTAMP")

    # 4. Migrations for users table
    user_cols = get_columns("users")
    if user_cols:
        if "profile_version" not in user_cols:
            cur.execute("ALTER TABLE users ADD COLUMN profile_version INTEGER NOT NULL DEFAULT 1")
        # Ensure default demo user exists for foreign keys
        demo_user = cur.execute("SELECT id FROM users WHERE id = 'USR-DEMO'").fetchone()
        if not demo_user:
            cur.execute("""
                INSERT INTO users (id, email, hashed_password, full_name, is_active, patient_id, profile_version)
                VALUES ('USR-DEMO', 'demo@patient.org', 'demo_hash', 'Alice M. Taylor (Demo)', 1, 'PT-DEMO-001', 1)
            """)

    con.commit()
    con.close()

if __name__ == "__main__":
    run_migrations("patient_twin.db")
    print("Migrations applied successfully to patient_twin.db")
