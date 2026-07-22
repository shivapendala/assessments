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
                "Assessment containing Aptitude & Verbal, Python Programming, Java & Spring Boot, "
                "Frontend, Automation/Manual Testing, and Cyber Security. Contains 20 questions "
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
                "question": "Q1. Pipe A can fill a tank in 6 hours, and Pipe B can fill it in 8 hours. Both pipes are opened together, but after 2 hours, Pipe A is closed. How much time will Pipe B take to fill the remaining part of the tank?",
                "option_a": "2 hours",
                "option_b": "3 hours",
                "option_c": "3 1/3 hours",
                "option_d": "4 hours",
                "correct_answer": "C"
            },
            {
                "question": "Q2. A boat travels 24 km upstream and 36 km downstream in 6 hours. It also travels 36 km upstream and 24 km downstream in 6.5 hours. What is the speed of the boat in still water?",
                "option_a": "8 km/h",
                "option_b": "10 km/h",
                "option_c": "12 km/h",
                "option_d": "15 km/h",
                "correct_answer": "B"
            },
            {
                "question": "Q3. Out of 7 consonants and 4 vowels, how many words of 3 consonants and 2 vowels can be formed?",
                "option_a": "210",
                "option_b": "1,050",
                "option_c": "25,200",
                "option_d": "21,400",
                "correct_answer": "C"
            },
            {
                "question": "Q4. A, B, and C start a business. A invests 3 times as much as B, and B invests two-third of what C invests. At the end of the year, the total profit is ₹6,600. What is B's share in the profit?",
                "option_a": "₹1,200",
                "option_b": "₹1,800",
                "option_c": "₹3,600",
                "option_d": "₹1,500",
                "correct_answer": "A"
            },
            {
                "question": "Q5. A container contains 40 liters of milk. From this container, 4 liters of milk was taken out and replaced by water. This process was repeated further two times. How much milk is now contained by the container?",
                "option_a": "26.34 liters",
                "option_b": "27.36 liters",
                "option_c": "28.00 liters",
                "option_d": "29.16 liters",
                "correct_answer": "D"
            },
            {
                "question": "Q6. In a certain code language, 'STRENGTH' is coded as 'URTCEPVF'. How is 'ROBUST' coded in that language?",
                "option_a": "TMDSUR",
                "option_b": "TMDRUS",
                "option_c": "SMDTUR",
                "option_d": "TNDSVR",
                "correct_answer": "A"
            },
            {
                "question": "Q7. Six people P, Q, R, S, T, and U are sitting in a circle facing the center. P is sitting opposite to S. Q is sitting to the immediate right of P. R is sitting between T and S. U is to the immediate left of S. Who is sitting opposite to Q?",
                "option_a": "R",
                "option_b": "T",
                "option_c": "U",
                "option_d": "P",
                "correct_answer": "A"
            },
            {
                "question": "Q8. Pointing to a photograph, Rohit said, 'She is the mother of my father's only granddaughter.' If Rohit is an only child, how is the woman in the photograph related to Rohit?",
                "option_a": "Sister",
                "option_b": "Wife",
                "option_c": "Daughter",
                "option_d": "Mother-in-law",
                "correct_answer": "B"
            },
            {
                "question": "Q9. A man walks 10 km towards North. From there, he walks 6 km towards South. Then, he walks 3 km towards East. How far and in which direction is he now with reference to his starting point?",
                "option_a": "5 km South-East",
                "option_b": "5 km North-East",
                "option_c": "7 km North",
                "option_d": "7 km East",
                "correct_answer": "B"
            },
            {
                "question": "Q10. Statements:\n1. Some matrices are vectors.\n2. All vectors are scalars.\n\nConclusions:\nI. Some matrices are scalars.\nII. No vector is a matrix.\n\nChoose the correct option:",
                "option_a": "Only Conclusion I follows",
                "option_b": "Only Conclusion II follows",
                "option_c": "Both Conclusions I and II follow",
                "option_d": "Neither Conclusion I nor II follows",
                "correct_answer": "A"
            },
            {
                "question": "Q11. Consider the following Python code:\n\n```python\ndef gen():\n    yield from [x**2 for x in range(3)]\n\ng = gen()\nprint(next(g))\nprint(list(g))\n```\n\nWhat is the printed output?",
                "option_a": "0 and [0, 1, 4]",
                "option_b": "0 and [1, 4]",
                "option_c": "1 and [4]",
                "option_d": "StopIteration error",
                "correct_answer": "B"
            },
            {
                "question": "Q12. What is the output of the following Python decorator implementation?\n\n```python\ndef make_multiplier(factor):\n    def decorator(func):\n        def wrapper(*args, **kwargs):\n            return func(*args, **kwargs) * factor\n        return wrapper\n    return decorator\n\n@make_multiplier(3)\n@make_multiplier(2)\ndef add(a, b):\n    return a + b\n\nprint(add(1, 2))\n```",
                "option_a": "9",
                "option_b": "12",
                "option_c": "18",
                "option_d": "15",
                "correct_answer": "C"
            },
            {
                "question": "Q13. What is the output of the following code snippet in Python?\n\n```python\nmatrix = [[1, 2], [3, 4]]\nmatrix_copy = list(matrix)\nmatrix[0][0] = 99\nmatrix.append([5, 6])\nprint(matrix_copy)\n```",
                "option_a": "[[1, 2], [3, 4]]",
                "option_b": "[[99, 2], [3, 4], [5, 6]]",
                "option_c": "[[99, 2], [3, 4]]",
                "option_d": "[[1, 2], [3, 4], [5, 6]]",
                "correct_answer": "C"
            },
            {
                "question": "Q14. In Python, given the class hierarchy below, what is the Method Resolution Order (MRO) of class D?\n\n```python\nclass A: pass\nclass B(A): pass\nclass C(A): pass\nclass D(B, C): pass\n```",
                "option_a": "D -> B -> A -> C -> object",
                "option_b": "D -> B -> C -> A -> object",
                "option_c": "D -> C -> B -> A -> object",
                "option_d": "D -> A -> B -> C -> object",
                "correct_answer": "B"
            },
            {
                "question": "Q15. What will be the output of the following Python code?\n\n```python\ndef outer():\n    count = 10\n    def inner():\n        nonlocal count\n        count += 5\n        return count\n    return inner\n\nf = outer()\nprint(f())\nprint(f())\n```",
                "option_a": "15 and 15",
                "option_b": "15 and 20",
                "option_c": "10 and 15",
                "option_d": "UnboundLocalError",
                "correct_answer": "B"
            },
            {
                "question": "Q16. In Java, what is the primary guarantee provided by the `volatile` keyword when applied to a member variable?",
                "option_a": "It ensures that only one thread can access or modify the variable at a time (mutual exclusion).",
                "option_b": "It guarantees both thread-safety and atomic operations for compound actions like count++.",
                "option_c": "It guarantees that any thread reading the variable sees the most recent write by any other thread (visibility) and prevents instruction reordering.",
                "option_d": "It serializes the variable so it can be sent over a network.",
                "correct_answer": "C"
            },
            {
                "question": "Q17. What does the following Java code print when executed?\n\n```java\npublic class Test {\n    public static int compute() {\n        try {\n            int x = 10 / 0;\n            return 1;\n        } catch (ArithmeticException e) {\n            return 2;\n        } finally {\n            return 3;\n        }\n    }\n    public static void main(String[] args) {\n        System.out.println(compute());\n    }\n}\n```",
                "option_a": "1",
                "option_b": "2",
                "option_c": "3",
                "option_d": "ArithmeticException is thrown",
                "correct_answer": "C"
            },
            {
                "question": "Q18. What is the output of the following Java code?\n\n```java\nString s1 = \"Java\";\nString s2 = new String(\"Java\");\nString s3 = s2.intern();\nSystem.out.println((s1 == s2) + \" \" + (s1 == s3));\n```",
                "option_a": "true true",
                "option_b": "false false",
                "option_c": "false true",
                "option_d": "true false",
                "correct_answer": "C"
            },
            {
                "question": "Q19. What is the output of the following Java code snippet?\n\n```java\nclass Parent {\n    public static void display() {\n        System.out.print(\"Parent \");\n    }\n}\nclass Child extends Parent {\n    public static void display() {\n        System.out.print(\"Child \");\n    }\n}\npublic class Main {\n    public static void main(String[] args) {\n        Parent obj = new Child();\n        obj.display();\n    }\n}\n```",
                "option_a": "Child",
                "option_b": "Parent",
                "option_c": "Compile-time error",
                "option_d": "Runtime Exception",
                "correct_answer": "B"
            },
            {
                "question": "Q20. In Java Generics, which of the following declarations is correct according to the PECS (Producer Extends, Consumer Super) rule for copy operations?",
                "option_a": "public static <T> void copy(List<? super T> dest, List<? extends T> src)",
                "option_b": "public static <T> void copy(List<? extends T> dest, List<? super T> src)",
                "option_c": "public static <T> void copy(List<T> dest, List<T> src) only, wildcards are not allowed.",
                "option_d": "public static <T> void copy(List<? extends T> dest, List<? extends T> src)",
                "correct_answer": "A"
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
