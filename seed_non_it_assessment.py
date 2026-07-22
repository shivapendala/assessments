"""
seed_non_it_assessment.py
Creates and populates a second assessment with 20 basic questions for Non-IT roles.
Format: 20 questions in 20 minutes.
"""
import os
from app import create_app
from models.models import db, Assessment, Question

def seed_assessment():
    app = create_app()
    with app.app_context():
        # Delete existing Non-IT assessment, submissions, answers and questions to start fresh
        from models.models import Submission, Answer
        non_it_assessments = Assessment.query.filter(Assessment.title.contains('Non-IT')).all()
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
                "Assessment containing Aptitude & Verbal, Communication, Medical Billing Basics, "
                "Data Entry, Customer Support, and General Knowledge. "
                "Contains 20 basic questions. Time limit: 20 minutes."
            ),
            duration=20,
            pass_percentage=50.0,
            status='inactive'
        )
        db.session.add(a)
        db.session.commit()

        questions = [
            {
                "question": "Q1. What does BPO stand for?",
                "option_a": "Business Process Outsourcing",
                "option_b": "Business Plan Optimization",
                "option_c": "Basic Process Operations",
                "option_d": "Business Product Outsourcing",
                "correct_answer": "A"
            },
            {
                "question": "Q2. Which of the following is a correct email format?",
                "option_a": "john.doe@gmail",
                "option_b": "john.doe.gmail.com",
                "option_c": "john.doe@gmail.com",
                "option_d": "@john.doe.gmail.com",
                "correct_answer": "C"
            },
            {
                "question": "Q3. A patient's bill shows: Consultation ₹500, Lab Test ₹1200, Medicines ₹800. What is the total bill?",
                "option_a": "₹2,300",
                "option_b": "₹2,500",
                "option_c": "₹2,100",
                "option_d": "₹2,000",
                "correct_answer": "B"
            },
            {
                "question": "Q4. What is the full form of OPD in healthcare?",
                "option_a": "Out Patient Department",
                "option_b": "Operational Patient Division",
                "option_c": "Out Patient Discharge",
                "option_d": "Optional Patient Data",
                "correct_answer": "A"
            },
            {
                "question": "Q5. Which Excel formula is used to calculate the sum of values from cells A1 to A10?",
                "option_a": "=ADD(A1:A10)",
                "option_b": "=TOTAL(A1:A10)",
                "option_c": "=SUM(A1:A10)",
                "option_d": "=A1+A10",
                "correct_answer": "C"
            },
            {
                "question": "Q6. What does 'AR' stand for in Medical Billing?",
                "option_a": "Account Receivable",
                "option_b": "Account Resolution",
                "option_c": "Annual Report",
                "option_d": "Active Record",
                "correct_answer": "A"
            },
            {
                "question": "Q7. A customer is angry on a call. What should you do first?",
                "option_a": "Hang up the call",
                "option_b": "Listen patiently and empathize",
                "option_c": "Argue back and defend yourself",
                "option_d": "Transfer the call immediately",
                "correct_answer": "B"
            },
            {
                "question": "Q8. Which of the following is NOT a common medical coding system?",
                "option_a": "ICD-10",
                "option_b": "CPT",
                "option_c": "HCPCS",
                "option_d": "PDF",
                "correct_answer": "D"
            },
            {
                "question": "Q9. If a data entry operator types 60 words per minute with 95% accuracy, how many correct words are typed in 10 minutes?",
                "option_a": "570",
                "option_b": "600",
                "option_c": "540",
                "option_d": "500",
                "correct_answer": "A"
            },
            {
                "question": "Q10. What is the correct way to address a patient/client over a professional call?",
                "option_a": "Hey! What do you want?",
                "option_b": "Good morning/afternoon! How may I help you?",
                "option_c": "What is the problem?",
                "option_d": "Call back later, we are busy.",
                "correct_answer": "B"
            },
            {
                "question": "Q11. In a data collection form, which field must always be unique for each patient record?",
                "option_a": "Date of Birth",
                "option_b": "Patient Name",
                "option_c": "Patient ID",
                "option_d": "City",
                "correct_answer": "C"
            },
            {
                "question": "Q12. Which key combination is used to copy selected text in a computer?",
                "option_a": "Ctrl + X",
                "option_b": "Ctrl + V",
                "option_c": "Ctrl + C",
                "option_d": "Ctrl + Z",
                "correct_answer": "C"
            },
            {
                "question": "Q13. If a claim is 'Denied' in medical billing, what is the next action?",
                "option_a": "Delete the patient record",
                "option_b": "Resubmit a corrected or appealed claim",
                "option_c": "Bill the patient immediately",
                "option_d": "Close the account",
                "correct_answer": "B"
            },
            {
                "question": "Q14. What does KPI stand for in operations/BPO?",
                "option_a": "Key Process Implementation",
                "option_b": "Key Performance Indicator",
                "option_c": "Knowledge Process Interface",
                "option_d": "Known Product Index",
                "correct_answer": "B"
            },
            {
                "question": "Q15. Which of the following is an example of PHI (Protected Health Information)?",
                "option_a": "A random medical textbook",
                "option_b": "A patient's name combined with their diagnosis",
                "option_c": "A general hospital brochure",
                "option_d": "Publicly available hospital ratings",
                "correct_answer": "B"
            },
            {
                "question": "Q16. In a typical night shift (10 PM – 6 AM), how many hours does an employee work?",
                "option_a": "6 hours",
                "option_b": "7 hours",
                "option_c": "8 hours",
                "option_d": "9 hours",
                "correct_answer": "C"
            },
            {
                "question": "Q17. Which insurance program in the US primarily covers patients aged 65 and above?",
                "option_a": "Medicaid",
                "option_b": "Medicare",
                "option_c": "COBRA",
                "option_d": "BlueCross",
                "correct_answer": "B"
            },
            {
                "question": "Q18. If a medical claim is submitted after the deadline, it is called:",
                "option_a": "Rejected claim",
                "option_b": "Late claim",
                "option_c": "Timely Filing Denial",
                "option_d": "Invalid claim",
                "correct_answer": "C"
            },
            {
                "question": "Q19. Which MS Office application is best suited for maintaining a patient appointment schedule?",
                "option_a": "MS Paint",
                "option_b": "MS Word",
                "option_c": "MS Excel",
                "option_d": "MS PowerPoint",
                "correct_answer": "C"
            },
            {
                "question": "Q20. What is HIPAA primarily concerned with?",
                "option_a": "Patient billing accuracy",
                "option_b": "Privacy and security of patient health information",
                "option_c": "Ensuring hospitals have enough staff",
                "option_d": "Tracking hospital expenses",
                "correct_answer": "B"
            }
        ]

        # Insert all 20 questions
        for q_data in questions:
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
        print("OK - Re-seeded Non-IT assessment 'Non-IT, Healthcare BPO & Operations Recruitment Drive' with 20 basic questions (20 min limit)!")

if __name__ == '__main__':
    seed_assessment()
