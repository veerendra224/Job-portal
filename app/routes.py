from flask_mail import Message
from flask import Blueprint, render_template, url_for, flash, redirect, request, abort
from flask_login import login_user, current_user, logout_user, login_required
from app import db, bcrypt
from app.models import User, Job, Application
from app.forms import RegistrationForm, LoginForm, JobPostForm, JobSearchForm, RequestResetForm, ResetPasswordForm
from app import mail

main = Blueprint('main', __name__)

@main.route("/")
@main.route("/home")
def home():
    form = JobSearchForm()
    jobs = Job.query.filter_by(is_active=True).order_by(Job.posted_at.desc()).limit(5).all()
    return render_template('index.html', jobs=jobs, form=form)

@main.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password, user_type=form.user_type.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)

@main.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
    return render_template('login.html', title='Login', form=form)

@main.route("/reset_password", methods=['GET', 'POST'])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.get_reset_token()
            msg = Message('Password Reset Request',
                          sender='noreply@demo.com',
                          recipients=[user.email])
            msg.body = f'''To reset your password, visit the following link:
{url_for('main.reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
            mail.send(msg)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('main.login'))
    return render_template('reset_request.html', title='Reset Password', form=form)

@main.route("/reset_password/<token>", methods=['GET', 'POST'])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token', 'warning')
        return redirect(url_for('main.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()
        flash('Your password has been updated! You are now able to log in', 'success')
        return redirect(url_for('main.login'))
    return render_template('reset_token.html', title='Reset Password', form=form)

@main.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.home'))

@main.route("/dashboard")
@login_required
def dashboard():
    if current_user.user_type == 'job_seeker':
        applications = Application.query.filter_by(applicant_id=current_user.id).order_by(Application.applied_at.desc()).all()
        return render_template('dashboard.html', applications=applications)
    elif current_user.user_type == 'employer':
        jobs = Job.query.filter_by(employer_id=current_user.id).order_by(Job.posted_at.desc()).all()
        return render_template('dashboard.html', jobs=jobs)
    else:  # admin
        return redirect(url_for('main.admin_dashboard'))

@main.route("/jobs")
def jobs():
    form = JobSearchForm()
    page = request.args.get('page', 1, type=int)
    jobs = Job.query.filter_by(is_active=True).order_by(Job.posted_at.desc()).paginate(page=page, per_page=10)
    return render_template('jobs.html', jobs=jobs, form=form)

@main.route("/job/<int:job_id>")
def job_details(job_id):
    job = Job.query.get_or_404(job_id)
    if current_user.is_authenticated and current_user.user_type == 'job_seeker':
        application = Application.query.filter_by(job_id=job_id, applicant_id=current_user.id).first()
    else:
        application = None
    return render_template('job_details.html', job=job, application=application)

@main.route("/job/<int:job_id>/apply", methods=['GET', 'POST'])
@login_required
def apply_job(job_id):
    if current_user.user_type != 'job_seeker':
        abort(403)
    job = Job.query.get_or_404(job_id)
    existing_application = Application.query.filter_by(job_id=job_id, applicant_id=current_user.id).first()
    if existing_application:
        flash('You have already applied for this job', 'info')
        return redirect(url_for('main.job_details', job_id=job_id))
    
    if request.method == 'POST':
        cover_letter = request.form.get('cover_letter')
        if not cover_letter:
            flash('Cover letter is required', 'danger')
            return redirect(url_for('main.apply_job', job_id=job_id))
        
        application = Application(
            cover_letter=cover_letter,
            job_id=job_id,
            applicant_id=current_user.id
        )
        db.session.add(application)
        db.session.commit()
        flash('Your application has been submitted!', 'success')
        return redirect(url_for('main.job_details', job_id=job_id))
    
    return render_template('apply_job.html', job=job)

@main.route("/post_job", methods=['GET', 'POST'])
@login_required
def post_job():
    if current_user.user_type != 'employer':
        abort(403)
    form = JobPostForm()
    if form.validate_on_submit():
        job = Job(
            title=form.title.data,
            description=form.description.data,
            requirements=form.requirements.data,
            salary=form.salary.data,
            location=form.location.data,
            category=form.category.data,
            company=form.company.data,
            employer_id=current_user.id
        )
        db.session.add(job)
        db.session.commit()
        flash('Your job has been posted!', 'success')
        return redirect(url_for('main.dashboard'))
    return render_template('post_job.html', title='Post New Job', form=form)

# Admin Routes
@main.route("/admin/dashboard")
@login_required
def admin_dashboard():
    if current_user.user_type != 'admin':
        abort(403)
    total_users = User.query.count()
    total_jobs = Job.query.count()
    total_applications = Application.query.count()
    return render_template('admin/dashboard.html', 
                         total_users=total_users,
                         total_jobs=total_jobs,
                         total_applications=total_applications)

@main.route("/admin/users")
@login_required
def admin_users():
    if current_user.user_type != 'admin':
        abort(403)
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template('admin/users.html', users=users)

@main.route("/admin/jobs")
@login_required
def admin_jobs():
    if current_user.user_type != 'admin':
        abort(403)
    jobs = Job.query.order_by(Job.posted_at.desc()).all()
    return render_template('admin/jobs.html', jobs=jobs)

@main.route("/admin/delete_user/<int:user_id>", methods=['POST'])
@login_required
def admin_delete_user(user_id):
    if current_user.user_type != 'admin':
        abort(403)
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash('User has been deleted', 'success')
    return redirect(url_for('main.admin_users'))

@main.route("/admin/toggle_job/<int:job_id>", methods=['POST'])
@login_required
def admin_toggle_job(job_id):
    if current_user.user_type != 'admin':
        abort(403)
    job = Job.query.get_or_404(job_id)
    job.is_active = not job.is_active
    db.session.commit()
    flash('Job status has been updated', 'success')
    return redirect(url_for('main.admin_jobs'))