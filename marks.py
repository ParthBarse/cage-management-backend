correct_answers = [
    {
        "question_id": "q1",
        "correctOptions": ["a", "b"],
        "marks": "5"
    },
    {
        "question_id": "q2",
        "correctOptions": ["c"],
        "marks": "3"
    },
    {
        "question_id": "q3",
        "correctOptions": ["a", "d"],
        "marks": "4"
    }
]

student_answers = [
    {
        "question_id": "q1",
        "answers": ["a", "b"]
    },
    {
        "question_id": "q2",
        "answers": ["c"]
    },
    {
        "question_id": "q3",
        "answers": ["a","d"]
    }
    ,
    {
        "question_id": "q4",
        "answers": ["a","d"]
    }
]


def calculate_marks(correct_answers, student_answers):
    total_marks = 0
    for correct in correct_answers:
        question_id = correct["question_id"]
        correct_options = set(correct["correctOptions"])
        marks = int(correct["marks"])
        
        for student in student_answers:
            if student["question_id"] == question_id:
                student_options = set(student["answers"])
                if student_options == correct_options:
                    total_marks += marks
    return total_marks


total_marks = calculate_marks(correct_answers, student_answers)
print(f"Total Marks: {total_marks}")