"""
seed_non_it_assessment.py
Creates and populates a second assessment with 20 high-quality questions mapped to the Non-IT JDs.
Format: 20 questions in 20 minutes (5 Basic, 5 Core Non-IT, 5 Medium, 5 Hard).
"""
import os
from app import create_app
from models.models import db, Assessment, Question

def seed_assessment():
    app = create_app()
    with app.app_context():
        # Delete existing Non-IT assessment, submissions, answers and questions to start fresh
        from models.models import Submission, Answer
        non_it_assessments = Assessment.query.filter(Assessment.title.like('%Non-IT%')).all()
        for old_a in non_it_assessments:
            subs = Submission.query.filter_by(assessment_id=old_a.id).all()
            for sub in subs:
                Answer.query.filter_by(submission_id=sub.id).delete()
                db.session.delete(sub)
            Question.query.filter_by(assessment_id=old_a.id).delete()
            db.session.delete(old_a)
        db.session.commit()

        # Create new assessment (inactive by default, toggle from admin)
        a = Assessment(
            title="Non-IT, Healthcare BPO & Operations Recruitment Drive",
            description=(
                "Assessment containing Aptitude & Verbal, Medical Coding, Medical Billing, "
                "Data Collection/Verification, AR & Telecalling, and Creative Content Creation. "
                "Contains 20 questions graded from Basic to Hard difficulty. Time limit: 20 minutes."
            ),
            duration=20,
            pass_percentage=50.0,
            status='inactive'
        )
        db.session.add(a)
        db.session.commit()

        questions = [
            # ─────────────────────────────────────────────────────────
            # BASIC (5 Questions)
            # ─────────────────────────────────────────────────────────
            {
                "question": "Basic Excel: Which basic Excel formula should you enter to calculate the sum of values from cell B2 to B10?",
                "option_a": "=ADD(B2:B10)",
                "option_b": "=SUM(B2:B10)",
                "option_c": "=TOTAL(B2:B10)",
                "option_d": "=B2+B10",
                "correct_answer": "B"
            },
            {
                "question": "Basic Medical Terminology: In healthcare terminology, what does the suffix '-itis' represent when added to a medical term (e.g., Bronchitis, Arthritis)?",
                "option_a": "Pain or headache",
                "option_b": "Inflammation or swelling",
                "option_c": "Cellular mutation",
                "option_d": "Surgical removal",
                "correct_answer": "B"
            },
            {
                "question": "Basic Telecalling: In BPO operations, what is the key difference between an Inbound call and an Outbound call?",
                "option_a": "Inbound calls are made by the agent; Outbound calls are received by the agent.",
                "option_b": "Inbound calls are received by the agent from customers; Outbound calls are initiated by the agent to customers.",
                "option_c": "Inbound calls use internet lines; Outbound calls use satellite lines.",
                "option_d": "There is no difference; they use the same scripts.",
                "correct_answer": "B"
            },
            {
                "question": "Basic Social Media: An AI Vlogging Creator is formatting a vertical video for Instagram Reels and YouTube Shorts. What is the standard aspect ratio recommended for these platforms?",
                "option_a": "16:9",
                "option_b": "9:16",
                "option_c": "1:1",
                "option_d": "4:3",
                "correct_answer": "B"
            },
            {
                "question": "Basic Data Collection: During data collection, what is the best practice to follow when encountering incomplete or blurry documents during verification?",
                "option_a": "Guess the missing digits to save processing time.",
                "option_b": "Flag the document as invalid and request re-upload or verification.",
                "option_c": "Delete the entry from the database permanently without logs.",
                "option_d": "Accept it temporarily and process the record.",
                "correct_answer": "B"
            },

            # ─────────────────────────────────────────────────────────
            # CORE NON-IT (5 Questions)
            # ─────────────────────────────────────────────────────────
            {
                "question": "Core Non-IT: What is the definition of an insurance 'Premium' in healthcare billing?",
                "option_a": "The maximum amount the patient pays for a visit.",
                "option_b": "The monthly or annual amount paid to the insurance company to keep the plan active.",
                "option_c": "The penalty charged for late claims submission.",
                "option_d": "A bonus paid to billing executives based on claim speed.",
                "correct_answer": "B"
            },
            {
                "question": "Core Non-IT: Which keyboard shortcut allows you to quickly paste copied data in MS Excel on Windows?",
                "option_a": "Ctrl + P",
                "option_b": "Ctrl + V",
                "option_c": "Ctrl + Alt + V",
                "option_d": "Ctrl + C",
                "correct_answer": "B"
            },
            {
                "question": "Core Non-IT: What is the main purpose of performing a 'KYC' (Know Your Customer) check during customer onboarding?",
                "option_a": "To check customer reviews about the service.",
                "option_b": "To verify the identity of the customer and prevent fraud or identity theft.",
                "option_c": "To calculate the net salary income of the applicant.",
                "option_d": "To document calling preferences.",
                "correct_answer": "B"
            },
            {
                "question": "Core Non-IT: Which AI tool is primarily used for generating realistic images or design assets from text descriptions?",
                "option_a": "ChatGPT",
                "option_b": "Midjourney / DALL-E",
                "option_c": "ElevenLabs",
                "option_d": "GitHub Copilot",
                "correct_answer": "B"
            },
            {
                "question": "Core Non-IT: When a customer is angry during a call, what is the best strategy a Telecaller should adopt?",
                "option_a": "Argue back to prove the company policy is correct.",
                "option_b": "Listen patiently, apologize for the inconvenience, and offer a logical solution.",
                "option_c": "Disconnect the call immediately.",
                "option_d": "Transfer the call to another agent without warning.",
                "correct_answer": "B"
            },

            # ─────────────────────────────────────────────────────────
            # MEDIUM (5 Questions)
            # ─────────────────────────────────────────────────────────
            {
                "question": "Medium Medical Coding: In medical coding, what is the primary difference between ICD codes and CPT codes?",
                "option_a": "ICD codes are for procedures; CPT codes are for diagnoses.",
                "option_b": "ICD codes classify diseases and diagnoses; CPT codes identify medical and procedural services performed.",
                "option_c": "ICD codes are for billing; CPT codes are for pharmacy orders.",
                "option_d": "There is no difference; they are released by the same agency.",
                "correct_answer": "B"
            },
            {
                "question": "Medium AR Calling: In Revenue Cycle Management (RCM), what does an 'EOB' (Explanation of Benefits) represent?",
                "option_a": "A certificate issued to certified medical coders.",
                "option_b": "A document sent by the insurance company explaining what was paid, denied, or adjusted on a claim.",
                "option_c": "An employee handbook detailing call rules.",
                "option_d": "A doctor's prescription layout.",
                "correct_answer": "B"
            },
            {
                "question": "Medium Excel: Which formula should you use to search for a value in the first column of a table array and return a value in the same row from another column?",
                "option_a": "=INDEX(MATCH())",
                "option_b": "=VLOOKUP()",
                "option_c": "=LOOKUP()",
                "option_d": "=HLOOKUP()",
                "correct_answer": "B"
            },
            {
                "question": "Medium AI Handcam: In an AI gesture data collection project, why is it critical to collect hand movements from diverse angles and lighting conditions?",
                "option_a": "To make the video content look more artistic.",
                "option_b": "To ensure the AI model generalizes well and can recognize gestures in real-world scenarios.",
                "option_c": "To decrease the dataset storage requirements.",
                "option_d": "To bypass operating system camera limits.",
                "correct_answer": "B"
            },
            {
                "question": "Medium Compliance: What is the main objective of the HIPAA regulation in US healthcare administration?",
                "option_a": "To regulate the salary standards of hospital doctors.",
                "option_b": "To protect patient medical records and other personal health information (PHI).",
                "option_c": "To dictate insurance coverage premiums limits.",
                "option_d": "To establish coding system updates schedules.",
                "correct_answer": "B"
            },

            # ─────────────────────────────────────────────────────────
            # HARD (5 Questions)
            # ─────────────────────────────────────────────────────────
            {
                "question": "Hard Medical Coding: What is the purpose of adding a 'Modifier' to a CPT code during the medical coding process?",
                "option_a": "To indicate the severity level of a patient's disease.",
                "option_b": "To provide extra information indicating a procedure was altered or performed on a specific body part without changing the CPT definition.",
                "option_c": "To change the payment tier to high-priority categories.",
                "option_d": "To override diagnosis validation errors.",
                "correct_answer": "B"
            },
            {
                "question": "Hard AR Calling: Which metric is the primary indicator of a billing team's efficiency in submitting clean, error-free claims to insurance companies?",
                "option_a": "First-Pass Yield / Clean Claim Rate",
                "option_b": "Average Hold Time (AHT)",
                "option_c": "Net collection rate",
                "option_d": "Outbound call count per agent",
                "correct_answer": "A"
            },
            {
                "question": "Hard Excel: Why is combining the `INDEX` and `MATCH` formulas often considered superior to using `VLOOKUP` alone in complex spreadsheets?",
                "option_a": "VLOOKUP runs slower and cannot look left (prior columns) without rearranging the dataset.",
                "option_b": "INDEX-MATCH does not require any parameters.",
                "option_c": "VLOOKUP can only search for numerical values.",
                "option_d": "INDEX-MATCH automatically sorts the rows.",
                "correct_answer": "A"
            },
            {
                "question": "Hard AI Vlogging: In scriptwriting using generative AI, which prompt engineering technique yields the most consistent tone and structured pacing for video reels?",
                "option_a": "Broad single-sentence prompts with no constraints.",
                "option_b": "Few-Shot prompting, providing a clear persona, target duration, and structural examples.",
                "option_c": "Copy-pasting dictionary definitions.",
                "option_d": "Using multiple languages inside the same prompt.",
                "correct_answer": "B"
            },
            {
                "question": "Hard Medical Billing: In insurance verification, what does the term 'Coordination of Benefits' (COB) refer to?",
                "option_a": "Coordinating scheduling between the patient and the physician.",
                "option_b": "Determining the payment responsibilities and sequence when a patient is covered by more than one health insurance plan.",
                "option_c": "Distributing commissions among billing department staff.",
                "option_d": "Arranging coding updates across hospital branches.",
                "correct_answer": "B"
            }
        ]

        # Insert questions
        for idx, q_data in enumerate(questions, 1):
            q = Question(
                assessment_id=a.id,
                question=q_data["question"],
                option_a=q_data["option_a"],
                option_b=q_data["option_b"],
                option_c=q_data["option_c"],
                option_d=q_data["option_d"],
                correct_answer=q_data["correct_answer"]
            )
            db.session.add(q)
        
        db.session.commit()
        print("OK - Re-seeded Non-IT assessment 'Non-IT, Healthcare BPO & Operations Recruitment Drive' with 20 questions (20 min limit)!")

if __name__ == '__main__':
    seed_assessment()
