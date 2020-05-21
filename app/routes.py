from app import app, db
from flask import render_template, flash, redirect, request, url_for
from app.forms import LoginForm, RegisterForm, QuizEditForm, QuizLoginForm, QuizStartForm, QuizAnswerForm, QuizReviewForm, changeQuestionForm, QuizMarkForm, GradingForm, EditProfileForm
from flask_login import login_user, login_required, logout_user, current_user
from app.models import User, Question, QuizSet, Answer, Grade


# ----  Index page -----
#New users register from here

@app.route('/', methods = ['GET', 'POST'])
def index():
    form = RegisterForm()
    if form.validate_on_submit():
        email = User.query.filter_by(email=form.email.data).first()
        if email is None:
            user = User(name=form.name.data, email=form.email.data, is_teacher=form.teacher.data)
            #password=form.password.data,
            user.set_password(form.password.data)
            db.session.add(user)
            db.session.commit()
            return render_template('notify.html', content='The user is successfully registered',  buttonText='Back to home page', link='index') 
        else:
            return render_template('notify.html', content='The user already exists!',  buttonText='Back to home page', link='index') 

    return render_template('index.html', registerForm = form)


# ----  Notification page -----

@app.route('/notification/<content>/<buttonText>/<link>')
def notification(content, buttonText, link):
    return render_template('notify.html', content=content, buttonText=buttonText, link=link)

# ----  Login page -----

@app.route('/login', methods = ['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            if user.is_teacher == True:
                next = request.args.get('next')
                if next is None or not next.startswith('/'):
                    next = url_for('teacher')
                return redirect(next)
            else:
                next = request.args.get('next')
                if next is None or not next.startswith('/'):
                    next = url_for('student')
                return redirect(next)
        else:
            return 'The account does not exist'

    return render_template('login.html', loginForm = form)


# ----  Student profile page -----

@app.route('/student', methods = ['GET', 'POST'])
@login_required
def student():
    form = QuizLoginForm()
    if form.validate_on_submit():
        if QuizSet.query.filter_by(quiz_id=form.QuizID.data).first() is None:
            return render_template('notify.html', content='You entered a wrong quizset ID!',  buttonText='Back to profile page', link=student) 
        QuizsetID = QuizSet.query.filter_by(quiz_id=form.QuizID.data).first().id
        if QuizsetID is not None:     
            return redirect(url_for('startQuiz', QuizsetID = QuizsetID, current_question=1))
        else:
            return render_template('notify.html', content='The quiz does not exist!',  buttonText='Back to profile page', link=student) 
    return render_template('student.html', loginQuizForm = form)


# ----  Student quiz page -----

@app.route('/startQuiz/<QuizsetID>/<current_question>', methods = ['GET', 'POST'])
@login_required
def startQuiz(QuizsetID, current_question):
    current_question = int(current_question)
    question_num = QuizSet.query.filter_by(id=QuizsetID).first().question_num
    teacher_id = QuizSet.query.filter_by(id=QuizsetID).first().author_id
    teacher_name = User.query.filter_by(id=teacher_id).first().name

    #calculate previous questions number
    prev_num = Prev_Questions_num(QuizsetID)
    form = QuizAnswerForm()

    if form.validate_on_submit():
        answer = Answer(Answer=form.answer.data, question_id=prev_num+current_question, quizset_id=QuizsetID, student_id=current_user.id)
        db.session.add(answer)
        db.session.commit()
        return redirect(url_for('answerSaved', current_question=current_question, QuizsetID=QuizsetID))

    return render_template('startQuiz.html', prev_num=prev_num, QuizsetID=QuizsetID, current_question=current_question, Question=Question, teacher_name=teacher_name, question_num=question_num, form=form)

# Helper function that helps calculate finished question numbers for students
def Prev_Questions_num(QuizsetID):
    counts = 0
    for i in range(1, int(QuizsetID)):
        counts = counts + Question.query.filter_by(quizset_id=i).count()
    return counts

# Helper function that  helps manage page after student submitted answer
@app.route('/answerSaved/<current_question>/<QuizsetID>', methods = ['GET', 'POST'])
@login_required
def answerSaved(current_question, QuizsetID):
    current_question = int(current_question) + 1
    return redirect(url_for('startQuiz', current_question=current_question, QuizsetID=QuizsetID))


# ----  Finish quiz page -----

@app.route('/finishQuiz')
@login_required
def finishQuiz():
    return render_template('notify.html', content='You have finished your quiz', buttonText='Back to profile page', link=url_for('student'))


# ----  Teacher profile page -----

@app.route('/teacher', methods = ['GET', 'POST'])
@login_required
def teacher():

    form = QuizReviewForm()
    if form.validate_on_submit() and form.QuizID.data is not None:
        QuizID=form.QuizID.data
        quizset = QuizSet.query.filter_by(quiz_id=QuizID).first()
        if quizset is not None:
            quizsetID = quizset.id
            current_question_id = Prev_Questions_num(quizsetID) + 1
            question_n = 0
            return redirect(url_for('reviewQuiz', quizsetID=quizsetID, current_question_id=current_question_id, question_n=question_n))
        else: 
            return 'the quiz does not exists'

    return render_template('teacher.html',  form=form)


# ----  Page for teachers to find the quiz to mark -----

@app.route('/markQuiz', methods = ['GET', 'POST'])
@login_required
def markQuiz():
    form = QuizMarkForm()
    if form.validate_on_submit():
         
        if QuizSet.query.filter_by(quiz_id=form.QuizID.data).first() is None:
            return render_template('notify.html', content= 'You entered a wrong quizset ID!', buttonText='Back to profile page', link=url_for('teacher'))
        else:
            quizsetID = QuizSet.query.filter_by(quiz_id=form.QuizID.data).first().id
            answer_num = Answer.query.filter_by(quizset_id=quizsetID).count()
            current_answer = 0
            return redirect(url_for('reviewAnswer', quizsetID=quizsetID, answer_num=answer_num, current_answer=current_answer))
    return render_template('findQuizToMark.html', form=form)


# ----  Logout page -----

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('notify.html', content='You have been logged out.',  buttonText='Back to home page', link=url_for('index'))


# ---- Page for teachers to start adding a quiz -----

@app.route('/startEditQuiz', methods = ['GET', 'POST'])
@login_required
def startEditQuiz():
    form = QuizStartForm()
    if form.validate_on_submit():
        num_question=form.question_num.data
        id_quiz = form.quiz_id.data
        quizset = QuizSet(title=form.title.data, quiz_id=id_quiz, question_num=num_question, author_id=current_user.id)
        db.session.add(quizset)
        db.session.commit()
        quizset_id = QuizSet.query.filter_by(quiz_id=id_quiz).first().id
        return redirect(url_for('editQuiz', current_question=1, QuizsetID=quizset_id, num_question=num_question))
    return render_template('startEditQuiz.html', quizStartForm=form)


# ----  Page for teachers to add quiz questions  -----

@app.route('/editQuiz/<QuizsetID>/<num_question>/<current_question>',  methods = ['GET', 'POST'])
@login_required
#there's problem with it
def editQuiz(QuizsetID, num_question, current_question):
    form = QuizEditForm()
    question_num = int(num_question)
    current_question = int(current_question)
    if form.validate_on_submit():
        #quizId = QuizSet.query.filter_by(quiz_id=qid).first().id
        question = Question(Question=form.question.data, quizset_id=QuizsetID)
        db.session.add(question)
        db.session.commit()
        return redirect(url_for('questionSaved', current_question=current_question, QuizsetID=QuizsetID, num_question=question_num))
    return render_template('editQuiz.html', quizEditForm=form, current_question=current_question, question_num=question_num)


# Helper function that helps count the number of question left to modify
@app.route('/questionSaved/<current_question>/<QuizsetID>/<num_question>', methods = ['GET', 'POST'])
@login_required
def questionSaved(current_question, QuizsetID, num_question):
    current_question = int(current_question) + 1
    return redirect(url_for('editQuiz', current_question=current_question, QuizsetID=QuizsetID, num_question=num_question))


# ----  Page for teachers to grade quiz questions  -----

@app.route('/reviewAnswer/<quizsetID>/<current_answer>/<answer_num>', methods = ['GET', 'POST'])
@login_required
def reviewAnswer(quizsetID,current_answer,answer_num):

    form = GradingForm()
    current_answer = int(current_answer)
    answer_num = int(answer_num)
    if quizsetID is None:
        return 'the quiz does not exists'
    if current_answer is answer_num:
        return 'you have graded all answers'
    else: 
        answer_dict = Answer.query.filter_by(quizset_id=quizsetID).all()
        answer = str(answer_dict[int(current_answer)])
        answer = answer.split(",")
        if form.validate_on_submit():
            grade = Grade(mark=form.mark.data, comment=form.comment.data, answer_id=answer[1], answerer_id=int(answer[0]))
            db.session.add(grade)
            db.session.commit()
            return redirect(url_for('nextAnswer', quizsetID=quizsetID, current_answer=current_answer, answer_num=answer_num))
        return render_template('reviewAnswer.html', answer=answer[2], form=form)


#Helper function that helps teacher navigate thru questions

@app.route('/nextAnswer/<quizsetID>/<current_answer>/<answer_num>', methods = ['GET', 'POST'])
@login_required
def nextAnswer(quizsetID, current_answer, answer_num):
    current_answer = int(current_answer) + 1
    return redirect(url_for('reviewAnswer', current_answer=current_answer, quizsetID=quizsetID, answer_num=answer_num))


# ----  Page for teachers to edit/modify quiz questions  -----

@app.route('/reviewQuiz/<quizsetID>/<current_question_id>/<question_n>', methods = ['Get', 'POST'])
@login_required
def reviewQuiz(quizsetID,current_question_id, question_n):

    if(current_user.id is not QuizSet.query.filter_by(id=quizsetID).first().author_id):
        return render_template('notify.html', content='you cannot edit the quiz because you are not the author',  buttonText='Back to profile page', link='teacher') 
    elif(int(question_n) is QuizSet.query.filter_by(id=quizsetID).first().question_num):
        return render_template('notify.html', content='you have done editing all questions in this quizset',  buttonText='Back to profile page', link='teacher') 
    else:
        current_question_id = int(current_question_id)
        form=changeQuestionForm()
        if form.validate_on_submit():
            changeQuestion = Question.query.filter_by(id=current_question_id).first()
            changeQuestion.Question=form.newQuestion.data
            db.session.commit()
            return redirect(url_for('nextQuestion', current_question_id=current_question_id, quizsetID=quizsetID, question_n=question_n))
        return render_template('reviewQuiz.html',  form=form, Question=Question, current_question_id=current_question_id)


#Helper function that helps teacher navigate thru questions

@app.route('/nextQuestion/<current_question_id>/<quizsetID>/<question_n>', methods = ['Get', 'POST'])
@login_required
def nextQuestion(current_question_id, quizsetID, question_n):
    current_question_id = int(current_question_id) + 1
    question_n = int(question_n) + 1
    return redirect(url_for('reviewQuiz', current_question_id=current_question_id, quizsetID=quizsetID, question_n=question_n))


# ----  Student View Grade page  -----

@app.route('/viewGrade',  methods = ['GET', 'POST'])
@login_required
def viewGrade():
    grade_dict = Grade.query.filter_by(answerer_id=current_user.id).all()
    
    return render_template('viewGrade.html', grade_dict=grade_dict, str=str, Answer=Answer)

# ----  Student View Ranking page   -----

@app.route('/viewRanking',  methods = ['GET', 'POST'])
@login_required
def viewRanking():
    quizsets_taken = []
    answerlist = Answer.query.filter_by(student_id=current_user.id).all()
    for key in answerlist:
        each_answerlist = str(key)
        each_answerlist = each_answerlist.split(',')
        this_quizset = each_answerlist[3]
        quizsets_taken.append(this_quizset)

    unique_quizsets = unique_items(quizsets_taken)

    all_marks = []
    all_students_id = []

    return render_template('viewRanking.html', unique_quizsets=unique_quizsets, QuizSet=QuizSet, User=User, Answer=Answer, Grade=Grade, str=str, all_marks=all_marks, calcualte_total_mark=calcualte_total_mark, calculate_ranking=calculate_ranking, all_students_id=all_students_id, len=len, unique_items=unique_items)


@app.route('/editProfile',  methods = ['GET', 'POST'])
@login_required
def editProfile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.faculty = form.faculty.data
        current_user.title = form.title.data
        current_user.phone = form.phone.data
        current_user.address = form.address.data
        db.session.add(current_user._get_current_object())
        db.session.commit()
        if current_user.is_teacher:
            return render_template('notify.html', content='Your profile has been successfuly updated', buttonText='Back to profile page', link='teacher')
        else:
            return render_template('notify.html', content='Your profile has been successfuly updated', buttonText='Back to profile page', link='student')
    return render_template('editProfile.html', EditProfileForm=form)



#Helper function that calculates the total mark of each quiz
def calcualte_total_mark(all_marks):
    total_mark = 0
    for marks in all_marks:
        ###!!!!!!theres bug when user is not graded
        total_mark = total_mark + marks
    return total_mark 

#Helper function that calculates the ranking of each quiz of current student
def calculate_ranking(all_students_id, quizset_id, student_mark):
    all_students_id = unique_items(all_students_id)
    all_students_total_marks = []
    for each_student_id in all_students_id:
        all_marks = []
        #calculate mark for each student
        for answers in Answer.query.filter_by(quizset_id=quizset_id, student_id=each_student_id).all():
            all_marks.append(Grade.query.filter_by(answer_id = str(answers).split(',')[1]).first().mark)
        all_students_total_marks.append(calcualte_total_mark(all_marks))
    all_students_total_marks.sort(reverse=True)
    rank = all_students_total_marks.index(student_mark) + 1

    return rank

#Helper function that sorts out unique items in an item set
def unique_items(all_items):
    unique_items = []
    for key in all_items: 
        if key not in unique_items:
            unique_items.append(key)
    return unique_items




#bug: teacher will unevidably regrade questions. Thus students receive double marks which result in faulty ranking