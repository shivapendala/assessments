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
        db.create_all()
        # Delete existing Non-IT assessment, submissions, answers and questions to start fresh
        from models.models import Submission, Answer
        all_a = Assessment.query.all()
        non_it_assessments = [a for a in all_a if 'Non-IT' in a.title]
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
            },
            {
                "question": "Q2. Under ICD-10-CM coding guidelines, a patient is admitted with acute exacerbation of COPD and also has Type 2 diabetes mellitus with diabetic chronic kidney disease Stage 3. Which condition should be sequenced as the PRINCIPAL diagnosis?",
                "option_a": "Type 2 diabetes mellitus (E11.65)",
                "option_b": "Acute exacerbation of COPD (J44.1), as it was the reason for admission",
                "option_c": "Diabetic chronic kidney disease Stage 3 (N18.3)",
                "option_d": "Both conditions can be listed as co-principal diagnoses with no sequencing rule",
                "correct_answer": "B"
            },
            {
                "question": "Q3. Your AR aging report shows: 0–30 days: $80,000 | 31–60 days: $40,000 | 61–90 days: $25,000 | 91–120 days: $15,000 | 120+ days: $10,000. If the industry benchmark for AR over 90 days is less than 15% of total AR, is this practice within the benchmark?",
                "option_a": "Yes — AR over 90 days is exactly 14.8%, which is below 15%",
                "option_b": "No — AR over 90 days is 20%, which exceeds the benchmark",
                "option_c": "Yes — AR over 90 days is 12.5%, which is below 15%",
                "option_d": "No — AR over 90 days is 25%, which exceeds the benchmark",
                "correct_answer": "C"
            },
            {
                "question": "Q4. In the US Revenue Cycle, a payer sends an ERA (Electronic Remittance Advice) with CO-45 (Charges exceed your contracted/legislated fee arrangement). The billed amount was $1,200 and allowed amount was $850. The patient has a $200 copay. Which statement correctly describes the financial disposition?",
                "option_a": "Provider collects $1,200 from payer and $200 from patient",
                "option_b": "Provider must write off $350 (CO-45 contractual adjustment), collect allowed $850 from payer minus patient responsibility $200 = $650 from payer, and $200 from patient",
                "option_c": "Provider collects $850 from payer; the $350 difference can also be billed to the patient",
                "option_d": "Resubmit the claim with the billed amount corrected to $850",
                "correct_answer": "B"
            },
            {
                "question": "Q5. A HIPAA breach occurs when a billing staff member accidentally emails an Excel file containing 512 patients' names, diagnoses, and insurance IDs to the wrong recipient. Under the HIPAA Breach Notification Rule, what is the MANDATORY response timeline and authority to notify?",
                "option_a": "Notify the affected patients within 30 days; no need to notify HHS if under 500 patients",
                "option_b": "Notify affected patients within 60 days of discovery; notify HHS within 60 days; notify media if over 500 residents in a state are affected",
                "option_c": "Internal investigation only; no patient notification required if the email was encrypted",
                "option_d": "Notify only if the recipient opened and read the email",
                "correct_answer": "B"
            },
            {
                "question": "Q6. During insurance eligibility verification for a patient scheduled for an elective knee MRI, you discover the patient has dual coverage: Primary = BlueCross PPO (deductible $500, met $300), Secondary = Aetna HMO. The MRI cost is $2,000. What is the CORRECT coordination of benefits (COB) process?",
                "option_a": "Bill both insurers simultaneously for $2,000 each",
                "option_b": "Bill primary BlueCross first; apply its payment and contractual adjustments; bill secondary Aetna only for the remaining patient responsibility after primary adjudication",
                "option_c": "Bill the HMO first because HMOs always take primary",
                "option_d": "Collect the full $2,000 from the patient upfront and let them claim from insurers",
                "correct_answer": "B"
            },
            {
                "question": "Q7. A call centre agent receives an escalated call. The patient is furious because their claim was denied three times, they've received a collections notice, and they have an upcoming surgery next week. Rank the correct escalation protocol: I. Acknowledge and de-escalate  II. Verify account and identify all open denial reasons  III. Place on hold to consult supervisor  IV. Provide a clear action plan with a callback commitment",
                "option_a": "III → I → II → IV",
                "option_b": "I → II → III → IV",
                "option_c": "II → III → I → IV",
                "option_d": "IV → I → II → III",
                "correct_answer": "B"
            },
            {
                "question": "Q8. An inpatient coder is reviewing a chart where the physician documents 'possible pneumonia' in the discharge summary. Under ICD-10-CM inpatient coding guidelines (UHDDS), how should this be coded?",
                "option_a": "Code only the signs and symptoms (cough, fever) — never code 'possible' diagnoses",
                "option_b": "Code pneumonia as if confirmed, because inpatient guidelines allow coding of uncertain diagnoses documented at discharge",
                "option_c": "Leave the principal diagnosis blank until the physician confirms",
                "option_d": "Code as 'observation for suspected pneumonia' only",
                "correct_answer": "B"
            },
            {
                "question": "Q9. An operator's daily data entry target is 200 patient records in 8 hours. An audit reveals the operator entered 174 records with 98% accuracy and 26 records were skipped. What is the operator's productivity rate and accuracy-adjusted output?",
                "option_a": "Productivity 87%, Accuracy-adjusted output: 170.5 correct records",
                "option_b": "Productivity 100%, Accuracy-adjusted output: 200 correct records",
                "option_c": "Productivity 87%, Accuracy-adjusted output: 174 correct records",
                "option_d": "Productivity 80%, Accuracy-adjusted output: 160 correct records",
                "correct_answer": "A"
            },
            {
                "question": "Q10. In Medicare medical billing, the concept of 'Medical Necessity' is critical for claim approval. A physician orders an MRI of the lumbar spine (CPT 72148) for a patient with 3 days of back pain with no neurological deficits or red flag symptoms. What is the most likely outcome?",
                "option_a": "Medicare approves it because the physician ordered it",
                "option_b": "Medicare denies it citing lack of medical necessity — coverage criteria typically require conservative treatment failure (4–6 weeks) before imaging is authorized",
                "option_c": "Medicare always covers MRIs regardless of clinical indication",
                "option_d": "Medicare automatically approves and bills the patient for the remainder",
                "correct_answer": "B"
            },
            {
                "question": "Q11. You are using Excel to calculate the net collection rate (NCR) for a billing department. The formula is: NCR = (Payments / (Charges − Contractual Adjustments)) × 100. If Payments = $450,000, Charges = $900,000, and Contractual Adjustments = $350,000, which Excel formula correctly computes NCR?",
                "option_a": "=450000/900000*100",
                "option_b": "=(450000/(900000-350000))*100",
                "option_c": "=(450000/350000)*100",
                "option_d": "=SUM(450000,350000)/900000*100",
                "correct_answer": "B"
            },
            {
                "question": "Q12. A denial comes in with CARC 97 (The benefit for this service is included in the payment/allowance for another service/procedure that has already been adjudicated). The claim had CPT 99213 (Office Visit E&M) and 93000 (ECG) billed on the same date. What is the most likely reason and resolution?",
                "option_a": "The ECG was not performed; add modifier 59 to both codes",
                "option_b": "Some payers bundle ECG into the E&M visit fee; resolution is to add modifier 25 to the E&M to indicate a separately identifiable service, then appeal if denied",
                "option_c": "Bill the ECG to the secondary insurance",
                "option_d": "The E&M code is wrong; replace 99213 with 99215",
                "correct_answer": "B"
            },
            {
                "question": "Q13. Under the Fair Debt Collection Practices Act (FDCPA), which of the following is PROHIBITED when a collections agent contacts a patient about an overdue medical balance?",
                "option_a": "Calling between 8 AM and 9 PM in the patient's time zone",
                "option_b": "Sending a written validation notice within 5 days of first contact",
                "option_c": "Calling the patient's workplace after the patient has informed the agent that calls there are not permitted",
                "option_d": "Identifying themselves as a debt collector",
                "correct_answer": "C"
            },
            {
                "question": "Q14. A medical biller is working a 91–120 day AR bucket. A claim for $3,500 was submitted to UnitedHealthcare on March 1, denied on March 28 (CO-4: The procedure code is inconsistent with the modifier). The corrected claim was resubmitted April 10 but shows no ERA after 45 days. What is the best next action?",
                "option_a": "Write off the claim — too old to collect",
                "option_b": "Bill the patient for the full $3,500 immediately",
                "option_c": "Call UnitedHealthcare's provider services line to confirm receipt, get a reference number, and request an expedited review citing the claim age",
                "option_d": "Resubmit the claim a third time without changes",
                "correct_answer": "C"
            },
            {
                "question": "Q15. In a BPO healthcare operations team, the SLA (Service Level Agreement) requires 95% of calls to be answered within 30 seconds. In an 8-hour shift, the team received 400 calls. 52 calls were answered after 30 seconds, and 8 calls were abandoned. What is the team's Service Level percentage?",
                "option_a": "87%",
                "option_b": "85%",
                "option_c": "90%",
                "option_d": "88%",
                "correct_answer": "A"
            },
            {
                "question": "Q16. A coder assigns ICD-10-CM code Z23 (Encounter for immunization) and CPT 90686 (influenza vaccine, quadrivalent) + 90471 (immunization administration). The claim is denied with 'service not covered — preventive benefit exhausted.' The patient's plan year started January 1 and they already received a flu shot in September at a pharmacy. What is the correct action?",
                "option_a": "Appeal immediately — flu shots are always covered twice a year",
                "option_b": "Verify the patient's Explanation of Benefits to confirm the prior flu vaccine claim; if confirmed, inform the patient of their financial responsibility and attempt to collect",
                "option_c": "Resubmit with a different CPT code",
                "option_d": "Write off — preventive denials cannot be appealed",
                "correct_answer": "B"
            },
            {
                "question": "Q17. What is the key difference between a 'Rejection' and a 'Denial' in the medical billing Revenue Cycle?",
                "option_a": "Rejections and denials are the same — both mean the payer will not pay",
                "option_b": "A rejection occurs at claim receipt/clearinghouse level (claim never entered the payer's adjudication system) due to format/data errors; a denial means the claim entered adjudication but payment was refused for clinical or policy reasons",
                "option_c": "A denial is issued by the clearinghouse; a rejection is issued by the payer",
                "option_d": "Rejections require an appeal; denials only need resubmission",
                "correct_answer": "B"
            },
            {
                "question": "Q18. A healthcare BPO Quality Analyst reviews 20 randomly sampled patient calls and finds: 3 calls with incorrect information provided, 1 call with HIPAA violation (agent disclosed diagnosis to a non-authorized person), 2 calls where the agent failed to follow escalation protocol. What is the Critical Error Rate, given that HIPAA violations and incorrect information are classified as 'critical' errors?",
                "option_a": "15%",
                "option_b": "30%",
                "option_c": "20%",
                "option_d": "10%",
                "correct_answer": "C"
            },
            {
                "question": "Q19. Under the Medicare Fee Schedule, the Relative Value Unit (RVU) for a procedure is calculated as: (Work RVU × Work GPCI) + (Practice Expense RVU × PE GPCI) + (Malpractice RVU × MP GPCI). If Work RVU = 3.0, Work GPCI = 1.05, PE RVU = 2.0, PE GPCI = 0.98, MP RVU = 0.5, MP GPCI = 1.02, and the Conversion Factor = $36.04, what is the Medicare allowed amount?",
                "option_a": "$196.10",
                "option_b": "$201.50",
                "option_c": "$198.22",
                "option_d": "$204.30",
                "correct_answer": "C"
            },
            {
                "question": "Q20. A Healthcare BPO team lead notices that the Average Handle Time (AHT) has increased from 4.5 minutes to 7.2 minutes over the past month, but the First Call Resolution (FCR) rate has also increased from 68% to 82%. What is the MOST accurate operational conclusion?",
                "option_a": "The increase in AHT is purely negative — agents are being inefficient",
                "option_b": "The team is underperforming; AHT should always decrease",
                "option_c": "The increased AHT is likely justified — agents are spending more time per call to fully resolve issues, which is driving the higher FCR and reducing repeat calls and operational cost",
                "option_d": "FCR and AHT are unrelated metrics; no conclusion can be drawn",
                "correct_answer": "C"
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
