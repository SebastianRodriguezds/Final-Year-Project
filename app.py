from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import re

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///app.db'  # Asegúrate de que la ruta a tu DB sea correcta
app.config['SECRET_KEY'] = '123456'  # Esto se usa para proteger las sesiones y formularios
db = SQLAlchemy(app)

# Modelos de la Base de Datos
class Company(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    sector = db.Column(db.String(100), nullable=False)
    number_employees = db.Column(db.Integer, nullable=False)
    type_subscription = db.Column(db.String(20), nullable=False)
    users = db.relationship('User', backref='company', lazy=True)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'admin' or 'employee'
    company_id = db.Column(db.Integer, db.ForeignKey('company.id'), nullable=False)
    department = db.Column(db.String(100), nullable=True)

class Consent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    metrics = db.Column(db.String(500))  # JSON or simple text with the selected metrics
    accepted = db.Column(db.Boolean, default=False)

# Crear las tablas (si no existen)
with app.app_context():
    db.create_all()

# Rutas para mostrar la vista de login o registro de empresa
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/select_sector', methods=['GET', 'POST'])
def select_sector():
    if request.method == 'POST':
        sector = request.form['sector']
        session['sector'] = sector  # Guardamos el sector en la sesión
        return redirect(url_for('register'))

    return render_template('select_sector.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    
    sector = session.get('sector')  # El sector es pasado como parámetro en la URL

    if not sector:
        flash("Please select a sector.", "danger")
        return redirect(url_for('select_sector'))

    if request.method == 'POST':
        # Obtener datos del formulario
        name = request.form['name']
        number_employees = request.form['number_employees']
        type_subscription = request.form['type_subscription']
        email = request.form['email']
        password = request.form['password']

        

        # Crear la empresa
        new_company = Company(name=name, sector=sector, number_employees=number_employees, type_subscription=type_subscription)
        db.session.add(new_company)
        db.session.commit()

        # Crear el administrador
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(email=email, password=hashed_password, role='admin', company_id=new_company.id)
        db.session.add(new_user)
        db.session.commit()

        flash("Company and Admin registered successfully!", "success")
        return redirect(url_for('index'))

    return render_template('register.html', sector=sector)

@app.route('/check_company_exists/<company_name>', methods=['GET'])
def check_company_exists(company_name):
    # Buscar la empresa en la base de datos (sin importar mayúsculas o minúsculas)
    company = Company.query.filter(db.func.lower(Company.name) == db.func.lower(company_name)).first()
    
    # Retornar un JSON con la información de si la empresa existe o no
    if company:
        return {"exists": True}
    else:
        return {"exists": False}


@app.route('/register_employee', methods=['GET', 'POST'])
def register_employee():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        company_name = request.form['company_name']
        department = request.form['department']

        # Verifica que la empresa exista
        company = Company.query.filter(db.func.lower(Company.name) == db.func.lower(company_name)).first()

        if not company:
            flash("Company does not exist.", "danger")
            return redirect(url_for('register_employee'))
        print(f"Empresa encontrada: {company.name}")

        # Validation empty fields
        if not email or not password:
            flash("Please fill in all fields", "danger")
            return redirect(url_for('register_employee'))
        
        #Validate format email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$'
        if not re.match(email_pattern, email):
            flash("Invalid email format", "danger")
            return redirect(url_for('register_employee'))

        # Crea el usuario
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(email=email, password=hashed_password, role='employee', company_id=company.id,
        department=department)
        db.session.add(new_user)
        try:
          db.session.commit()
        except Exception as e:
          db.session.rollback()  # Rollback en caso de error
          flash(f"Error: {e}", "danger") 
        finally:
          db.session.remove()

        flash("Employee registered successfully!", "success")
        return redirect(url_for('login'))

    companies = Company.query.all()  # Obtener todas las empresas existentes
    return render_template('register_employee.html', companies=companies)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['role'] = user.role

            if user.role == 'admin':
                if user.company_id:
                  return redirect(url_for('dashboard', company_id=user.company_id))  # Administrador
                else:
                    flash("User does not have an associated company.", "danger")
                    return redirect(url_for('login'))
            
            elif user.role == 'employee':
                consent = Consent.query.filter_by(user_id = user.id).first()
                if not consent or not consent.accepted:
                    return redirect(url_for('consent', user_id=user.id))
                
                if user.company_id:
                    return redirect(url_for('employee_dashboard', company_id=user.company_id))  # Empleado
                else:
                    flash("User does not have an associated company.", "danger")
                    return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/employee_dashboard/<int:company_id>')
def employee_dashboard(company_id):
    print(f"Redirected to employee dashboard for company ID: {company_id}")
    company = Company.query.get_or_404(company_id)
    return render_template('employee_dashboard.html', company=company)

@app.route('/dashboard/<int:company_id>')
def dashboard(company_id):
    company = Company.query.get_or_404(company_id)
    return render_template('dashboard.html', company=company)

#Rute to the consent
@app.route('/consent/<int:user_id>', methods=['GET', 'POST'])
def consent(user_id):
    user = User.query.get_or_404(user_id)
    existing_consent = Consent.query.filter_by(user_id=user.id).first()
    available_metrics = [ "work_hours", 
        "activity_logs", 
        "productivity_scores",
        "keystroke_monitoring",  # Nueva métrica: Monitoreo de pulsaciones de teclas
        "screen_time",           # Nueva métrica: Tiempo activo en pantalla
        "email_analysis" ]

    if request.method == 'POST':
        selected_metrics = request.form.getlist('metrics') #Lista de metricas
        consent_given = 'accept' in request.form

        if existing_consent:
            existing_consent.metrics = ','.join(selected_metrics)
            existing_consent.accepted = consent_given
        else:
            new_consent = Consent(user_id= user.id, metrics=','.join(selected_metrics), accepted=consent_given)
            db.session.add(new_consent)
        
        db.session.commit()
        return redirect(url_for('employee_dashboard', company_id=user.company_id))
    
    return render_template('consent.html', user=user, existing_consent=existing_consent, available_metrics=available_metrics)

# Agregar cierre de sesión
@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully", "success")
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)