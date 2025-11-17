"""
Seed JEE syllabus data into the database
Includes topics from Physics, Chemistry, and Mathematics
"""

import sqlite3
from pathlib import Path
import json
import sys


def get_db_path():
    """Get the database file path"""
    project_root = Path(__file__).parent.parent.parent
    return project_root / "mindmentor.db"


# JEE Syllabus Data
JEE_TOPICS = [
    # PHYSICS
    {"subject": "Physics", "chapter": "Mechanics", "topic": "Kinematics", "weight": 1.5, "difficulty": "Medium"},
    {"subject": "Physics", "chapter": "Mechanics", "topic": "Laws of Motion", "weight": 1.5, "difficulty": "Medium"},
    {"subject": "Physics", "chapter": "Mechanics", "topic": "Work, Energy and Power", "weight": 1.2, "difficulty": "Medium"},
    {"subject": "Physics", "chapter": "Mechanics", "topic": "Rotational Motion", "weight": 1.3, "difficulty": "Hard"},
    {"subject": "Physics", "chapter": "Mechanics", "topic": "Gravitation", "weight": 1.0, "difficulty": "Medium"},
    {"subject": "Physics", "chapter": "Properties of Matter", "topic": "Elasticity", "weight": 0.8, "difficulty": "Easy"},
    {"subject": "Physics", "chapter": "Properties of Matter", "topic": "Fluid Mechanics", "weight": 1.2, "difficulty": "Medium"},
    {"subject": "Physics", "chapter": "Thermodynamics", "topic": "Kinetic Theory of Gases", "weight": 1.0, "difficulty": "Medium"},
    {"subject": "Physics", "chapter": "Thermodynamics", "topic": "Laws of Thermodynamics", "weight": 1.2, "difficulty": "Hard"},
    {"subject": "Physics", "chapter": "Electrostatics", "topic": "Electric Charges and Fields", "weight": 1.3, "difficulty": "Medium"},
    {"subject": "Physics", "chapter": "Electrostatics", "topic": "Capacitance", "weight": 1.0, "difficulty": "Medium"},
    {"subject": "Physics", "chapter": "Current Electricity", "topic": "Ohm's Law and Resistance", "weight": 1.1, "difficulty": "Easy"},
    {"subject": "Physics", "chapter": "Current Electricity", "topic": "Kirchhoff's Laws", "weight": 1.2, "difficulty": "Medium"},
    {"subject": "Physics", "chapter": "Magnetism", "topic": "Magnetic Effects of Current", "weight": 1.2, "difficulty": "Medium"},
    {"subject": "Physics", "chapter": "Magnetism", "topic": "Electromagnetic Induction", "weight": 1.4, "difficulty": "Hard"},
    {"subject": "Physics", "chapter": "Optics", "topic": "Ray Optics", "weight": 1.1, "difficulty": "Medium"},
    {"subject": "Physics", "chapter": "Optics", "topic": "Wave Optics", "weight": 1.0, "difficulty": "Hard"},
    {"subject": "Physics", "chapter": "Modern Physics", "topic": "Dual Nature of Matter", "weight": 1.0, "difficulty": "Medium"},
    {"subject": "Physics", "chapter": "Modern Physics", "topic": "Atoms and Nuclei", "weight": 1.1, "difficulty": "Medium"},
    {"subject": "Physics", "chapter": "Modern Physics", "topic": "Semiconductor Devices", "weight": 0.9, "difficulty": "Easy"},
    
    # CHEMISTRY
    {"subject": "Chemistry", "chapter": "Physical Chemistry", "topic": "Atomic Structure", "weight": 1.2, "difficulty": "Medium"},
    {"subject": "Chemistry", "chapter": "Physical Chemistry", "topic": "Chemical Bonding", "weight": 1.3, "difficulty": "Medium"},
    {"subject": "Chemistry", "chapter": "Physical Chemistry", "topic": "Gaseous State", "weight": 0.9, "difficulty": "Easy"},
    {"subject": "Chemistry", "chapter": "Physical Chemistry", "topic": "Thermodynamics", "weight": 1.4, "difficulty": "Hard"},
    {"subject": "Chemistry", "chapter": "Physical Chemistry", "topic": "Chemical Equilibrium", "weight": 1.2, "difficulty": "Medium"},
    {"subject": "Chemistry", "chapter": "Physical Chemistry", "topic": "Ionic Equilibrium", "weight": 1.3, "difficulty": "Hard"},
    {"subject": "Chemistry", "chapter": "Physical Chemistry", "topic": "Electrochemistry", "weight": 1.2, "difficulty": "Medium"},
    {"subject": "Chemistry", "chapter": "Physical Chemistry", "topic": "Chemical Kinetics", "weight": 1.1, "difficulty": "Medium"},
    {"subject": "Chemistry", "chapter": "Inorganic Chemistry", "topic": "Periodic Table", "weight": 1.0, "difficulty": "Easy"},
    {"subject": "Chemistry", "chapter": "Inorganic Chemistry", "topic": "s-Block Elements", "weight": 0.8, "difficulty": "Easy"},
    {"subject": "Chemistry", "chapter": "Inorganic Chemistry", "topic": "p-Block Elements", "weight": 1.3, "difficulty": "Medium"},
    {"subject": "Chemistry", "chapter": "Inorganic Chemistry", "topic": "d and f Block Elements", "weight": 1.2, "difficulty": "Hard"},
    {"subject": "Chemistry", "chapter": "Inorganic Chemistry", "topic": "Coordination Compounds", "weight": 1.1, "difficulty": "Medium"},
    {"subject": "Chemistry", "chapter": "Organic Chemistry", "topic": "Basic Concepts", "weight": 1.0, "difficulty": "Easy"},
    {"subject": "Chemistry", "chapter": "Organic Chemistry", "topic": "Hydrocarbons", "weight": 1.2, "difficulty": "Medium"},
    {"subject": "Chemistry", "chapter": "Organic Chemistry", "topic": "Organic Compounds with Functional Groups", "weight": 1.4, "difficulty": "Hard"},
    {"subject": "Chemistry", "chapter": "Organic Chemistry", "topic": "Biomolecules", "weight": 0.9, "difficulty": "Medium"},
    {"subject": "Chemistry", "chapter": "Organic Chemistry", "topic": "Polymers", "weight": 0.8, "difficulty": "Easy"},
    {"subject": "Chemistry", "chapter": "Organic Chemistry", "topic": "Chemistry in Everyday Life", "weight": 0.7, "difficulty": "Easy"},
    
    # MATHEMATICS
    {"subject": "Mathematics", "chapter": "Algebra", "topic": "Sets and Relations", "weight": 0.9, "difficulty": "Easy"},
    {"subject": "Mathematics", "chapter": "Algebra", "topic": "Complex Numbers", "weight": 1.2, "difficulty": "Medium"},
    {"subject": "Mathematics", "chapter": "Algebra", "topic": "Quadratic Equations", "weight": 1.1, "difficulty": "Medium"},
    {"subject": "Mathematics", "chapter": "Algebra", "topic": "Sequences and Series", "weight": 1.2, "difficulty": "Medium"},
    {"subject": "Mathematics", "chapter": "Algebra", "topic": "Permutations and Combinations", "weight": 1.3, "difficulty": "Hard"},
    {"subject": "Mathematics", "chapter": "Algebra", "topic": "Binomial Theorem", "weight": 1.0, "difficulty": "Medium"},
    {"subject": "Mathematics", "chapter": "Algebra", "topic": "Matrices and Determinants", "weight": 1.4, "difficulty": "Hard"},
    {"subject": "Mathematics", "chapter": "Trigonometry", "topic": "Trigonometric Functions", "weight": 1.2, "difficulty": "Medium"},
    {"subject": "Mathematics", "chapter": "Trigonometry", "topic": "Inverse Trigonometric Functions", "weight": 1.0, "difficulty": "Medium"},
    {"subject": "Mathematics", "chapter": "Trigonometry", "topic": "Trigonometric Equations", "weight": 1.1, "difficulty": "Medium"},
    {"subject": "Mathematics", "chapter": "Coordinate Geometry", "topic": "Straight Lines", "weight": 1.1, "difficulty": "Easy"},
    {"subject": "Mathematics", "chapter": "Coordinate Geometry", "topic": "Circles", "weight": 1.2, "difficulty": "Medium"},
    {"subject": "Mathematics", "chapter": "Coordinate Geometry", "topic": "Conic Sections", "weight": 1.4, "difficulty": "Hard"},
    {"subject": "Mathematics", "chapter": "Coordinate Geometry", "topic": "3D Geometry", "weight": 1.3, "difficulty": "Hard"},
    {"subject": "Mathematics", "chapter": "Calculus", "topic": "Limits and Continuity", "weight": 1.2, "difficulty": "Medium"},
    {"subject": "Mathematics", "chapter": "Calculus", "topic": "Differentiation", "weight": 1.5, "difficulty": "Hard"},
    {"subject": "Mathematics", "chapter": "Calculus", "topic": "Applications of Derivatives", "weight": 1.3, "difficulty": "Hard"},
    {"subject": "Mathematics", "chapter": "Calculus", "topic": "Integration", "weight": 1.5, "difficulty": "Hard"},
    {"subject": "Mathematics", "chapter": "Calculus", "topic": "Differential Equations", "weight": 1.2, "difficulty": "Hard"},
    {"subject": "Mathematics", "chapter": "Vectors", "topic": "Vector Algebra", "weight": 1.1, "difficulty": "Medium"},
    {"subject": "Mathematics", "chapter": "Probability", "topic": "Probability Theory", "weight": 1.3, "difficulty": "Medium"},
    {"subject": "Mathematics", "chapter": "Statistics", "topic": "Mean, Median, Mode", "weight": 0.8, "difficulty": "Easy"},
]


def seed_jee_topics(db_path=None):
    """
    Seed JEE syllabus topics into the database
    
    Args:
        db_path: Path to database file
    """
    if db_path is None:
        db_path = get_db_path()
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if already seeded
        cursor.execute("SELECT COUNT(*) FROM topics")
        count = cursor.fetchone()[0]
        if count > 0:
            return True  # Already seeded
        
        inserted_count = 0
        for topic_data in JEE_TOPICS:
            cursor.execute("""
                INSERT OR IGNORE INTO topics 
                (subject, chapter_name, topic_name, exam_weight, difficulty_level)
                VALUES (?, ?, ?, ?, ?)
            """, (
                topic_data["subject"],
                topic_data["chapter"],
                topic_data["topic"],
                topic_data["weight"],
                topic_data["difficulty"]
            ))
            if cursor.rowcount > 0:
                inserted_count += 1
        
        conn.commit()
        
        print(f"✅ Successfully seeded {inserted_count} JEE topics")
        
        # Show summary by subject
        cursor.execute("""
            SELECT subject, COUNT(*) as count 
            FROM topics 
            GROUP BY subject
        """)
        summary = cursor.fetchall()
        
        print("\n📊 Topics by subject:")
        for subject, count in summary:
            print(f"   - {subject}: {count} topics")
        
        return True
    
    except sqlite3.Error as e:
        print(f"❌ Error seeding topics: {e}", file=sys.stderr)
        conn.rollback()
        return False
    
    finally:
        conn.close()


def seed_jee_topics_silent(db_path=None):
    """
    Seed JEE topics silently (for production/Streamlit Cloud)
    Returns True if successful or already seeded
    """
    if db_path is None:
        db_path = get_db_path()
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if already seeded
        cursor.execute("SELECT COUNT(*) FROM topics")
        count = cursor.fetchone()[0]
        if count > 0:
            conn.close()
            return True  # Already seeded
        
        # Insert topics
        for topic_data in JEE_TOPICS:
            cursor.execute("""
                INSERT OR IGNORE INTO topics 
                (subject, chapter_name, topic_name, exam_weight, difficulty_level)
                VALUES (?, ?, ?, ?, ?)
            """, (
                topic_data["subject"],
                topic_data["chapter"],
                topic_data["topic"],
                topic_data["weight"],
                topic_data["difficulty"]
            ))
        
        conn.commit()
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Error seeding topics: {e}", file=sys.stderr)
        return False


if __name__ == "__main__":
    print("=== Seeding JEE Syllabus Data ===\n")
    
    db_path = get_db_path()
    if not db_path.exists():
        print(f"❌ Database not found at {db_path}")
        print("Please run init_db.py first to create the database.")
    else:
        success = seed_jee_topics()
        if success:
            print("\n✅ JEE syllabus data seeded successfully!")
        else:
            print("\n❌ Failed to seed JEE syllabus data!")
