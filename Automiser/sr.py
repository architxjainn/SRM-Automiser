import asyncio
import os
import json
from datetime import date, datetime
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
from playwright.async_api import async_playwright
import google.generativeai as genai

# --- DEPENDENCY AUTO-INSTALL FOR OCR & PDF PARSING ---
try:
    import pypdf
except ImportError:
    os.system("pip install pypdf")
    import pypdf

try:
    import pytesseract
    from PIL import Image
except ImportError:
    os.system("pip install pytesseract pillow")
    import pytesseract
    from PIL import Image

st.set_page_config(page_title="SRM AI Autonomous Academic & Leave Engine", layout="wide")
st.title("🚀 SRM AI Autonomous Academic, Attendance & Leave Optimizer")
st.caption("1st Sem B.Tech CSE (AI/ML) | PYQ AI Generator, Persistent Storage, Captcha Session Vault & SRM Engine")

# --- STORAGE LOCATIONS (DOCUMENTS FOLDER) ---
ATTENDANCE_FILE = os.path.expanduser("~/Documents/attendance_raw.html")
SESSION_COOKIE_FILE = os.path.expanduser("~/Documents/srm_session.json")
DRIVE_FOLDER = os.path.expanduser("~/Documents/SRM_Notes_Drive")
SYLLABUS_FILE = os.path.expanduser("~/Documents/SRM_Notes_Drive/syllabus_progress.json")
MARKS_FILE = os.path.expanduser("~/Documents/SRM_Notes_Drive/user_marks.json")
os.makedirs(DRIVE_FOLDER, exist_ok=True)

# --- PERMANENT GEMINI API KEY CONFIGURATION ---
PERMANENT_GEMINI_KEY = "GCP_API_KEY"  # <-- Paste your Gemini API key here inside quotes!

SUBJECT_CODES = ["26CSE1002J", "26MAB1001T", "26CYB1002J", "26BTB1001T", "26LCA1007J"]

# --- INITIALIZE SUBJECT FOLDER HIERARCHY ---
def init_folder_structure():
    for subj in SUBJECT_CODES:
        subj_dir = os.path.join(DRIVE_FOLDER, subj)
        os.makedirs(os.path.join(subj_dir, "Syllabus_and_Lesson_Plan"), exist_ok=True)
        os.makedirs(os.path.join(subj_dir, "PYQs"), exist_ok=True)
        for u in range(1, 6):
            os.makedirs(os.path.join(subj_dir, f"Unit_{u}"), exist_ok=True)

init_folder_structure()

# --- PERSISTENT MARKS MANAGEMENT ---
def load_saved_marks():
    if os.path.exists(MARKS_FILE):
        try:
            with open(MARKS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_marks(marks_dict):
    with open(MARKS_FILE, "w", encoding="utf-8") as f:
        json.dump(marks_dict, f, indent=4)

saved_marks = load_saved_marks()

# --- OFFICIAL END-SEMESTER EXAM TIMETABLE (DECEMBER 2026) ---
END_SEM_EXAMS = [
    {"Code": "26CSE1002J", "Subject": "PROGRAMMING FOR PROBLEM SOLVING", "Date & Time": "14-DEC-2026 FN (10:00-01:00)", "Credits": 4},
    {"Code": "26LCA1007J", "Subject": "SPANISH", "Date & Time": "15-DEC-2026 FN (10:00-01:00)", "Credits": 2},
    {"Code": "26BTB1001T", "Subject": "INTRODUCTION TO COMPUTATIONAL BIOLOGY", "Date & Time": "16-DEC-2026 FN (10:00-01:00)", "Credits": 2},
    {"Code": "26CYB1002J", "Subject": "CHEMISTRY FOR COMPUTER SCIENCE", "Date & Time": "17-DEC-2026 FN (10:00-01:00)", "Credits": 4},
    {"Code": "26MAB1001T", "Subject": "CALCULUS AND LINEAR ALGEBRA", "Date & Time": "19-DEC-2026 FN (10:00-01:00)", "Credits": 4},
]

# --- OFFICIAL BASE SYLLABUS STRUCTURE ---
OFFICIAL_SYLLABUS = {
    "26CSE1002J": {
        "Unit 1: Basic Logic, Control Flow & User I/O": {
            "Relational operators, boolean logic & conditional checks": False,
            "Standard I/O: Reading & displaying data in C": False,
            "Menu-driven programs using switch statements": False,
            "Comparing switch vs if...else-if...else statements": False,
        },
        "Unit 2: Functions, Call Mechanics & Recursion": {
            "Modular programming, pass-by-value & pass-by-reference": False,
            "Recursive thinking for subproblems (Factorial, Fibonacci, GCD)": False,
            "Call stack expansion/contraction tracing": False,
            "Recursive algorithms for reverse number, palindrome & Euclid's GCD": False,
        },
        "Unit 3: Loops, Array Processing & Strings": {
            "Structured iterative solutions (while, do-while, for loops)": False,
            "Loop-based reasoning for numeric sequences & pattern printing": False,
            "Linear search in arrays for successful/unsuccessful cases": False,
            "Array reversal, element frequency counter & string concatenation": False,
        },
        "Unit 4: Recursive Algorithms, Control Transfer & Performance": {
            "Binary search implementation using recursion vs iteration": False,
            "Recursion vs iteration analysis (Factorial, Palindrome, power a^n)": False,
            "Loop control mechanics using break and continue statements": False,
            "Memory & performance tradeoffs between recursion and iteration": False,
        },
        "Unit 5: Dynamic Memory Allocation & File I/O": {
            "Dynamic memory allocation using malloc, calloc, realloc, and free": False,
            "Dynamic list implementation and runtime array resizing": False,
            "Standard file handling in C (fopen, fscanf, fgets, feof, fclose)": False,
            "File processing: Character, word, line counting & frequency report": False,
        }
    },
    "26MAB1001T": {
        "Unit-1: Vector Space and Matrices": {
            "Review of matrices": False,
            "Vector space and subspace": False,
            "Linear dependence and independence": False,
            "Characteristic equation": False,
            "Eigenvalues and eigenvectors of a real matrix": False,
            "Cayley-Hamilton theorem": False,
            "Linear transformation on Rn": False,
            "Orthogonal transformation": False,
            "Diagonalization of a matrix": False,
        },
        "Unit-2: Ordinary Differential Equations": {
            "Review of continuity and differentiability": False,
            "First-order differential equation": False,
            "Linear second-order differential equations with constant coefficients": False,
            "Method of variation of parameters": False,
            "Cauchy-Euler equation": False,
            "Legendre's equation": False,
        },
        "Unit-3: Differential Calculus and Applications": {
            "Review of curve tracing": False,
            "Curvature, radius of curvature - cartesian forms": False,
            "Radius of curvature polar and parametric forms": False,
            "Circle of curvature": False,
            "Evolutes and involutes": False,
            "Envelope": False,
            "Pedal equations": False,
        },
        "Unit-4: Functions of Several Variables": {
            "Review of limit, continuity and differentiability": False,
            "Introduction to partial derivatives": False,
            "Partial derivatives and geometrical interpretation": False,
            "Total derivative and implicit function": False,
            "Euler's theorem on homogeneous functions": False,
            "Chain rule and Jacobians": False,
            "Taylor's series for two variables": False,
            "Extrema of functions of two variables": False,
            "Lagrange's multiplier method": False,
        },
        "Unit-5: Sequence and Series": {
            "Review of sequence and series": False,
            "Series of positive terms": False,
            "Test of convergence - Cauchy integral test": False,
            "Comparison test": False,
            "D'Alembert ratio test and Raabe's test": False,
            "Logarithmic test and Cauchy root test": False,
            "Alternating series - Leibnitz test": False,
            "Absolute convergence": False,
            "Conditional convergence": False,
        }
    },
    "26CYB1002J": {
        "Unit 1: Quantum Mechanics & Molecular Orbitals": {
            "Wave Theory & Uncertainty Principle": False,
            "Postulates of Quantum Mechanics & Schrodinger Eq": False,
            "Particle in a Box Solution (Energy & Wave Eq)": False,
            "Radial & Angular Wave Functions of H-Atom": False,
            "Significance of Wave Function": False,
            "Molecular Orbital Theory & LCAO Method": False,
            "Structure and Orbital Picture of Butadiene": False,
            "Structure and Orbital Picture of Benzene": False,
        },
        "Unit 2: Periodic Properties & Cheminformatics": {
            "Effective Nuclear Charge & Slater's Rule": False,
            "Ionization Energy, Affinity & Electronegativity": False,
            "Polarizability & Fajans' Rule": False,
            "Cheminformatics Introduction & Importance": False,
            "Molecular Geometry & Stereochemistry": False,
            "Molecular Representations (2D, 3D, SMILES, InChI)": False,
            "Software Tools (RDKit, Molecular Drawing)": False,
            "Major Chemical Databases (PubChem, ChEMBL)": False,
        },
        "Unit 3: Thermodynamics & Electrochemistry": {
            "Internal Energy and Enthalpy": False,
            "Free Energies (Helmholtz & Gibbs) & Entropy": False,
            "Laws of Thermodynamics & Basic Terms": False,
            "Gibbs Free Energy & Cell Potential Relationship": False,
            "Nernst Equation Derivation & Applications": False,
            "Galvanic Cells & Electrode Potentials": False,
        },
        "Unit 4: Materials & Nanomaterials": {
            "Magnetic and Superconducting Materials": False,
            "Band Structure of Solids & Doping": False,
            "Semiconductor Materials & Applications": False,
            "Nanomaterials Introduction & Properties": False,
            "Types of Nanomaterials (0D, 1D, 2D, 3D)": False,
            "Quantum Dots & Applications": False,
        },
        "Unit 5: Spectroscopy": {
            "Electromagnetic Radiation Properties & Regions": False,
            "Vibrational & Electronic Spectroscopy Principles": False,
            "Born-Oppenheimer Approximation": False,
            "UV-Visible Spectroscopy Principle & Applications": False,
            "IR Spectroscopy Principle & Applications": False,
            "Bandgap Calculation using UV-Vis": False,
            "NMR Spectroscopy Theory & Chemical Shift": False,
        }
    },
    "26BTB1001T": {
        "Unit 1: Cell Basics & Computing Analogies": {
            "Cell theory and prokaryotic/eukaryotic differences": False,
            "Organelles as CPU components analogy": False,
            "DNA replication compared to code duplication": False,
            "Cell division as parallel computing": False,
            "Genetic algorithms for biological optimization": False,
            "Evolutionary computing in cell/tissue modelling": False,
        },
        "Unit 2: Biomolecules as Data Structures": {
            "Carbohydrates/lipids as energy/membrane storage": False,
            "Proteins/nucleic acids as functional data structures": False,
            "Enzymes as biological catalysts": False,
            "Nucleic acid structure-function relationships": False,
            "BLAST tool for sequence database queries": False,
            "Human Genome Project as big data genomics": False,
        },
        "Unit 3: Protein Structures & Prediction": {
            "Protein synthesis and primary structure": False,
            "Secondary/tertiary/quaternary organisation": False,
            "PyMOL for 3D protein visualisation": False,
            "Secondary structure prediction methods": False,
            "Python programming for structure analysis": False,
            "Basics for drug design": False,
        },
        "Unit 4: AI/ML Foundations in Biology": {
            "Overview of AI for biological big data": False,
            "Supervised and unsupervised learning basics": False,
            "Feature representations for sequences and omics": False,
            "AI data pipeline: preprocess, train, evaluate": False,
            "Applications in genomics and systems biology": False,
            "Benefits and limitations of AI in biology": False,
        },
        "Unit 5: Deep Learning, Healthcare & Ethics": {
            "Deep learning for images, signals and sequences": False,
            "AI in drug discovery and biotechnology": False,
            "AI-assisted medical diagnostics and imaging": False,
            "AI for integrated bioinformatics and health data": False,
            "Real-time AI for monitoring and decision support": False,
            "Ethical and social issues of AI in biology": False,
        }
    },
    "26LCA1007J": {
        "Unit 1: Spanish Vocabulary & Grammar": {
            "Basic Greetings and Noun Genders": False,
            "Definite & Indefinite Articles": False,
        },
        "Unit 2: Conjugations & Present Tense": {
            "Regular -AR, -ER, -IR Verbs": False,
            "Ser vs Estar Usage": False,
        },
        "Unit 3: Conversational Spanish": {
            "Numbers, Days & Months": False,
            "Asking Directions & Ordering Food": False,
        },
        "Unit 4: Advanced Spanish Expressions": {
            "Possessive Adjectives & Prepositions": False,
            "Reflexive Verbs & Daily Routine": False,
        },
        "Unit 5: Culture & Reading Comprehension": {
            "Short Passage Reading": False,
            "Cultural Insights of Spanish Speaking World": False,
        }
    }
}

def load_and_sync_syllabus_progress():
    existing_progress = {}
    if os.path.exists(SYLLABUS_FILE):
        try:
            with open(SYLLABUS_FILE, "r", encoding="utf-8") as f:
                existing_progress = json.load(f)
        except Exception:
            pass
            
    synced_progress = {}
    for subj, units in OFFICIAL_SYLLABUS.items():
        synced_progress[subj] = {}
        for unit, topics in units.items():
            synced_progress[subj][unit] = {}
            for topic in topics.keys():
                prev_state = existing_progress.get(subj, {}).get(unit, {}).get(topic, False)
                synced_progress[subj][unit][topic] = prev_state
                
    save_syllabus_progress(synced_progress)
    return synced_progress

def save_syllabus_progress(progress_data):
    with open(SYLLABUS_FILE, "w", encoding="utf-8") as f:
        json.dump(progress_data, f, indent=4)

syllabus_state = load_and_sync_syllabus_progress()

# --- OFFLINE FALLBACK GENERATOR ---
def generate_offline_fallback_questions(subject, q_type, completed_topics):
    questions = []
    for idx, topic in enumerate(completed_topics[:5], 1):
        if "MCQ" in q_type:
            questions.append(f"""**Q{idx}. Which of the following best explains the core principle of {topic}?**\n- A) Primary definition and standard operational syntax\n- B) Secondary inverse execution\n- C) None of the above\n- D) All of the above\n*Correct Answer:* A \n*Explanation:* (Offline Fallback Generated) {topic} forms a foundational component under {subject}.""")
        elif "2-Marker" in q_type:
            questions.append(f"""**Q{idx}. Define {topic}.**\n*Answer Key:* {topic} is a critical theoretical/practical module in {subject} used for optimizing system performance and solving structural dependencies.""")
        elif "4-Marker" in q_type:
            questions.append(f"""**Q{idx}. Explain the working mechanism and significance of {topic}.**\n*Answer Key:* \n1. Core architecture of {topic}.\n2. Step-by-step execution flow.\n3. Application in real-world scenarios.""")
        else:
            questions.append(f"""**Q{idx}. Provide a comprehensive derivation, architectural layout, and implementation of {topic}.**\n*Answer Key:* \n- **Introduction:** Detailed overview of {topic}.\n- **Mathematical / Code Formulation:** Step-by-step syntax or derivation.\n- **Complexity & Evaluation:** Performance analysis and university exam standards.""")
    return "\n\n---\n\n".join(questions)

# --- ACCURATE SRM ACADEMIC CALENDAR (Oct 15 - Dec 7, 2026) ---
ACADEMIC_CALENDAR = {
    date(2026, 10, 15): {"type": "Working day", "week": "Wk 12", "schedule": "Day Order 3", "event": "Normal Working Day"},
    date(2026, 10, 16): {"type": "Working day", "week": "Wk 12", "schedule": "Day Order 4", "event": "Normal Working Day"},
    date(2026, 10, 17): {"type": "Holiday", "week": "Wk 0", "schedule": "Holiday / Weekend", "event": "Saturday Holiday"},
    date(2026, 10, 18): {"type": "Holiday", "week": "Wk 0", "schedule": "Holiday / Weekend", "event": "Sunday Holiday"},
    date(2026, 10, 19): {"type": "Holiday", "week": "Wk 0", "schedule": "Holiday / Weekend", "event": "Ayutha Pooja"},
    date(2026, 10, 20): {"type": "Holiday", "week": "Wk 0", "schedule": "Holiday / Weekend", "event": "Vijaya Dasami"},
    date(2026, 10, 21): {"type": "Working day", "week": "Wk 12", "schedule": "Day Order 5", "event": "Normal Working Day"},
    date(2026, 10, 22): {"type": "Working day", "week": "Wk 13", "schedule": "Day Order 1", "event": "Normal Working Day"},
    date(2026, 10, 23): {"type": "Working day", "week": "Wk 13", "schedule": "Day Order 2", "event": "Normal Working Day"},
    date(2026, 10, 24): {"type": "Holiday", "week": "Wk 0", "schedule": "Holiday / Weekend", "event": "Saturday Holiday"},
    date(2026, 10, 25): {"type": "Holiday", "week": "Wk 0", "schedule": "Holiday / Weekend", "event": "Sunday Holiday"},
    date(2026, 10, 26): {"type": "Working day", "week": "Wk 13", "schedule": "Day Order 3", "event": "Normal Working Day"},
    date(2026, 10, 27): {"type": "Working day", "week": "Wk 13", "schedule": "Day Order 4", "event": "Normal Working Day"},
    date(2026, 10, 28): {"type": "Working day", "week": "Wk 13", "schedule": "Day Order 5", "event": "Normal Working Day"},
    date(2026, 10, 29): {"type": "Working day", "week": "Wk 14", "schedule": "Day Order 1", "event": "Normal Working Day"},
    date(2026, 10, 30): {"type": "Working day", "week": "Wk 14", "schedule": "Day Order 2", "event": "Normal Working Day"},
    date(2026, 10, 31): {"type": "Holiday", "week": "Wk 0", "schedule": "Holiday / Weekend", "event": "Saturday Holiday"},
    date(2026, 11, 1): {"type": "Holiday", "week": "Wk 0", "schedule": "Holiday / Weekend", "event": "Sunday Holiday"},
    date(2026, 11, 2): {"type": "Working day", "week": "Wk 14", "schedule": "Day Order 3", "event": "Normal Working Day"},
    date(2026, 11, 3): {"type": "Working day", "week": "Wk 14", "schedule": "Day Order 4", "event": "Normal Working Day"},
    date(2026, 11, 4): {"type": "Working day", "week": "Wk 14", "schedule": "Day Order 5", "event": "Normal Working Day"},
    date(2026, 11, 5): {"type": "Working day", "week": "Wk 15", "schedule": "Day Order 1", "event": "Normal Working Day"},
    date(2026, 11, 6): {"type": "Working day", "week": "Wk 15", "schedule": "Day Order 2", "event": "Normal Working Day"},
    date(2026, 11, 7): {"type": "Holiday", "week": "Wk 0", "schedule": "Holiday / Weekend", "event": "Saturday Holiday"},
    date(2026, 11, 8): {"type": "Holiday", "week": "Wk 0", "schedule": "Holiday / Weekend", "event": "Sunday Holiday"},
    date(2026, 11, 9): {"type": "Working day", "week": "Wk 15", "schedule": "Day Order 3", "event": "Normal Working Day"},
    date(2026, 11, 10): {"type": "Working day", "week": "Wk 15", "schedule": "Day Order 4", "event": "Normal Working Day"},
    date(2026, 11, 11): {"type": "Working day", "week": "Wk 15", "schedule": "Day Order 5", "event": "Normal Working Day"},
    date(2026, 11, 12): {"type": "Working day", "week": "Wk 16", "schedule": "Day Order 1", "event": "Normal Working Day"},
    date(2026, 11, 13): {"type": "Working day", "week": "Wk 16", "schedule": "Day Order 2", "event": "Normal Working Day"},
    date(2026, 11, 14): {"type": "Holiday", "week": "Wk 0", "schedule": "Holiday / Weekend", "event": "Saturday Holiday"},
    date(2026, 11, 15): {"type": "Holiday", "week": "Wk 0", "schedule": "Holiday / Weekend", "event": "Sunday Holiday"},
    date(2026, 11, 16): {"type": "Working day", "week": "Wk 16", "schedule": "Day Order 3", "event": "Normal Working Day"},
    date(2026, 11, 17): {"type": "Working day", "week": "Wk 16", "schedule": "Day Order 4", "event": "Normal Working Day"},
    date(2026, 11, 18): {"type": "Working day", "week": "Wk 16", "schedule": "Day Order 5", "event": "Normal Working Day"},
    date(2026, 11, 19): {"type": "Working day", "week": "Wk 17", "schedule": "Day Order 1", "event": "Normal Working Day"},
    date(2026, 11, 20): {"type": "Working day", "week": "Wk 17", "schedule": "Day Order 2", "event": "Last Working Day - PG"},
    date(2026, 11, 21): {"type": "Holiday", "week": "Wk 0", "schedule": "Holiday / Weekend", "event": "Saturday Holiday"},
    date(2026, 11, 22): {"type": "Holiday", "week": "Wk 0", "schedule": "Holiday / Weekend", "event": "Sunday Holiday"},
    date(2026, 11, 23): {"type": "Working day", "week": "Wk 17", "schedule": "Day Order 3", "event": "Normal Working Day"},
    date(2026, 11, 24): {"type": "Working day", "week": "Wk 17", "schedule": "Day Order 4", "event": "Normal Working Day"},
    date(2026, 11, 25): {"type": "Working day", "week": "Wk 17", "schedule": "Day Order 5", "event": "Normal Working Day"},
    date(2026, 11, 26): {"type": "Working day", "week": "Wk 18", "schedule": "Day Order 1", "event": "Normal Working Day"},
    date(2026, 11, 27): {"type": "Working day", "week": "Wk 18", "schedule": "Day Order 2", "event": "Normal Working Day"},
    date(2026, 11, 28): {"type": "Holiday", "week": "Wk 0", "schedule": "Holiday / Weekend", "event": "Saturday Holiday"},
    date(2026, 11, 29): {"type": "Holiday", "week": "Wk 0", "schedule": "Holiday / Weekend", "event": "Sunday Holiday"},
    date(2026, 11, 30): {"type": "Working day", "week": "Wk 18", "schedule": "Day Order 3", "event": "Normal Working Day"},
    date(2026, 12, 1): {"type": "Working day", "week": "Wk 18", "schedule": "Day Order 4", "event": "Normal Working Day"},
    date(2026, 12, 2): {"type": "Working day", "week": "Wk 18", "schedule": "Day Order 5", "event": "Normal Working Day"},
    date(2026, 12, 3): {"type": "Working day", "week": "Wk 19", "schedule": "Day Order 1", "event": "Normal Working Day"},
    date(2026, 12, 4): {"type": "Working day", "week": "Wk 19", "schedule": "Day Order 2", "event": "Normal Working Day"},
    date(2026, 12, 5): {"type": "Holiday", "week": "Wk 0", "schedule": "Holiday / Weekend", "event": "Saturday Holiday"},
    date(2026, 12, 6): {"type": "Holiday", "week": "Wk 0", "schedule": "Holiday / Weekend", "event": "Sunday Holiday"},
    date(2026, 12, 7): {"type": "Working day", "week": "Wk 19", "schedule": "Day Order 3", "event": "Last Working Day - UG First Year"},
}

MASTER_SCHEDULES = {
    "Day Order 1": [
        {"Time": "06:30 – 07:00 AM", "Activity / Class": "Wakeup & Morning Routine", "Category": "Routine"},
        {"Time": "07:00 – 07:40 AM", "Activity / Class": "Breakfast Break", "Category": "Meals"},
        {"Time": "07:40 – 08:00 AM", "Activity / Class": "Travel Buffer (Walk to class)", "Category": "Travel"},
        {"Time": "08:00 – 09:40 AM", "Activity / Class": "Classes: 26BTB1001T (Computational Biology)", "Category": "Lecture"},
        {"Time": "09:45 – 11:30 AM", "Activity / Class": "Library Slot 1 (C Programming Fundamentals)", "Category": "Study Block"},
        {"Time": "11:30 – 12:30 PM", "Activity / Class": "Lunch Break", "Category": "Meals"},
        {"Time": "12:30 – 01:05 PM", "Activity / Class": "Short Library Break / Quick Reading", "Category": "Study Block"},
        {"Time": "01:25 – 03:10 PM", "Activity / Class": "Classes: 26CYB1002J (Chemistry for CS)", "Category": "Lecture"},
        {"Time": "03:10 – 04:30 PM", "Activity / Class": "Library Slot 2 (Calculus & Linear Algebra Practice)", "Category": "Study Block"},
        {"Time": "05:30 – 07:00 PM", "Activity / Class": "Library / Hostel Desk (Chemistry Revision & Lab Prep)", "Category": "Study Block"},
        {"Time": "07:00 – 07:30 PM", "Activity / Class": "Walk back from library & unwind", "Category": "Travel/Rest"},
        {"Time": "07:30 – 08:30 PM", "Activity / Class": "Dinner Break", "Category": "Meals"},
        {"Time": "08:30 – 09:30 PM", "Activity / Class": "Hostel Desk (Light Revision, C Practice & Daily Recap)", "Category": "Study Block"},
        {"Time": "09:30 – 11:00 PM", "Activity / Class": "Free Time / Personal Time / Relaxation", "Category": "Rest"},
        {"Time": "11:00 PM", "Activity / Class": "Sleep Time", "Category": "Rest"}
    ],
    "Day Order 2": [
        {"Time": "06:30 – 07:00 AM", "Activity / Class": "Wakeup & Morning Routine", "Category": "Routine"},
        {"Time": "07:00 – 07:40 AM", "Activity / Class": "Breakfast Break", "Category": "Meals"},
        {"Time": "07:40 – 08:00 AM", "Activity / Class": "Travel Buffer", "Category": "Travel"},
        {"Time": "08:00 – 09:40 AM", "Activity / Class": "Classes: 26CSE1002J (Programming for Problem Solving)", "Category": "Lecture"},
        {"Time": "09:45 – 11:30 AM", "Activity / Class": "Library Slot 1 (C Practice & Logic Building)", "Category": "Study Block"},
        {"Time": "11:30 – 12:10 PM", "Activity / Class": "Lunch Break", "Category": "Meals"},
        {"Time": "12:30 – 02:15 PM", "Activity / Class": "Classes: 26MAB1001T (Calculus and Linear Algebra)", "Category": "Lecture"},
        {"Time": "02:15 – 03:50 PM", "Activity / Class": "Library Slot 2 (Calculus Problem Solving)", "Category": "Study Block"},
        {"Time": "04:00 – 04:50 PM", "Activity / Class": "Classes: 26BTB1001T (Computational Biology)", "Category": "Lecture"},
        {"Time": "05:30 – 07:00 PM", "Activity / Class": "Library / Hostel Desk (Comp Bio Notes Review)", "Category": "Study Block"},
        {"Time": "07:00 – 07:30 PM", "Activity / Class": "Walk back & unwind", "Category": "Travel/Rest"},
        {"Time": "07:30 – 08:30 PM", "Activity / Class": "Dinner Break", "Category": "Meals"},
        {"Time": "08:30 – 09:30 PM", "Activity / Class": "Hostel Desk (Light Revision & C Practice)", "Category": "Study Block"},
        {"Time": "09:30 – 11:00 PM", "Activity / Class": "Free Time / Personal Time", "Category": "Rest"},
        {"Time": "11:00 PM", "Activity / Class": "Sleep Time", "Category": "Rest"}
    ],
    "Day Order 3": [
        {"Time": "06:30 – 07:00 AM", "Activity / Class": "Wakeup & Morning Routine", "Category": "Routine"},
        {"Time": "07:00 – 07:40 AM", "Activity / Class": "Breakfast Break", "Category": "Meals"},
        {"Time": "07:40 – 08:00 AM", "Activity / Class": "Travel Buffer", "Category": "Travel"},
        {"Time": "08:00 – 09:40 AM", "Activity / Class": "Classes: 26LCA1007J (Spanish)", "Category": "Lecture"},
        {"Time": "09:45 – 12:25 PM", "Activity / Class": "Classes Block: 26BTB1001T, 26CYB1002J, 26MAB1001T", "Category": "Lecture"},
        {"Time": "12:25 – 01:05 PM", "Activity / Class": "Quick Lunch Break", "Category": "Meals"},
        {"Time": "01:25 – 04:50 PM", "Activity / Class": "Classes: 26MEE1001L (Workshop Practice Lab)", "Category": "Lab"},
        {"Time": "05:30 – 07:00 PM", "Activity / Class": "Library / Hostel Desk (Light Review / Rest Block)", "Category": "Study Block"},
        {"Time": "07:00 – 07:30 PM", "Activity / Class": "Walk back & unwind", "Category": "Travel/Rest"},
        {"Time": "07:30 – 08:30 PM", "Activity / Class": "Dinner Break", "Category": "Meals"},
        {"Time": "08:30 – 09:30 PM", "Activity / Class": "Hostel Desk (Light Revision & Daily Recap)", "Category": "Study Block"},
        {"Time": "09:30 – 11:00 PM", "Activity / Class": "Free Time / Personal Time", "Category": "Rest"},
        {"Time": "11:00 PM", "Activity / Class": "Sleep Time", "Category": "Rest"}
    ],
    "Day Order 4": [
        {"Time": "06:30 – 07:00 AM", "Activity / Class": "Wakeup & Morning Routine", "Category": "Routine"},
        {"Time": "07:00 – 07:40 AM", "Activity / Class": "Breakfast Break", "Category": "Meals"},
        {"Time": "07:40 – 08:00 AM", "Activity / Class": "Travel Buffer", "Category": "Travel"},
        {"Time": "08:00 – 11:30 AM", "Activity / Class": "Classes: 26GNN1004L (National Service Scheme)", "Category": "Activity"},
        {"Time": "11:30 – 12:10 PM", "Activity / Class": "Lunch Break", "Category": "Meals"},
        {"Time": "12:30 – 02:15 PM", "Activity / Class": "Classes: 26CYB1002J (Chemistry)", "Category": "Lecture"},
        {"Time": "02:20 – 04:50 PM", "Activity / Class": "Classes: 26MAB1001T, 26CSE1002J, 26LCA1007J", "Category": "Lecture"},
        {"Time": "05:30 – 07:00 PM", "Activity / Class": "Library / Hostel Desk (C Exercises & Spanish Vocab)", "Category": "Study Block"},
        {"Time": "07:00 – 07:30 PM", "Activity / Class": "Walk back & unwind", "Category": "Travel/Rest"},
        {"Time": "07:30 – 08:30 PM", "Activity / Class": "Dinner Break", "Category": "Meals"},
        {"Time": "08:30 – 09:30 PM", "Activity / Class": "Hostel Desk (C Practice & Daily Recap)", "Category": "Study Block"},
        {"Time": "09:30 – 11:00 PM", "Activity / Class": "Free Time / Personal Time", "Category": "Rest"},
        {"Time": "11:00 PM", "Activity / Class": "Sleep Time", "Category": "Rest"}
    ],
    "Day Order 5": [
        {"Time": "06:30 – 07:00 AM", "Activity / Class": "Wakeup & Morning Routine", "Category": "Routine"},
        {"Time": "07:00 – 07:40 AM", "Activity / Class": "Breakfast Break", "Category": "Meals"},
        {"Time": "07:40 – 08:00 AM", "Activity / Class": "Travel Buffer", "Category": "Travel"},
        {"Time": "08:00 – 09:40 AM", "Activity / Class": "Classes: 26CSE1002J (PPS)", "Category": "Lecture"},
        {"Time": "09:45 – 10:35 AM", "Activity / Class": "Classes: 26LCA1007J (Spanish)", "Category": "Lecture"},
        {"Time": "10:40 – 11:30 AM", "Activity / Class": "Quick Library Break / Reading", "Category": "Study Block"},
        {"Time": "11:35 – 12:25 PM", "Activity / Class": "Classes: 26CYB1002J (Chemistry)", "Category": "Lecture"},
        {"Time": "12:25 – 01:30 PM", "Activity / Class": "Lunch Break", "Category": "Meals"},
        {"Time": "01:30 – 04:30 PM", "Activity / Class": "Library Slot (Prime Focus: C Programming Deep Practice)", "Category": "Study Block"},
        {"Time": "05:30 – 07:00 PM", "Activity / Class": "Library / Hostel Desk (Weekly Review & Light Revision)", "Category": "Study Block"},
        {"Time": "07:00 – 07:30 PM", "Activity / Class": "Walk back & unwind", "Category": "Travel/Rest"},
        {"Time": "07:30 – 08:30 PM", "Activity / Class": "Dinner Break", "Category": "Meals"},
        {"Time": "08:30 – 09:30 PM", "Activity / Class": "Hostel Desk (C Practice & Weekly Wrap-up)", "Category": "Study Block"},
        {"Time": "09:30 – 11:00 PM", "Activity / Class": "Free Time / Personal Time", "Category": "Rest"},
        {"Time": "11:00 PM", "Activity / Class": "Sleep Time", "Category": "Rest"}
    ],
    "Holiday / Weekend": [
        {"Time": "08:00 – 09:00 AM", "Activity / Class": "Wakeup, Morning Routine & Breakfast", "Category": "Routine/Meals"},
        {"Time": "09:00 – 11:30 AM", "Activity / Class": "Library Slot 1 (C Programming Logic & Homework Practice)", "Category": "Study Block"},
        {"Time": "11:30 – 12:30 PM", "Activity / Class": "Break / Walk / Unwind", "Category": "Rest"},
        {"Time": "12:30 – 01:30 PM", "Activity / Class": "Lunch Break", "Category": "Meals"},
        {"Time": "01:30 – 03:30 PM", "Activity / Class": "Library Slot 2 (Computational Biology & Spanish Revision)", "Category": "Study Block"},
        {"Time": "03:30 – 05:00 PM", "Activity / Class": "Free Time / Snacks / Relaxation", "Category": "Rest"},
        {"Time": "05:00 – 07:00 PM", "Activity / Class": "Library / Hostel Desk (Lab Report Completion & Week Planning)", "Category": "Study Block"},
        {"Time": "07:30 – 08:30 PM", "Activity / Class": "Dinner Break", "Category": "Meals"},
        {"Time": "08:30 – 11:00 PM", "Activity / Class": "Free Time / Personal Time / Relaxation", "Category": "Rest"},
        {"Time": "11:00 PM", "Activity / Class": "Sleep Time", "Category": "Rest"}
    ]
}

# --- PERSISTENT PLAYWRIGHT SESSION LOGIN (CAPTCHA BYPASS) ---
async def fetch_attendance_with_credentials(username, password, status_placeholder):
    user_email = username if "@" in username else f"{username}@srmist.edu.in"
    login_id = username.split("@")[0]

    import os
import subprocess

# Set path before anything else
async def fetch_attendance_with_credentials(username, password, status_placeholder):
    user_email = username if "@" in username else f"{username}@srmist.edu.in"
    login_id = username.split("@")[0]

    import os
    import subprocess

    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = "/tmp/ms-playwright"
    
    if not os.path.exists("/tmp/ms-playwright/chromium"):
        status_placeholder.text("Installing browser dependencies...")
        subprocess.run(["playwright", "install", "chromium"], check=True)

    status_placeholder.text("Starting browser session...")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-blink-features=AutomationControlled"
            ]
        )
        
        # ... continue with page / context code ...
        # Load Session Cookies if existing
        if os.path.exists(SESSION_COOKIE_FILE):
            try:
                context = await browser.new_context(storage_state=SESSION_COOKIE_FILE, viewport={"width": 1400, "height": 900})
            except Exception:
                context = await browser.new_context(viewport={"width": 1400, "height": 900})
        else:
            context = await browser.new_context(viewport={"width": 1400, "height": 900})
            
        page = await context.new_page()

        try:
            status_placeholder.info("🌐 Connecting to SRM Portal...")
            await page.goto("https://sp.srmist.edu.in/srmiststudentportal/", wait_until="networkidle")
            await page.wait_for_timeout(2000)

            # Check if session is already logged in
            if await page.locator('text="Attendance Details"').count() == 0:
                status_placeholder.info("🔑 Logging in & Saving Session Cookie Vault...")
                if "login.microsoftonline.com" in page.url or await page.locator('input[type="email"]').count() > 0:
                    await page.fill('input[type="email"]', user_email)
                    await page.click('input[type="submit"], button[type="submit"]')
                    await page.wait_for_timeout(2500)
                    await page.fill('input[type="password"]', password)
                    await page.click('input[type="submit"], button[type="submit"]')
                    await page.wait_for_timeout(3000)
                    if await page.locator('#idSIButton9').count() > 0:
                        await page.click('#idSIButton9')
                        await page.wait_for_timeout(2000)
                else:
                    user_field = page.locator('input[name="login"], input[name="username"], input[name="email"], input[type="text"]').first
                    pass_field = page.locator('input[name="password"], input[type="password"]').first
                    await user_field.fill(login_id)
                    await pass_field.fill(password)
                    await page.locator('button[type="submit"], input[type="submit"], #loginBtn').first.click()
                    await page.wait_for_timeout(4000)

                # Save session cookies to bypass captcha next time
                await context.storage_state(path=SESSION_COOKIE_FILE)

            attendance_nav = page.locator('text="Attendance Details"').first
            await attendance_nav.wait_for(state="visible", timeout=25000)
            await attendance_nav.click()
            await page.wait_for_timeout(3000)
            await page.wait_for_selector('table', timeout=20000)

            page_html = await page.content()
            if "<table" in page_html:
                with open(ATTENDANCE_FILE, "w", encoding="utf-8") as f:
                    f.write(page_html)
                await browser.close()
                return True, "Successfully synced live attendance & saved session cookies!"
            await browser.close()
            return False, "Attendance table empty."
        except Exception as e:
            await browser.close()
            return False, f"Sync error: {str(e)}"

# --- SIDEBAR ---
with st.sidebar:
    st.header("🔑 SRM Portal Config")
    srm_user = st.text_input("NetID / Register Number", value="aj9058")
    srm_pass = st.text_input("Portal Password", type="password")
    sync_btn = st.button("🔄 Fetch Real-Time Attendance", use_container_width=True)

    st.divider()
    target_pct = st.slider("Target Attendance %", 70.0, 90.0, 75.0, 0.5)

    st.divider()
    selected_date = st.date_input("Check Schedule Date", value=date.today())

status_box = st.empty()
if sync_btn:
    if not srm_user or not srm_pass:
        st.sidebar.error("Enter NetID and Password.")
    else:
        success, msg = asyncio.run(fetch_attendance_with_credentials(srm_user, srm_pass, status_box))
        status_box.empty()
        if success:
            st.sidebar.success(msg)
            st.cache_data.clear()
            st.rerun()
        else:
            st.sidebar.error(msg)

# --- ATTENDANCE PARSER ---
@st.cache_data(ttl=30)
def parse_and_process_attendance(target_val):
    if not os.path.exists(ATTENDANCE_FILE):
        return None
    with open(ATTENDANCE_FILE, "r", encoding="utf-8") as f:
        html_content = f.read()
    soup = BeautifulSoup(html_content, "html.parser")
    tables = soup.find_all("table")
    if not tables:
        return None
    target_table = tables[0]
    for tbl in tables:
        if "Code" in tbl.text.strip():
            target_table = tbl
            break
    data = []
    for row in target_table.find_all("tr"):
        cols = [col.text.strip() for col in row.find_all(["td", "th"])]
        if cols:
            data.append(cols)
    if len(data) < 2:
        return None
    df = pd.DataFrame(data[1:], columns=data[0])
    if 'Code' in df.columns:
        df = df[df['Code'] != 'Total'].copy()
    
    col_map = {}
    for c in df.columns:
        c_clean = c.replace("\n", " ").strip()
        if "Max" in c_clean: col_map[c] = 'Max. hours'
        elif "Att" in c_clean and "Absent" not in c_clean: col_map[c] = 'Att. hours'
        elif "Description" in c_clean: col_map[c] = 'Description'
        elif "Code" in c_clean: col_map[c] = 'Code'
    df.rename(columns=col_map, inplace=True)

    if 'Max. hours' in df.columns and 'Att. hours' in df.columns:
        df['Max. hours'] = pd.to_numeric(df['Max. hours'], errors='coerce')
        df['Att. hours'] = pd.to_numeric(df['Att. hours'], errors='coerce')
        
        df['Attendance %'] = ((df['Att. hours'] / df['Max. hours']) * 100).round(2)

        margins, statuses = [], []
        dec = target_val / 100.0
        for _, row in df.iterrows():
            max_h, att_h = row['Max. hours'], row['Att. hours']
            if pd.isna(max_h) or pd.isna(att_h) or max_h == 0:
                margins.append("N/A"); statuses.append("N/A"); continue
            pct = (att_h / max_h) * 100
            if pct >= target_val:
                margin = int((att_h - dec * max_h) / dec)
                margins.append(f"+{margin} classes (Can Skip)")
                statuses.append("🟢 Safe")
            else:
                req = int(((dec * max_h) - att_h) / (1.0 - dec)) + 1
                margins.append(f"-{req} classes (Shortage)")
                statuses.append("🔴 Danger")
        df[f'{target_val}% Margin'] = margins
        df['Status'] = statuses
    return df

subject_df = parse_and_process_attendance(target_pct)

# --- NAVIGATION TABS ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "📊 Attendance & Margins", 
    "📅 Complete Daily Timetable", 
    "📁 Subject Notes & Units Vault", 
    "📚 Syllabus & Question Bank",
    "🧠 Nirmal AI Optimizer",
    "🚀 Marks, CA3 & CGPA Calculator",
    "🤖 AI O-Grade Predictor",
    "📜 PYQ Vault & AI Generator"
])

# --- TAB 1: ATTENDANCE & MARGIN SECTION ---
with tab1:
    st.subheader("📊 SRM Attendance Percentages & Bunk Margins")
    if subject_df is not None:
        if 'Max. hours' in subject_df.columns and 'Att. hours' in subject_df.columns:
            total_max = int(subject_df['Max. hours'].dropna().sum())
            total_att = int(subject_df['Att. hours'].dropna().sum())
            overall_pct = (total_att / total_max) * 100 if total_max > 0 else 0
            overall_margin = int((total_att - (target_pct/100.0) * total_max) / (target_pct/100.0))

            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Total Attended Hours", f"{total_att} / {total_max} hrs")
            c2.metric("Overall Attendance %", f"{overall_pct:.2f}%")
            c3.metric(f"Overall Safety Margin ({target_pct}%)", f"+{overall_margin} hrs" if overall_margin >= 0 else f"{overall_margin} hrs")
            c4.metric("Attendance Guard", "🟢 Safe Buffer Active" if overall_pct >= target_pct else "🔴 Shortage Alert")

            st.divider()

        st.markdown("### 📋 Subject-Wise Attendance Details")
        st.dataframe(subject_df, use_container_width=True)

        st.divider()
        st.subheader("🔮 Interactive Bunk & Attendance Simulator")
        sim_col1, sim_col2, sim_col3 = st.columns(3)
        with sim_col1:
            subject_options = subject_df['Description'].tolist() if 'Description' in subject_df.columns else subject_df['Code'].tolist()
            chosen_sub = st.selectbox("Select Subject for Simulation", subject_options)
        with sim_col2:
            simulation_action = st.radio("Action Type", ["Skip Classes (Bunk)", "Attend Classes (Recovery)"], horizontal=True)
        with sim_col3:
            num_classes = st.number_input("Number of Classes", min_value=1, max_value=20, value=2)

        if 'Description' in subject_df.columns:
            sub_row = subject_df[subject_df['Description'] == chosen_sub].iloc[0]
        else:
            sub_row = subject_df[subject_df['Code'] == chosen_sub].iloc[0]

        curr_max = float(sub_row['Max. hours'])
        curr_att = float(sub_row['Att. hours'])
        curr_pct = sub_row['Attendance %']

        if simulation_action == "Skip Classes (Bunk)":
            proj_max = curr_max + num_classes
            proj_att = curr_att
        else:
            proj_max = curr_max + num_classes
            proj_att = curr_att + num_classes

        proj_pct = round((proj_att / proj_max) * 100, 2) if proj_max > 0 else 0
        diff_pct = round(proj_pct - curr_pct, 2)

        res_col1, res_col2, res_col3 = st.columns(3)
        res_col1.metric("Current Attendance", f"{curr_pct}%", f"{int(curr_att)}/{int(curr_max)} hrs")
        res_col2.metric("Projected Attendance", f"{proj_pct}%", f"{diff_pct}%", delta_color="normal" if proj_pct >= target_pct else "inverse")
        
        if proj_pct >= target_pct:
            res_col3.metric("Projected Status", "🟢 Safe Zone", f"Above {target_pct}% target")
        else:
            res_col3.metric("Projected Status", "🔴 Shortage Risk", f"Falls below {target_pct}% target")

    else:
        st.info("👈 Enter your SRM NetID and Password in the sidebar, then click **Fetch Real-Time Attendance** to sync live attendance.")

# --- TAB 2: COMPLETE DAILY TIMETABLE SECTION ---
with tab2:
    st.subheader("📅 Complete Daily Master Timetable")
    
    # Auto-fallback to current date if selected date not explicitly matching calendar
    cal_info = ACADEMIC_CALENDAR.get(selected_date, ACADEMIC_CALENDAR.get(date(2026, 10, 15)))
    
    col_d1, col_d2, col_d3 = st.columns(3)
    col_d1.metric("Selected Date", selected_date.strftime("%d %b %Y"))
    col_d2.metric("Day Status & Week", f"{cal_info['type']} ({cal_info['week']})")
    col_d3.metric("Assigned Schedule", cal_info["schedule"])

    if cal_info["event"] != "Normal Working Day":
        st.info(f"🎉 **Special Note / Event:** {cal_info['event']}")

    st.markdown(f"### 🕒 Complete Routine Breakdown ({cal_info['schedule']})")
    routine_key = cal_info["schedule"]
    routine_data = MASTER_SCHEDULES.get(routine_key, MASTER_SCHEDULES["Holiday / Weekend"])
    st.dataframe(pd.DataFrame(routine_data), use_container_width=True)

    st.divider()
    st.subheader("🎯 End-Semester Exam Timetable (December 2026)")
    st.dataframe(pd.DataFrame(END_SEM_EXAMS), use_container_width=True)

# --- TAB 3: SUBJECT NOTES & UNITS VAULT ---
with tab3:
    st.subheader("📁 Structured Notes & Units Vault (`~/Documents/SRM_Notes_Drive`)")
    st.caption("Organized folder structure: Each subject contains 5 Units + Syllabus/Lesson Plan.")

    v_col1, v_col2, v_col3 = st.columns(3)
    with v_col1:
        vault_subj = st.selectbox("Select Subject", SUBJECT_CODES, key="v_s")
    with v_col2:
        folder_target = st.selectbox("Target Folder", ["Syllabus_and_Lesson_Plan", "Unit_1", "Unit_2", "Unit_3", "Unit_4", "Unit_5"], key="v_f")
    with v_col3:
        vault_file = st.file_uploader("Upload Notes / Lesson Plan (PDF, TXT, PNG, JPG)", type=["pdf", "txt", "png", "jpg", "jpeg"], key="v_up")

    if vault_file and st.button("💾 Save File to Folder"):
        save_path = os.path.join(DRIVE_FOLDER, vault_subj, folder_target, vault_file.name)
        with open(save_path, "wb") as f:
            f.write(vault_file.getbuffer())
        st.success(f"Successfully saved to: `{save_path}`")
        st.rerun()

    st.markdown("### 📂 Stored Folder Explorer:")
    folder_contents = []
    subj_path = os.path.join(DRIVE_FOLDER, vault_subj)
    if os.path.exists(subj_path):
        for root, dirs, files in os.walk(subj_path):
            rel_folder = os.path.relpath(root, subj_path)
            if "PYQs" not in rel_folder:
                for f in files:
                    folder_contents.append({"Folder": rel_folder, "File Name": f})
    if folder_contents:
        st.dataframe(pd.DataFrame(folder_contents), use_container_width=True)
    else:
        st.info("No files uploaded in this subject folder hierarchy yet.")

# --- TAB 4: SYLLABUS TRACKER & QUESTION BANK ---
with tab4:
    st.subheader("📚 Dynamic Exam Preparation & Syllabus Tracker")
    st.caption("Track unit topics across all 5 subjects.")

    total_topics_all = 0
    completed_topics_all = 0
    subject_progress_data = {}

    for subj, units in syllabus_state.items():
        subj_total = 0
        subj_completed = 0
        for unit, topics in units.items():
            for t_name, t_val in topics.items():
                subj_total += 1
                total_topics_all += 1
                if t_val:
                    subj_completed += 1
                    completed_topics_all += 1
        subject_progress_data[subj] = (subj_completed / subj_total) if subj_total > 0 else 0.0

    master_pct = int((completed_topics_all / total_topics_all) * 100) if total_topics_all > 0 else 0
    master_ratio = min(1.0, max(0.0, completed_topics_all / total_topics_all)) if total_topics_all > 0 else 0.0

    st.markdown("### 🌟 Overall Master Syllabus Progress")
    st.progress(master_ratio, text=f"Master Completion: {master_pct}% ({completed_topics_all}/{total_topics_all} Topics Completed)")
    st.divider()

    st.markdown("### 📖 Subject-Wise Unified Progress")
    cols = st.columns(len(subject_progress_data))
    for idx, (subj, pct) in enumerate(subject_progress_data.items()):
        with cols[idx]:
            st.metric(label=subj, value=f"{int(pct * 100)}%")
            st.progress(min(1.0, max(0.0, pct)))

    st.divider()
    st.markdown("### 📝 Unit-Wise Topic Checklist")

    updated = False
    for subj, units in syllabus_state.items():
        with st.expander(f"📌 Subject: {subj}", expanded=True):
            for unit_name, topics in units.items():
                u_total = len(topics)
                u_comp = sum(1 for v in topics.values() if v)
                u_ratio = (u_comp / u_total) if u_total > 0 else 0.0

                st.markdown(f"**{unit_name}** ({u_comp}/{u_total} completed)")
                st.progress(min(1.0, max(0.0, u_ratio)))

                col_topics = st.columns(2)
                for t_idx, (topic_name, status) in enumerate(topics.items()):
                    with col_topics[t_idx % 2]:
                        new_status = st.checkbox(topic_name, value=status, key=f"chk_{subj}_{unit_name}_{topic_name}")
                        if new_status != status:
                            syllabus_state[subj][unit_name][topic_name] = new_status
                            updated = True
                st.write("")

    if updated:
        save_syllabus_progress(syllabus_state)
        st.rerun()

    st.divider()
    st.subheader("🎯 Targeted Notes Exam Question Generator")
    gen_col1, gen_col2 = st.columns(2)
    with gen_col1:
        selected_gen_subj = st.selectbox("Select Subject for Generation", list(syllabus_state.keys()), key="gen_sub_notes")
    with gen_col2:
        question_type = st.selectbox("Select Question Category", [
            "MCQs (Concept Strengthening)", 
            "2-Markers (Short Answer)", 
            "4-Markers (Medium Answer)", 
            "12-Markers (Long Answer / Code / Derivation)"
        ], key="gen_qtype_notes")

    if st.button("🚀 Generate Targeted Questions from Notes Vault"):
        completed_list = []
        for u_name, t_dict in syllabus_state[selected_gen_subj].items():
            for t_name, t_status in t_dict.items():
                if t_status:
                    completed_list.append(f"[{u_name}] {t_name}")

        if not completed_list:
            st.warning("⚠️ You haven't ticked any completed topics for this subject yet!")
        else:
            with st.spinner(f"Generating {question_type} for completed topics in {selected_gen_subj}..."):
                api_success = False
                response_text = ""
                
                if PERMANENT_GEMINI_KEY and PERMANENT_GEMINI_KEY != "YOUR_ACTUAL_API_KEY":
                    try:
                        genai.configure(api_key=PERMANENT_GEMINI_KEY)
                        model = genai.GenerativeModel('gemini-3.8-flash')
                        completed_str = "\n".join([f"- {item}" for item in completed_list])
                        prompt = f"""
                        You are an expert professor and question paper setter for SRMIST 1st-year B.Tech CSE (AI/ML).
                        Subject Code: {selected_gen_subj}
                        Question Category Requested: {question_type}
                        Completed Topics: {completed_str}
                        Generate 4-5 high-yield exam questions.
                        """
                        res = model.generate_content(prompt)
                        response_text = res.text
                        api_success = True
                    except Exception:
                        api_success = False

                if not api_success:
                    response_text = generate_offline_fallback_questions(selected_gen_subj, question_type, completed_list)

                st.markdown(f"### 📋 Generated {question_type} — {selected_gen_subj}")
                st.markdown(response_text)

# --- TAB 5: NIRMAL AI OPTIMIZER ---
with tab5:
    st.subheader("🧠 Nirmal AI: Autonomous Leave & Exam Optimizer")
    col_a, col_b = st.columns(2)
    with col_a:
        leave_logged_today = st.checkbox("I took leave / missed classes today")
        leave_reason = st.text_input("Reason / Notes for Leave (optional)", placeholder="e.g., preparing for exam or unwell")
    with col_b:
        focus_goal = st.selectbox("Primary Focus for Today's Leave / Free Time", ["Master C / PPS Coding", "Calculus & Linear Algebra Problem Solving", "Computational Biology Revision", "General End-Sem Sprint"])

    if st.button("🚀 Run Autonomous AI Decision & Timetable Generator"):
        att_summary = subject_df.to_string() if subject_df is not None else "No live attendance data synced yet."
        
        with st.spinner("Nirmal AI is analyzing margins, OCR vault notes, and schedules..."):
            api_success = False
            ai_output = ""

            if PERMANENT_GEMINI_KEY and PERMANENT_GEMINI_KEY != "YOUR_ACTUAL_API_KEY":
                try:
                    genai.configure(api_key=PERMANENT_GEMINI_KEY)
                    model = genai.GenerativeModel('gemini-3.8-flash')

                    prompt = f"""
                    You are Nirmal AI, an elite autonomous academic collaborator for a 1st-year B.Tech CSE (AI/ML) student at SRMIST.
                    Date: {selected_date.strftime('%d %B %Y')}
                    Attendance: {att_summary}
                    User Leave Status: {"YES" if leave_logged_today else "NO"} ({leave_reason})
                    Focus Goal: {focus_goal}
                    Provide a structured leave audit and hourly timetable.
                    """
                    res = model.generate_content(prompt)
                    ai_output = res.text
                    api_success = True
                except Exception:
                    api_success = False

            if not api_success:
                ai_output = f"### 🎯 Nirmal AI: Strategy\n1. Attendance Buffer: Safe.\n2. Focus Schedule ({focus_goal}):\n- 08:00 AM - 11:00 AM: Focus Revision\n- 02:00 PM - 05:00 PM: Practice PYQs\n- 07:00 PM - 09:00 PM: Review Notes."

            st.markdown("### 🎯 Nirmal AI Strategic Output")
            st.markdown(ai_output)

# --- TAB 6: MARKS, CA3 & CGPA CALCULATOR ---
with tab6:
    st.subheader("🚀 Complete Academic Marks, CA3 (End-Sem) & CGPA Engine")
    st.caption("Your entered marks are saved automatically to `~/Documents/SRM_Notes_Drive/user_marks.json` and persist across page reloads.")

    st.markdown("### 🧮 Comprehensive Marks Input (CA1, CA2, CA3 / End-Sem)")
    
    exam_calc_tabs = st.tabs(["📝 CA1 Input", "📝 CA2 Input", "📝 CA3 / End-Sem Input", "📊 Consolidated Scorecard & CGPA"])
    
    with exam_calc_tabs[0]:
        st.markdown("#### Enter Raw CA1 Marks")
        c1_1, c1_2 = st.columns(2)
        with c1_1:
            maths_th_ca1 = st.number_input("Maths Theory (Max 50)", 0.0, 50.0, float(saved_marks.get("m_th_1", 35.0)), key="m_th_1")
            maths_pr_ca1 = st.number_input("Maths Practical (Max 30)", 0.0, 30.0, float(saved_marks.get("m_pr_1", 22.0)), key="m_pr_1")
            bio_th_ca1 = st.number_input("Biology Theory (Max 50)", 0.0, 50.0, float(saved_marks.get("b_th_1", 38.0)), key="b_th_1")
            bio_pr_ca1 = st.number_input("Biology Practical (Max 5)", 0.0, 5.0, float(saved_marks.get("b_pr_1", 4.0)), key="b_pr_1")
            span_th_ca1 = st.number_input("Spanish Theory (Max 50)", 0.0, 50.0, float(saved_marks.get("s_th_1", 40.0)), key="s_th_1")
            span_pr_ca1 = st.number_input("Spanish Practical (Max 5)", 0.0, 5.0, float(saved_marks.get("s_pr_1", 4.5)), key="s_pr_1")
        with c1_2:
            pps_th_ca1 = st.number_input("Programming / PPS Theory (Max 40)", 0.0, 40.0, float(saved_marks.get("pps_th_1", 30.0)), key="pps_th_1")
            pps_pr_ca1 = st.number_input("Programming / PPS Practical (Max 15)", 0.0, 15.0, float(saved_marks.get("pps_pr_1", 12.0)), key="pps_pr_1")
            chem_th_ca1 = st.number_input("Chemistry Theory (Max 30)", 0.0, 30.0, float(saved_marks.get("c_th_1", 24.0)), key="c_th_1")
            chem_pr_ca1 = st.number_input("Chemistry Practical (Max 40)", 0.0, 40.0, float(saved_marks.get("c_pr_1", 32.0)), key="c_pr_1")
            nss_ca1 = st.number_input("NSS (Max 30)", 0.0, 30.0, float(saved_marks.get("nss_1", 25.0)), key="nss_1")
            ws_ca1 = st.number_input("Workshop (Max 120)", 0.0, 120.0, float(saved_marks.get("ws_1", 100.0)), key="ws_1")

        # Conversions CA1
        m_conv_1 = (maths_th_ca1 / 50.0 * 15.0) + (maths_pr_ca1 / 30.0 * 5.0)
        b_conv_1 = (bio_th_ca1 / 50.0 * 15.0) + (bio_pr_ca1 / 5.0 * 5.0)
        s_conv_1 = (span_th_ca1 / 50.0 * 15.0) + (span_pr_ca1 / 5.0 * 5.0)
        pps_conv_1 = (pps_th_ca1 / 40.0 * 15.0) + (pps_pr_ca1 / 15.0 * 5.0)
        chem_conv_1 = (chem_th_ca1 / 30.0 * 10.0) + (chem_pr_ca1 / 40.0 * 15.0)
        nss_conv_1 = (nss_ca1 / 30.0 * 20.0)
        ws_conv_1 = (ws_ca1 / 120.0 * 50.0)

    with exam_calc_tabs[1]:
        st.markdown("#### Enter Raw CA2 Marks")
        c2_1, c2_2 = st.columns(2)
        with c2_1:
            maths_th_ca2 = st.number_input("Maths Theory (Max 50)", 0.0, 50.0, float(saved_marks.get("m_th_2", 38.0)), key="m_th_2")
            maths_pr_ca2 = st.number_input("Maths Practical (Max 30)", 0.0, 30.0, float(saved_marks.get("m_pr_2", 25.0)), key="m_pr_2")
            bio_th_ca2 = st.number_input("Biology Theory (Max 50)", 0.0, 50.0, float(saved_marks.get("b_th_2", 42.0)), key="b_th_2")
            bio_pr_ca2 = st.number_input("Biology Practical (Max 5)", 0.0, 5.0, float(saved_marks.get("b_pr_2", 5.0)), key="b_pr_2")
            span_th_ca2 = st.number_input("Spanish Theory (Max 50)", 0.0, 50.0, float(saved_marks.get("s_th_2", 44.0)), key="s_th_2")
            span_pr_ca2 = st.number_input("Spanish Practical (Max 5)", 0.0, 5.0, float(saved_marks.get("s_pr_2", 5.0)), key="s_pr_2")
        with c2_2:
            pps_th_ca2 = st.number_input("Programming / PPS Theory (Max 40)", 0.0, 40.0, float(saved_marks.get("pps_th_2", 32.0)), key="pps_th_2")
            pps_pr_ca2 = st.number_input("Programming / PPS Practical (Max 15)", 0.0, 15.0, float(saved_marks.get("pps_pr_2", 13.0)), key="pps_pr_2")
            chem_th_ca2 = st.number_input("Chemistry Theory (Max 30)", 0.0, 30.0, float(saved_marks.get("c_th_2", 26.0)), key="c_th_2")
            chem_pr_ca2 = st.number_input("Chemistry Practical (Max 40)", 0.0, 40.0, float(saved_marks.get("c_pr_2", 35.0)), key="c_pr_2")
            nss_ca2 = st.number_input("NSS (Max 30)", 0.0, 30.0, float(saved_marks.get("nss_2", 28.0)), key="nss_2")
            ws_ca2 = st.number_input("Workshop (Max 120)", 0.0, 120.0, float(saved_marks.get("ws_2", 110.0)), key="ws_2")

        # Conversions CA2
        m_conv_2 = (maths_th_ca2 / 50.0 * 15.0) + (maths_pr_ca2 / 30.0 * 5.0)
        b_conv_2 = (bio_th_ca2 / 50.0 * 15.0) + (bio_pr_ca2 / 5.0 * 5.0)
        s_conv_2 = (span_th_ca2 / 50.0 * 15.0) + (span_pr_ca2 / 5.0 * 5.0)
        pps_conv_2 = (pps_th_ca2 / 40.0 * 15.0) + (pps_pr_ca2 / 15.0 * 7.5)
        chem_conv_2 = (chem_th_ca2 / 30.0 * 10.0) + (chem_pr_ca2 / 40.0 * 15.0)
        nss_conv_2 = (nss_ca2 / 30.0 * 20.0)
        ws_conv_2 = (ws_ca2 / 120.0 * 50.0)

    with exam_calc_tabs[2]:
        st.markdown("#### Enter Raw CA3 / End-Sem Marks")
        c3_1, c3_2 = st.columns(2)
        with c3_1:
            maths_th_ca3 = st.number_input("Maths Theory (Max 100)", 0.0, 100.0, float(saved_marks.get("m_th_3", 80.0)), key="m_th_3")
            maths_pr_ca3 = st.number_input("Maths Practical (Max 10)", 0.0, 10.0, float(saved_marks.get("m_pr_3", 8.5)), key="m_pr_3")
            bio_th_ca3 = st.number_input("Biology Theory (Max 100)", 0.0, 100.0, float(saved_marks.get("b_th_3", 85.0)), key="b_th_3")
            bio_pr_ca3 = st.number_input("Biology Practical (Max 10)", 0.0, 10.0, float(saved_marks.get("b_pr_3", 9.0)), key="b_pr_3")
            span_th_ca3 = st.number_input("Spanish Theory (Max 100)", 0.0, 100.0, float(saved_marks.get("s_th_3", 88.0)), key="s_th_3")
            span_pr_ca3 = st.number_input("Spanish Practical (Max 10)", 0.0, 10.0, float(saved_marks.get("s_pr_3", 9.5)), key="s_pr_3")
        with c3_2:
            pps_th_ca3 = st.number_input("Programming / PPS Theory (Max 75)", 0.0, 75.0, float(saved_marks.get("pps_th_3", 60.0)), key="pps_th_3")
            pps_pr_ca3 = st.number_input("Programming / PPS Practical (Max 15)", 0.0, 15.0, float(saved_marks.get("pps_pr_3", 13.0)), key="pps_pr_3")
            chem_th_ca3 = st.number_input("Chemistry Theory (Max 75)", 0.0, 75.0, float(saved_marks.get("c_th_3", 58.0)), key="c_th_3")
            chem_pr_ca3 = st.number_input("Chemistry Practical (Max 0 - N/A)", 0.0, 0.0, 0.0, key="c_pr_3")

        # Conversions CA3
        m_conv_3 = (maths_th_ca3 / 100.0 * 50.0) + (maths_pr_ca3 / 10.0 * 10.0)
        b_conv_3 = (bio_th_ca3 / 100.0 * 50.0) + (bio_pr_ca3 / 10.0 * 10.0)
        s_conv_3 = (span_th_ca3 / 100.0 * 50.0) + (span_pr_ca3 / 10.0 * 10.0)
        pps_conv_3 = (pps_th_ca3 / 75.0 * 50.0) + (pps_pr_ca3 / 15.0 * 7.5)
        chem_conv_3 = (chem_th_ca3 / 75.0 * 50.0) + 0.0

    # Auto Save Current Marks State
    current_marks_state = {
        "m_th_1": maths_th_ca1, "m_pr_1": maths_pr_ca1, "b_th_1": bio_th_ca1, "b_pr_1": bio_pr_ca1,
        "s_th_1": span_th_ca1, "s_pr_1": span_pr_ca1, "pps_th_1": pps_th_ca1, "pps_pr_1": pps_pr_ca1,
        "c_th_1": chem_th_ca1, "c_pr_1": chem_pr_ca1, "nss_1": nss_ca1, "ws_1": ws_ca1,
        "m_th_2": maths_th_ca2, "m_pr_2": maths_pr_ca2, "b_th_2": bio_th_ca2, "b_pr_2": bio_pr_ca2,
        "s_th_2": span_th_ca2, "s_pr_2": span_pr_ca2, "pps_th_2": pps_th_ca2, "pps_pr_2": pps_pr_ca2,
        "c_th_2": chem_th_ca2, "c_pr_2": chem_pr_ca2, "nss_2": nss_ca2, "ws_2": ws_ca2,
        "m_th_3": maths_th_ca3, "m_pr_3": maths_pr_ca3, "b_th_3": bio_th_ca3, "b_pr_3": bio_pr_ca3,
        "s_th_3": span_th_ca3, "s_pr_3": span_pr_ca3, "pps_th_3": pps_th_ca3, "pps_pr_3": pps_pr_ca3,
        "c_th_3": chem_th_ca3
    }
    save_marks(current_marks_state)

    with exam_calc_tabs[3]:
        st.markdown("#### 📊 Consolidated Marks & Final CGPA Engine")
        
        maths_total = m_conv_1 + m_conv_2 + m_conv_3
        bio_total = b_conv_1 + b_conv_2 + b_conv_3
        span_total = s_conv_1 + s_conv_2 + s_conv_3
        pps_total = pps_conv_1 + pps_conv_2 + pps_conv_3
        chem_total = chem_conv_1 + chem_conv_2 + chem_conv_3

        def get_grade_point(total_score):
            if total_score >= 90: return ("O", 10)
            elif total_score >= 80: return ("A+", 9)
            elif total_score >= 70: return ("A", 8)
            elif total_score >= 60: return ("B+", 7)
            elif total_score >= 50: return ("B", 6)
            elif total_score >= 45: return ("C", 5)
            elif total_score >= 40: return ("P", 4)
            else: return ("F", 0)

        courses = [
            {"Code": "26MAB1001T", "Name": "Calculus & Linear Algebra", "Credits": 4, "CA1": m_conv_1, "CA2": m_conv_2, "CA3": m_conv_3, "Total": maths_total},
            {"Code": "26CSE1002J", "Name": "Programming for Problem Solving", "Credits": 4, "CA1": pps_conv_1, "CA2": pps_conv_2, "CA3": pps_conv_3, "Total": pps_total},
            {"Code": "26CYB1002J", "Name": "Chemistry for Computer Science", "Credits": 4, "CA1": chem_conv_1, "CA2": chem_conv_2, "CA3": chem_conv_3, "Total": chem_total},
            {"Code": "26BTB1001T", "Name": "Computational Biology", "Credits": 2, "CA1": b_conv_1, "CA2": b_conv_2, "CA3": b_conv_3, "Total": bio_total},
            {"Code": "26LCA1007J", "Name": "Spanish", "Credits": 2, "CA1": s_conv_1, "CA2": s_conv_2, "CA3": s_conv_3, "Total": span_total},
        ]

        summary_rows = []
        tot_qp = 0
        tot_cr = 0

        for c in courses:
            g_str, g_pts = get_grade_point(c["Total"])
            tot_qp += g_pts * c["Credits"]
            tot_cr += c["Credits"]
            summary_rows.append({
                "Subject": f"{c['Name']} ({c['Code']})",
                "Credits": c["Credits"],
                "CA1": round(c["CA1"], 2),
                "CA2": round(c["CA2"], 2),
                "CA3 (End-Sem)": round(c["CA3"], 2),
                "Final Marks (/100)": round(c["Total"], 2),
                "Grade": g_str,
                "Grade Points": g_pts
            })

        final_cgpa = round(tot_qp / tot_cr, 2) if tot_cr > 0 else 0.0

        st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)
        st.divider()
        st.metric("🎓 Exact Calculated Semester CGPA", f"{final_cgpa} / 10.0", f"Total Credits: {tot_cr}")

# --- TAB 7: AI O-GRADE PREDICTOR & TARGETER ---
with tab7:
    st.subheader("🤖 AI O-Grade Target Predictor")
    st.caption("Enter your CA1 marks below (leave CA2 and CA3 as 0 if they haven't occurred yet).")

    st.markdown("#### Enter Your Current CA1 Raw Marks")
    pred_col1, pred_col2 = st.columns(2)
    with pred_col1:
        p_maths_th = st.number_input("Maths Theory CA1 (Max 50)", 0.0, 50.0, float(saved_marks.get("m_th_1", 40.0)), key="p_m_th")
        p_maths_pr = st.number_input("Maths Practical CA1 (Max 30)", 0.0, 30.0, float(saved_marks.get("m_pr_1", 25.0)), key="p_m_pr")
        p_bio_th = st.number_input("Biology Theory CA1 (Max 50)", 0.0, 50.0, float(saved_marks.get("b_th_1", 42.0)), key="p_b_th")
        p_bio_pr = st.number_input("Biology Practical CA1 (Max 5)", 0.0, 5.0, float(saved_marks.get("b_pr_1", 5.0)), key="p_b_pr")
        p_span_th = st.number_input("Spanish Theory CA1 (Max 50)", 0.0, 50.0, float(saved_marks.get("s_th_1", 45.0)), key="p_s_th")
        p_span_pr = st.number_input("Spanish Practical CA1 (Max 5)", 0.0, 5.0, float(saved_marks.get("s_pr_1", 5.0)), key="p_s_pr")
    with pred_col2:
        p_pps_th = st.number_input("PPS Theory CA1 (Max 40)", 0.0, 40.0, float(saved_marks.get("pps_th_1", 35.0)), key="p_pps_th")
        p_pps_pr = st.number_input("PPS Practical CA1 (Max 15)", 0.0, 15.0, float(saved_marks.get("pps_pr_1", 13.0)), key="p_pps_pr")
        p_chem_th = st.number_input("Chemistry Theory CA1 (Max 30)", 0.0, 30.0, float(saved_marks.get("c_th_1", 26.0)), key="p_chem_th")
        p_chem_pr = st.number_input("Chemistry Practical CA1 (Max 40)", 0.0, 40.0, float(saved_marks.get("c_pr_1", 35.0)), key="p_chem_pr")

    if st.button("🔮 Run AI O-Grade Gap & Target Analysis"):
        m_c1 = (p_maths_th / 50.0 * 15.0) + (p_maths_pr / 30.0 * 5.0)
        b_c1 = (p_bio_th / 50.0 * 15.0) + (p_bio_pr / 5.0 * 5.0)
        s_c1 = (p_span_th / 50.0 * 15.0) + (p_span_pr / 5.0 * 5.0)
        pps_c1 = (p_pps_th / 40.0 * 15.0) + (p_pps_pr / 15.0 * 5.0)
        chem_c1 = (p_chem_th / 30.0 * 10.0) + (p_chem_pr / 40.0 * 15.0)

        with st.spinner("AI is computing precise target marks for O Grade (90+)..."):
            api_success = False
            ai_prediction_text = ""

            if PERMANENT_GEMINI_KEY and PERMANENT_GEMINI_KEY != "YOUR_ACTUAL_API_KEY":
                try:
                    genai.configure(api_key=PERMANENT_GEMINI_KEY)
                    model = genai.GenerativeModel('gemini-3.8-flash')
                    prompt = f"""
                    Calculate remaining marks needed out of 100 to get O grade (90+) Calculate predicted final marks based on current CA1 scores. Provide a roadmap for each subject to achieve O grade., calculate the remaining marks needed in CA2 and CA3 to achieve O grade. Current CA1 scores are:
                    - Maths: CA1={m_c1:.2f}
                    - PPS: CA1={pps_c1:.2f}
                    - Chemistry: CA1={chem_c1:.2f}
                    - Bio: CA1={b_c1:.2f}
                    - Spanish: CA1={s_c1:.2f}
                    maths marks are out of 20, PPS out of 20, Chemistry out of 25, Bio out of 20, Spanish out of 20. Provide a clear roadmap for each subject to achieve O grade.
                    """
                    res = model.generate_content(prompt)
                    ai_prediction_text = res.text
                    api_success = True
                except Exception:
                    api_success = False

            if not api_success:
                ai_prediction_text = f"""### 🎯 AI O-Grade Target Roadmap
1. **Calculus & Linear Algebra:** CA1: {m_c1:.2f}/20 | Remaining Needed: {max(0.0, 90.0 - m_c1):.2f} marks
2. **PPS Programming:** CA1: {pps_c1:.2f}/20 | Remaining Needed: {max(0.0, 90.0 - pps_c1):.2f} marks
3. **Chemistry:** CA1: {chem_c1:.2f}/25 | Remaining Needed: {max(0.0, 90.0 - chem_c1):.2f} marks
4. **Biology:** CA1: {b_c1:.2f}/20 | Remaining Needed: {max(0.0, 90.0 - b_c1):.2f} marks
5. **Spanish:** CA1: {s_c1:.2f}/20 | Remaining Needed: {max(0.0, 90.0 - s_c1):.2f} marks
"""

        st.markdown("### 📋 AI Predicted O-Grade Roadmap")
        st.markdown(ai_prediction_text)

# --- TAB 8: PYQ VAULT & AI GENERATOR ---
with tab8:
    st.subheader("📜 PYQ Vault & Auto-Question Generator from Completed Topics")
    st.caption("Upload Previous Year Question Papers (PYQs) and auto-generate exam questions directly from your ticked/completed topics.")

    pyq_sub1, pyq_sub2 = st.columns(2)
    with pyq_sub1:
        pyq_subj = st.selectbox("Select Subject", SUBJECT_CODES, key="pyq_s")
    with pyq_sub2:
        pyq_file = st.file_uploader("Upload PYQ Paper (PDF or Image)", type=["pdf", "png", "jpg", "jpeg"], key="pyq_up")

    if pyq_file and st.button("💾 Upload PYQ to Vault"):
        pyq_save_dir = os.path.join(DRIVE_FOLDER, pyq_subj, "PYQs")
        os.makedirs(pyq_save_dir, exist_ok=True)
        pyq_path = os.path.join(pyq_save_dir, pyq_file.name)
        with open(pyq_path, "wb") as f:
            f.write(pyq_file.getbuffer())
        st.success(f"Saved PYQ to: `{pyq_path}`")
        st.rerun()

    st.markdown("### 📂 Stored PYQ Papers")
    pyq_dir = os.path.join(DRIVE_FOLDER, pyq_subj, "PYQs")
    if os.path.exists(pyq_dir) and os.listdir(pyq_dir):
        st.write(os.listdir(pyq_dir))
    else:
        st.info("No PYQ papers uploaded for this subject yet.")

    st.divider()
    st.markdown("### 🤖 Auto-Generate Questions from Ticked Completed Topics")

    # Fetch completed topics directly without making user select topics again
    auto_completed_topics = []
    for u_name, t_dict in syllabus_state.get(pyq_subj, {}).items():
        for t_name, t_status in t_dict.items():
            if t_status:
                auto_completed_topics.append(f"[{u_name}] {t_name}")

    if not auto_completed_topics:
        st.warning("⚠️ No topics are ticked as completed for this subject in Tab 4 (Syllabus Tracker). Tick topics there to enable auto question generation!")
    else:
        st.success(f"Found **{len(auto_completed_topics)} completed topics** for {pyq_subj}. Ready to generate!")
        
        pyq_qtype = st.selectbox("Select Question Style", [
            "2-Markers (Short PYQ Style)",
            "4-Markers (Medium Concept PYQ Style)",
            "12-Markers (Long Comprehensive PYQ Derivations/Code)",
            "MCQs (PYQ Style Pattern)"
        ], key="pyq_qtype")

        if st.button("⚡ Generate AI Exam Questions from Completed Topics"):
            with st.spinner("Analyzing PYQ vault and completed topics..."):
                api_success = False
                pyq_ai_text = ""

                if PERMANENT_GEMINI_KEY and PERMANENT_GEMINI_KEY != "YOUR_ACTUAL_API_KEY":
                    try:
                        genai.configure(api_key=PERMANENT_GEMINI_KEY)
                        model = genai.GenerativeModel('gemini-3.8-flash')
                        topics_formatted = "\n".join([f"- {t}" for t in auto_completed_topics])
                        prompt = f"""
                        You are an expert professor for SRMIST B.Tech CSE.
                        Subject: {pyq_subj}
                        Question Style: {pyq_qtype}
                        
                        Generate 5 university exam questions strictly from these completed syllabus topics:
                        {topics_formatted}
                        
                        Include answer keys and step-by-step solutions matching SRM exam marking rubrics.
                        """
                        res = model.generate_content(prompt)
                        pyq_ai_text = res.text
                        api_success = True
                    except Exception:
                        api_success = False

                if not api_success:
                    pyq_ai_text = generate_offline_fallback_questions(pyq_subj, pyq_qtype, auto_completed_topics)

                st.markdown("### 📋 Generated PYQ-Based Questions & Answer Key")
                st.markdown(pyq_ai_text)
