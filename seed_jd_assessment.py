"""
seed_jd_assessment.py
Creates and populates an assessment with 20 high-quality questions mapped to the IT recruitment drive JDs.
Format: 20 questions in 20 minutes.
"""
import os
from app import create_app
from models.models import db, Assessment, Question, Submission, Answer

def seed_assessment():
    app = create_app()
    with app.app_context():
        # Delete existing IT assessment, submissions, answers and questions to start fresh
        it_assessments = Assessment.query.filter(Assessment.title.contains('IT'), ~Assessment.title.contains('Non-IT')).all()
        for old_a in it_assessments:
            subs = Submission.query.filter_by(assessment_id=old_a.id).all()
            for sub in subs:
                Answer.query.filter_by(submission_id=sub.id).delete()
                db.session.delete(sub)
            Question.query.filter_by(assessment_id=old_a.id).delete()
            db.session.delete(old_a)
        db.session.commit()

        # Create new assessment
        a = Assessment(
            title="Comprehensive IT & Software Engineering Recruitment Drive",
            description=(
                "Assessment containing Aptitude & Reasoning, Python Programming, Java, "
                "SQL, Web Development, and Data Structures & Algorithms. Contains 20 questions "
                "graded from Basic to Hard difficulty. Time limit: 20 minutes."
            ),
            duration=20,
            pass_percentage=50.0,
            status='active'
        )
        db.session.add(a)
        db.session.commit()

        questions = [
            {
                "question": "Q1. A shopkeeper marks an item 40% above the cost price and gives a 10% discount. What is his profit percentage?",
                "option_a": "20%",
                "option_b": "24%",
                "option_c": "26%",
                "option_d": "30%",
                "correct_answer": "C"
            },
            {
                "question": "Q2. A can complete a work in 12 days, B in 18 days, and C in 36 days. If all three work together, how many days will they take?",
                "option_a": "4",
                "option_b": "5",
                "option_c": "5.5",
                "option_d": "6",
                "correct_answer": "D"
            },
            {
                "question": "Q3. Two dice are thrown together. What is the probability that the sum is at least 10?",
                "option_a": "1/6",
                "option_b": "1/4",
                "option_c": "5/36",
                "option_d": "7/36",
                "correct_answer": "A"
            },
            {
                "question": "Q4. ₹10,000 is invested at 10% per annum compounded annually for 2 years. The compound interest is:",
                "option_a": "₹2,000",
                "option_b": "₹2,100",
                "option_c": "₹2,200",
                "option_d": "₹2,250",
                "correct_answer": "B"
            },
            {
                "question": "Q5. A train 240 meters long crosses a pole in 12 seconds. What is its speed?",
                "option_a": "60 km/h",
                "option_b": "72 km/h",
                "option_c": "80 km/h",
                "option_d": "90 km/h",
                "correct_answer": "B"
            },
            {
                "question": "Q6. 3, 8, 15, 24, 35, 48, ?",
                "option_a": "61",
                "option_b": "63",
                "option_c": "64",
                "option_d": "72",
                "correct_answer": "B"
            },
            {
                "question": "Q7. ACE, BDF, CEG, ?",
                "option_a": "DFH",
                "option_b": "DEG",
                "option_c": "DFI",
                "option_d": "EGI",
                "correct_answer": "A"
            },
            {
                "question": "Q8. Statement:\n\nAll engineers are graduates.\n\nSome graduates are programmers.\n\nConclusions:\n\nI. Some engineers are programmers.\n\nII. All engineers are graduates.",
                "option_a": "Only I follows",
                "option_b": "Only II follows",
                "option_c": "Both follow",
                "option_d": "Neither follows",
                "correct_answer": "B"
            },
            {
                "question": "Q9. Five friends A, B, C, D, and E sit in a row.\n\nA sits to the immediate left of B.\nC sits at one end.\nD sits between B and E.\n\nWho sits in the middle?",
                "option_a": "A",
                "option_b": "B",
                "option_c": "D",
                "option_d": "E",
                "correct_answer": "B"
            },
            {
                "question": "Q10. If DOG → FQI then CAT → ?",
                "option_a": "ECV",
                "option_b": "EDX",
                "option_c": "DBU",
                "option_d": "FCW",
                "correct_answer": "A"
            },
            {
                "question": "Q11. What is the output?\n\n```python\nx = [10, 20, 30]\nprint(x[-2])\n```",
                "option_a": "10",
                "option_b": "20",
                "option_c": "30",
                "option_d": "ERROR",
                "correct_answer": "B"
            },
            {
                "question": "Q12. What is the output of the following Python code?\n\n```python\ndef fun(x=[]):\n    x.append(5)\n    return x\n\nprint(fun())\nprint(fun())\n```",
                "option_a": "[5][5]",
                "option_b": "[5][5,5]",
                "option_c": "ERROR",
                "option_d": "[][]",
                "correct_answer": "B"
            },
            {
                "question": "Q13. Which of the following is true?",
                "option_a": "Java supports multiple inheritance using classes.",
                "option_b": "Java supports inheritance using classes.",
                "option_c": "Java does not support interfaces.",
                "option_d": "Java has no inheritance",
                "correct_answer": "B"
            },
            {
                "question": "Q14. Which query returns the second highest salary?",
                "option_a": "SELECT MAX(salary) FROM employee;",
                "option_b": "SELECT MIN(salary) FROM employee;",
                "option_c": "SELECT MAX(salary) FROM employee WHERE salary < (SELECT MAX(salary) FROM employee);",
                "option_d": "SELECT salary,FROM employee;",
                "correct_answer": "C"
            },
            {
                "question": "Q15. Which HTTP status code means 'Resource Created Successfully'?",
                "option_a": "200",
                "option_b": "201",
                "option_c": "204",
                "option_d": "404",
                "correct_answer": "B"
            },
            {
                "question": "Q16. What is the output of the following Python code?\n\n```python\na = \"Python\"\nprint(a[::-1])\n```",
                "option_a": "Python",
                "option_b": "nohtyP",
                "option_c": "Error",
                "option_d": "P",
                "correct_answer": "B"
            },
            {
                "question": "Q17. What is the output of the following Python code?\n\n```python\nprint(bool([]))\n```",
                "option_a": "True",
                "option_b": "False",
                "option_c": "Error",
                "option_d": "None",
                "correct_answer": "B"
            },
            {
                "question": "Q18. Which data structure is used in Breadth-First Search (BFS)?",
                "option_a": "Stack",
                "option_b": "Queue",
                "option_c": "Linked List",
                "option_d": "Heap",
                "correct_answer": "B"
            },
            {
                "question": "Q19. What is the time complexity of Binary Search?",
                "option_a": "O(n)",
                "option_b": "O(log n)",
                "option_c": "O(n log n)",
                "option_d": "O(1)",
                "correct_answer": "B"
            },
            {
                "question": "Q20. Which sorting algorithm has the best average-case time complexity among these?",
                "option_a": "Bubble Sort",
                "option_b": "Selection Sort",
                "option_c": "Merge Sort",
                "option_d": "Insertion Sort",
                "correct_answer": "C"
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
        print("OK - Re-seeded IT assessment 'Comprehensive IT & Software Engineering Recruitment Drive' with 20 custom questions (20 min limit)!")

if __name__ == '__main__':
    seed_assessment()
