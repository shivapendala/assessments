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
        db.create_all()
        # Delete existing IT assessment, submissions, answers and questions to start fresh
        all_a = Assessment.query.all()
        it_assessments = [a for a in all_a if 'IT' in a.title and 'Non-IT' not in a.title]
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
                "question": "Q1. A bag contains 4 red and 6 black balls. Three balls are drawn at random one by one without replacement. What is the probability that at least two of them are red?",
                "option_a": "11/30",
                "option_b": "1/2",
                "option_c": "1/3",
                "option_d": "2/3",
                "correct_answer": "C"
            },
            {
                "question": "Q2. Three pipelines A, B, and C can fill a reservoir in 6 hours. After working together for 2 hours, pipeline C is closed, and A and B fill the remaining part in 7 hours. How many hours would pipeline C alone take to fill the reservoir?",
                "option_a": "10 hours",
                "option_b": "12 hours",
                "option_c": "14 hours",
                "option_d": "16 hours",
                "correct_answer": "C"
            },
            {
                "question": "Q3. What is the remainder when 2^2024 is divided by 17?",
                "option_a": "1",
                "option_b": "2",
                "option_c": "4",
                "option_d": "16",
                "correct_answer": "A"
            },
            {
                "question": "Q4. In a knockout tournament with 64 teams, how many total matches are played to determine the single winner?",
                "option_a": "63",
                "option_b": "64",
                "option_c": "32",
                "option_d": "127",
                "correct_answer": "A"
            },
            {
                "question": "Q5. There are 100 prisoners and 100 boxes, each containing a unique number from 1 to 100. Each prisoner enters the room one by one and can open up to 50 boxes to find their own number. They cannot communicate after entering. What strategy maximizes their team survival probability (where ALL must find their own number) to ~31.18%?",
                "option_a": "Open 50 random boxes",
                "option_b": "Use the loop strategy (open box of their number, then follow the pointer inside)",
                "option_c": "Open even-numbered boxes only",
                "option_d": "No strategy can raise the probability above 0%",
                "correct_answer": "B"
            },
            {
                "question": "Q6. In the cryptarithmetic equation SEND + MORE = MONEY, what digit does the letter 'O' represent?",
                "option_a": "0",
                "option_b": "1",
                "option_c": "8",
                "option_d": "9",
                "correct_answer": "A"
            },
            {
                "question": "Q7. What is the next number in the sequence: 2, 9, 28, 65, 126, ?",
                "option_a": "217",
                "option_b": "218",
                "option_c": "224",
                "option_d": "244",
                "correct_answer": "A"
            },
            {
                "question": "Q8. If all Wicks are Tacks, no Tack is a Bracket, and some Brackets are Cogs, which of the following must be true?",
                "option_a": "Some Cogs are not Tacks.",
                "option_b": "No Wick is a Cog.",
                "option_c": "All Cogs are Brackets.",
                "option_d": "Some Wicks are Brackets.",
                "correct_answer": "A"
            },
            {
                "question": "Q9. A, B, C, D, and E are sitting in a circle. A is sitting next to B. C is sitting two places away from D. E is sitting to the immediate right of C. If B is sitting to the immediate left of D, who is sitting to the immediate right of A?",
                "option_a": "B",
                "option_b": "C",
                "option_c": "D",
                "option_d": "E",
                "correct_answer": "B"
            },
            {
                "question": "Q10. If in a certain code language, 'PRIME' is coded as 'KSNRI', how is 'BINARY' coded?",
                "option_a": "YRMZIB",
                "option_b": "YRMXIB",
                "option_c": "ZSNYJC",
                "option_d": "XQLWGA",
                "correct_answer": "A"
            },
            {
                "question": "Q11. What is the output of the following Python code?\n\n```python\nfuncs = [lambda x: x * i for i in range(3)]\nprint([f(2) for f in funcs])\n```",
                "option_a": "[0, 2, 4]",
                "option_b": "[4, 4, 4]",
                "option_c": "[2, 2, 2]",
                "option_d": "[0, 0, 0]",
                "correct_answer": "B"
            },
            {
                "question": "Q12. In Python, which of the following execution styles will successfully bypass the Global Interpreter Lock (GIL) to utilize multiple CPU cores for CPU-bound tasks?",
                "option_a": "threading.Thread",
                "option_b": "asyncio event loops",
                "option_c": "multiprocessing.Process",
                "option_d": "gevent greenlets",
                "correct_answer": "C"
            },
            {
                "question": "Q13. What will be printed by the following Java code?\n\n```java\nString s1 = \"hello\";\nString s2 = new String(\"hello\");\nString s3 = s2.intern();\nSystem.out.println((s1 == s2) + \" \" + (s1 == s3));\n```",
                "option_a": "true true",
                "option_b": "false false",
                "option_c": "false true",
                "option_d": "true false",
                "correct_answer": "C"
            },
            {
                "question": "Q14. Which SQL clause allows you to assign a unique sequential integer to rows within a partition of a result set, starting at 1 for the first row in each partition?",
                "option_a": "DENSE_RANK() OVER (PARTITION BY ... ORDER BY ...)",
                "option_b": "ROW_NUMBER() OVER (PARTITION BY ... ORDER BY ...)",
                "option_c": "RANK() OVER (PARTITION BY ... ORDER BY ...)",
                "option_d": "NTILE(1) OVER (PARTITION BY ... ORDER BY ...)",
                "correct_answer": "B"
            },
            {
                "question": "Q15. Which CORS header must a server include in its HTTP response to allow a browser script running on 'https://example.com' to read the response?",
                "option_a": "Access-Control-Allow-Origin: https://example.com",
                "option_b": "Access-Control-Request-Headers: Origin",
                "option_c": "Sec-Fetch-Mode: cors",
                "option_d": "Access-Control-Allow-Methods: GET, POST",
                "correct_answer": "A"
            },
            {
                "question": "Q16. What is the primary mechanism in Python to customize the creation and initialization of class objects themselves (not instances of classes)?",
                "option_a": "The __init__ constructor",
                "option_b": "Inheriting from object",
                "option_c": "Creating a custom Metaclass using __new__ of type",
                "option_d": "Decorating methods with @classmethod",
                "correct_answer": "C"
            },
            {
                "question": "Q17. What does calling next(g) do on a generator function g containing a yield statement?",
                "option_a": "Restarts the generator from the beginning",
                "option_b": "Resumes execution up to the next yield expression, returning its value",
                "option_c": "Terminates the generator and throws StopIteration",
                "option_d": "Creates a copy of the generator",
                "correct_answer": "B"
            },
            {
                "question": "Q18. Which of the following problems cannot be solved optimally using a standard Greedy algorithm?",
                "option_a": "Fractional Knapsack Problem",
                "option_b": "0/1 Knapsack Problem",
                "option_c": "Dijkstra's Single Source Shortest Path (non-negative weights)",
                "option_d": "Huffman Coding",
                "correct_answer": "B"
            },
            {
                "question": "Q19. What is the maximum height of an AVL tree with N nodes, and how does it compare to a Red-Black tree with the same number of nodes?",
                "option_a": "AVL height is exactly O(N); Red-Black is O(log N)",
                "option_b": "AVL height is bounded by ~1.44 log2 N; Red-Black is bounded by ~2 log2 N (AVL is more strictly balanced)",
                "option_c": "AVL height is bounded by ~2 log2 N; Red-Black is bounded by ~1.44 log2 N",
                "option_d": "Both heights are exactly log2 N",
                "correct_answer": "B"
            },
            {
                "question": "Q20. Which phase of TCP congestion control is triggered when a sender detects a packet loss via three duplicate ACKs (Fast Retransmit)?",
                "option_a": "Slow Start",
                "option_b": "Congestion Avoidance",
                "option_c": "Fast Recovery (entering Congestion Avoidance directly, bypassing Slow Start)",
                "option_d": "Connection Tear-down",
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
