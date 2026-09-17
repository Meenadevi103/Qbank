import os
import django
import sys
import fitz  # PyMuPDF

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'qbank.settings')
django.setup()

from django.contrib.auth.models import User
from departments.models import Department, Course, Semester
from subjects.models import Subject
from papers.models import QuestionPaper
from django.core.files.base import ContentFile

def create_pdf_with_text(text, filename):
    doc = fitz.open()
    page = doc.new_page()
    
    # Split text into lines and write to PDF (simple wrapping)
    lines = text.split('\n')
    y = 50
    for line in lines:
        # Very basic word wrap
        words = line.split()
        current_line = ""
        for word in words:
            if len(current_line) + len(word) > 80:
                page.insert_text((50, y), current_line, fontsize=11)
                y += 15
                current_line = word + " "
            else:
                current_line += word + " "
        
        if current_line:
            page.insert_text((50, y), current_line, fontsize=11)
            y += 15
            
        if y > 750:
            page = doc.new_page()
            y = 50
            
    pdf_bytes = doc.write()
    doc.close()
    return pdf_bytes

def main():
    # 1. Create Superuser
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
        print("Superuser 'admin' created with password 'admin123'")
    else:
        # Ensure password is set to admin123
        u = User.objects.get(username='admin')
        u.set_password('admin123')
        u.save()
        print("Superuser 'admin' already exists. Password reset to 'admin123'")

    # 2. Setup Hierarchy
    dept, _ = Department.objects.get_or_create(name='Computer Applications')
    course, _ = Course.objects.get_or_create(department=dept, name='MCA')
    sem, _ = Semester.objects.get_or_create(course=course, number=2, name='Semester 2')

    # 3. Setup Subjects
    java, _ = Subject.objects.get_or_create(course=course, semester=sem, name='Java Programming', code='MCA 202')
    or_subj, _ = Subject.objects.get_or_create(course=course, semester=sem, name='Operations Research', code='MCA 201')
    daa, _ = Subject.objects.get_or_create(course=course, semester=sem, name='Design and Analysis of Algorithms', code='MCA 204')

    # 4. Define Papers Text
    papers_data = [
        {
            'subject': java,
            'year': '2025',
            'filename': 'java_2025.pdf',
            'text': """
Rajagiri College of Social Sciences (Autonomous)
Second semester MCA Degree Examination
March, 2025
(Regular/Supplementary - 2022 admission onwards)
Code: 5658
Sub: (MCA 202) Java Programming
Max. Marks: 75
Duration: 3 Hrs.

SECTION A
Answer any TEN questions.
1 Contrast between TCP and UDP.
2 What do you mean by inheritance?
3 State any two methods in ArrayList class.
4 How can an interface be used to define constants?
5 Discuss the functionality of JProgressBar.
6 Discuss the role of port numbers in communication.
7 How is memory allocated for instance variables and methods?
8 Compare ODBC and JDBC.
9 What is the use of finally block in exception handling?
10 Why is Swing preferred over AWT? Give reasons.
11 State the use of instanceof operator.
12 What do you mean by a delegation event model?

SECTION B
Answer ALL questions.
13 (a) Develop a Java program for the multiplication of two matrices.
[OR]
(b) Elaborate on the various methods of utilizing "super" in Java programming, accompanied by examples.

14 (a) Create a class for storing a String and provide operations for reading, displaying, adding, concatenating and comparing two strings.
[OR]
(b) Develop a program to perform multithreading using a Thread class.

15 (a) Detail the methods in URL and URLConnection class with syntax and example.
[OR]
(b) Implement the transient keyword to demonstrate Serialization and Deserialization in an Employee Class.

16 (a) How can we execute a stored procedure in a database using JDBC?
[OR]
(b) Draw the architecture of JDBC. Explain.

17 (a) Write notes on the following Swing classes i. JTable ii. JColorChooser iii. JSlider
[OR]
(b) Write a program to play an audio clip in an applet window.
            """
        },
        {
            'subject': java,
            'year': '2024',
            'filename': 'java_2024.pdf',
            'text': """
Rajagiri College of Social Sciences (Autonomous)
Second semester MCA Degree Examination
April, 2024
Code: 5085
Sub: (MCA 202) Java Programming
Max. Marks: 75

SECTION A
1 Detail the significance of bytecode in programming.
2 How can an interface be used to define constants?
3 What is the use of a URLConnection class?
4 Describe a JDBC-ODBC bridge.
5 Contrast between TextField and TextArea controls.
6 Differentiate between call by value and call by reference.
7 State the difference between throw and throws, with necessary examples.
8 How does deserialization work for a HAS-A relationship?
9 How are transactions handled in JDBC?
10 Comment on List and Choice in AWT.
11 What do you mean by inheritance?
12 Discuss the role of Adapter classes in windows programming in Java.

SECTION B
13 (a) Develop a Java program for the multiplication of two matrices.
[OR]
(b) Demonstrate the use of instanceof operator in Java.

14 (a) Create a program that exhibits the contents of a file, along with displaying the total count of lines within it.
[OR]
(b) Create a program that demonstrates the usage of access specifiers within packages.

15 (a) Implement a program to create a two-way chat application using socket programming.
[OR]
(b) Write a programme to download the content of any resource from the internet.

16 (a) Write notes on Connection, ResultSet, Statement and Driver, with respect to JDBC.
[OR]
(b) Compare ArrayList and LinkedList. Write a program to store a set of names using ArrayList and LinkedList.

17 (a) Write a program to create a registration form using AWT controls.
[OR]
(b) Using JTable, display the contents in a Student table on a Swing form.
            """
        },
        {
            'subject': or_subj,
            'year': '2025',
            'filename': 'or_2025.pdf',
            'text': """
Rajagiri College of Social Sciences (Autonomous)
Second semester MCA Degree Examination
March, 2025
Code: 5657
Sub: (MCA 201) Operations Research

SECTION A
1 What roles do the Poisson distribution and exponential distribution play in queueing theory?
2 The ABC Furniture Company produces tables and chairs. The production process for each is similar... Formulate a linear programming problem.
3 What are the assumptions and limitations of game theory?
4 Write down the dual of the following LPP. Min 6x1 + 4x2 + 2x3...
5 Describe the difference between deterministic and stochastic simulation.
6 A manufacturer produces two types of models M1 and M2... Formulate a mathematical model to the problem.
7 Distinguish between assignment problems and transportation problems.
8 What is a two person zero sum game?
9 Discuss the impact of service rates on queueing system behavior.
10 What is a pseudo random number?
11 What do you understand by degeneracy in transportation problems? How would you solve degeneracy?
12 Define the following terms: i) Balking. ii) Reneging. iii) Jockeying.

SECTION B
13 (a) Solve by Two-phase method the following LP problem.
[OR]
(b) A company possesses two manufacturing plants, each of which can produce three products...

14 (a) Solve the following assignment problem.
[OR]
(b) Solve the following traveling salesman problem.

15 (a) i) Solve the following game by the principle of dominance. ii) Two players A and B, without showing each other, put a coin on a table...
[OR]
(b) A project consisting of twelve distinct activities to be analyzed by using PERT.

16 (a) Customers arrive at a one window drive in bank according to Poisson distribution...
[OR]
(b) A trucker driver between fixed locations in Los Angeles and Phoenix.

17 (a) A company manufactures around 200 mopeds every day...
[OR]
(b) i) Explain how random numbers are generated. ii) Describe Monte Carlo simulation method.
            """
        },
        {
            'subject': or_subj,
            'year': '2024',
            'filename': 'or_2024.pdf',
            'text': """
Rajagiri College of Social Sciences (Autonomous)
Second semester MCA Degree Examination
April, 2024
Code: 5084
Sub: (MCA 201) Operations Research

SECTION A
1 Explain how you formulate a mathematical model to a given linear programming problem.
2 Explain the term sensitivity analysis.
3 Distinguish float and slack.
4 Define the following terms: i) Balking. ii) Reneging. iii) Jockeying.
5 Explain the types of simulation.
6 Neethu wishes to mix two types of food P and Q...
7 Explain the characteristics of the dual problem.
8 What is dummy activity? Give example.
9 What are transient and steady states of queuing systems?
10 Describe the difference between deterministic and stochastic simulation.
11 Explain dominance property.
12 What are the advantages and disadvantages of simulation?

SECTION B
13 (a) Using Simplex Method solve the following problem.
[OR]
(b) Using Big M method, solve the following LPP.

14 (a) A company has four machines to do three jobs...
[OR]
(b) Solve the following LPP by dual simplex method.

15 (a) Solve the game graphically whose pay off matrix is given below.
[OR]
(b) A project consisting of twelve distinct activities to be analyzed by using PERT.

16 (a) Customers arrive at a one window drive in bank according to Poisson distribution...
[OR]
(b) People arrive at a ticket booth in a Poisson distribution arrival rate...

17 (a) Discuss the Monte Carlo method of solving a problem...
[OR]
(b) A tourist car operator finds out that during the past 100 days... Using random numbers simulate the demand.
            """
        },
        {
            'subject': daa,
            'year': '2024',
            'filename': 'daa_2024.pdf',
            'text': """
Rajagiri College of Social Sciences (Autonomous)
Second semester MCA Degree Examination
April, 2024
Code: 5087
Sub: (MCA 204) Design and Analysis of Algorithms

SECTION A
1 Analyse the time complexity of a nested loop with indices i and j, where i runs from 1 to n and j runs from 1 to i.
2 Differentiate stable and non stable sorting algorithms with examples.
3 What do you mean by prefix code property in Data Compression?
4 Explain level order traversal of a binary tree.
5 Write Euclid's algorithm for finding GCD.
6 Give a practical scenario where hashing is implemented?
7 What is Master's theorem? How can it be used to solve a recurrence relation?
8 Differentiate dynamic programming with greedy strategy.
9 What are the four types of edges present while performing depth first search on a graph?
10 What do you mean by Hamiltonian Path?
11 What is the role of Pivot element in Quick Sort?
12 What do you mean by P class problems?

SECTION B
13 (a) Detail any two Sorting algorithms along with its time complexity.
[OR]
(b) Explain the concept of hashing. What is its relevance in algorithm analysis?

14 (a) With an algorithm of your choice, explain divide and conquer strategy.
[OR]
(b) Explain backtracking strategy with an example.

15 (a) Apply dynamic programming to solve matrix chain multiplication of any four set of matrix.
[OR]
(b) Find the Longest Common Subsequence for the set X = {A, B, C, B, D, A, B} and Y = {B, D, C, A, B, A} using Dynamic Programming Strategy.

16 (a) Solve the All Pair shortest path problem for the following graph using Floyd Warshalls Algorithm.
[OR]
(b) What do you mean by topological sort? Explain the algorithm with example.

17 (a) Justify the role of approximation algorithms in solving optimization problems.
[OR]
(b) Illustrate the Miller Rabin algorithm with an example.
            """
        }
    ]

    for p in papers_data:
        # Create PDF bytes
        pdf_bytes = create_pdf_with_text(p['text'], p['filename'])
        
        # Check if question paper already exists to avoid duplicates
        existing = QuestionPaper.objects.filter(subject=p['subject'], academic_year=p['year']).first()
        if existing:
            print(f"Question Paper for {p['subject'].name} ({p['year']}) already exists. Updating...")
            existing.pdf_file.save(p['filename'], ContentFile(pdf_bytes))
            existing.save()
            # Clear old extracted text so it gets re-analyzed
            if hasattr(existing, 'extracted_text'):
                existing.extracted_text.delete()
            existing.ocr_processed = False
            existing.save()
        else:
            print(f"Creating Question Paper for {p['subject'].name} ({p['year']})")
            qp = QuestionPaper(
                course=course,
                semester=sem,
                subject=p['subject'],
                academic_year=p['year'],
                exam_type='End Semester',
            )
            qp.pdf_file.save(p['filename'], ContentFile(pdf_bytes))
            qp.save()

    print("\nDone! Admin username is 'admin' and password is 'admin123'")

if __name__ == '__main__':
    main()
