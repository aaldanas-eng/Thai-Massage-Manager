from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_mail import Mail
from models import db, User, Spa, UserSpa, MassageSession, PasswordReset
from config import Config
from datetime import datetime, timedelta
import secrets
from sqlalchemy import func

app = Flask(__name__)
app.config.from_object(Config)

# Inicializar extensiones
db.init_app(app)
mail = Mail(app)

# Configurar Login Manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Funciones de email simplificadas
def send_activation_request(admin_email, user_data):
    """Envía email al admin solicitando activación de usuario"""
    try:
        from flask_mail import Message
        subject = "Solicitud de Activación - Thai Massage Manager"
        
        # Email simple en texto plano para evitar problemas con templates
        body = f"""
        Nuevo usuario registrado que requiere activación:
        
        Nombre: {user_data['first_name']} {user_data['last_name']}
        Email: {user_data['email']}
        Teléfono: {user_data.get('phone', 'No proporcionado')}
        
        Por favor, accede al panel de administración para activar esta cuenta.
        """
        
        msg = Message(
            subject=subject,
            recipients=[admin_email],
            body=body
        )
        mail.send(msg)
        print(f"Email de activación enviado a {admin_email}")
        return True
    except Exception as e:
        print(f"Error enviando email de activación: {e}")
        return False

def send_welcome_email(user_email, user_name):
    """Envía email de bienvenida cuando el usuario es activado"""
    try:
        from flask_mail import Message
        subject = "Bienvenido a Thai Massage Manager"
        
        body = f"""
        Hola {user_name},
        
        Tu cuenta ha sido activada exitosamente en Thai Massage Manager.
        
        Ahora puedes acceder al sistema y comenzar a registrar tus sesiones de trabajo.
        
        ¡Bienvenido!
        """
        
        msg = Message(
            subject=subject,
            recipients=[user_email],
            body=body
        )
        mail.send(msg)
        print(f"Email de bienvenida enviado a {user_email}")
        return True
    except Exception as e:
        print(f"Error enviando email de bienvenida: {e}")
        return False

# Crear tablas y datos iniciales
with app.app_context():
    db.create_all()
    
    # Crear admin si no existe
    if not User.query.filter_by(is_admin=True).first():
        admin = User(
            email=app.config.get('ADMIN_EMAIL', 'aac.techsol@gmail.com'),
            first_name="Admin",
            last_name="System",
            is_active=True,
            is_admin=True
        )
        admin.set_password("admin123")
        db.session.add(admin)
        
        # Crear algunos SPAs de ejemplo
        if not Spa.query.first():
            spas = [
                Spa(name="Spa Central", address="Calle Principal 123", phone="+34 912 345 678"),
                Spa(name="Spa Norte", address="Avenida Norte 456", phone="+34 913 456 789"),
                Spa(name="Spa Sur", address="Plaza Sur 789", phone="+34 914 567 890")
            ]
            db.session.add_all(spas)
        
        db.session.commit()
        print("Base de datos inicializada con usuario admin y SPAs de ejemplo")

# Rutas de Autenticación
@app.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        else:
            return redirect(url_for('user_dashboard'))
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password) and user.is_active:
            login_user(user)
            flash('¡Inicio de sesión exitoso!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))
        else:
            flash('Email o contraseña incorrectos, o cuenta no activa', 'error')
    
    return render_template('auth/login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        email = request.form.get('email')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')
        password = request.form.get('password')
        
        if User.query.filter_by(email=email).first():
            flash('Este email ya está registrado', 'error')
            return render_template('auth/register.html')
        
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone,
            is_active=False
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        # Enviar email al admin para activación
        user_data = {
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'phone': phone
        }
        if send_activation_request(app.config.get('ADMIN_EMAIL'), user_data):
            flash('Registro exitoso. Se ha enviado una solicitud de activación al administrador.', 'success')
        else:
            flash('Registro exitoso, pero hubo un error al notificar al administrador. Por favor contacta con soporte.', 'warning')
        
        return redirect(url_for('login'))
    
    return render_template('auth/register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión correctamente', 'info')
    return redirect(url_for('index'))

# Rutas de Usuario
@app.route('/user/dashboard')
@login_required
def user_dashboard():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    # Estadísticas rápidas
    total_sessions = MassageSession.query.filter_by(user_id=current_user.id).count()
    total_hours = db.session.query(func.sum(MassageSession.hours)).filter_by(user_id=current_user.id).scalar() or 0
    
    # Calcular ganancias totales
    total_earnings = 0
    sessions = MassageSession.query.filter_by(user_id=current_user.id).all()
    for session in sessions:
        user_spa = UserSpa.query.filter_by(user_id=current_user.id, spa_id=session.spa_id).first()
        if user_spa:
            total_earnings += session.hours * user_spa.price_per_hour
    
    return render_template('user/dashboard.html',
                         total_sessions=total_sessions,
                         total_hours=total_hours,
                         total_earnings=total_earnings)

@app.route('/user/add_session', methods=['GET', 'POST'])
@login_required
def add_session():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    user_spas = UserSpa.query.filter_by(user_id=current_user.id, is_active=True).all()
    
    if request.method == 'POST':
        try:
            spa_id = request.form.get('spa_id')
            date = request.form.get('date')
            hours = float(request.form.get('hours', 0))
            is_car = 'is_car' in request.form
            comments = request.form.get('comments')
            
            # Verificar que el spa pertenece al usuario
            user_spa = UserSpa.query.filter_by(user_id=current_user.id, spa_id=spa_id).first()
            if not user_spa:
                flash('Spa no válido', 'error')
                return redirect(url_for('add_session'))
            
            session = MassageSession(
                user_id=current_user.id,
                spa_id=spa_id,
                date=datetime.strptime(date, '%Y-%m-%d').date(),
                hours=hours,
                is_car=is_car,
                comments=comments
            )
            
            db.session.add(session)
            db.session.commit()
            
            flash('Sesión agregada correctamente', 'success')
            return redirect(url_for('user_sessions'))
        except Exception as e:
            flash(f'Error al agregar sesión: {str(e)}', 'error')
            return redirect(url_for('add_session'))
    
    return render_template('user/add_session.html', user_spas=user_spas)

@app.route('/user/sessions')
@login_required
def user_sessions():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    sessions = MassageSession.query.filter_by(user_id=current_user.id).order_by(MassageSession.date.desc()).all()
    
    session_data = []
    for session in sessions:
        user_spa = UserSpa.query.filter_by(user_id=current_user.id, spa_id=session.spa_id).first()
        price_per_hour = user_spa.price_per_hour if user_spa else 0
        total = session.hours * price_per_hour
        tax_amount = total * 0.21  # 21% de impuestos
        net_amount = total - tax_amount
        
        session_data.append({
            'session': session,
            'spa_name': session.spa.name,
            'price_per_hour': price_per_hour,
            'total': total,
            'tax_amount': tax_amount,
            'net_amount': net_amount
        })
    
    return render_template('user/sessions.html', sessions=session_data)

@app.route('/user/statistics')
@login_required
def user_statistics():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    # Filtros
    spa_filter = request.args.get('spa', 'all')
    date_from = request.args.get('date_from')
    date_to = request.args.get('date_to')
    
    # Consulta base
    query = MassageSession.query.filter_by(user_id=current_user.id)
    
    # Aplicar filtros
    if spa_filter != 'all':
        query = query.filter_by(spa_id=spa_filter)
    
    if date_from:
        query = query.filter(MassageSession.date >= datetime.strptime(date_from, '%Y-%m-%d').date())
    
    if date_to:
        query = query.filter(MassageSession.date <= datetime.strptime(date_to, '%Y-%m-%d').date())
    
    sessions = query.all()
    
    # Calcular estadísticas
    total_hours = sum(session.hours for session in sessions)
    total_earnings = 0
    earnings_by_spa = {}
    
    for session in sessions:
        user_spa = UserSpa.query.filter_by(user_id=current_user.id, spa_id=session.spa_id).first()
        if user_spa:
            session_earning = session.hours * user_spa.price_per_hour
            total_earnings += session_earning
            
            spa_name = session.spa.name
            if spa_name not in earnings_by_spa:
                earnings_by_spa[spa_name] = 0
            earnings_by_spa[spa_name] += session_earning
    
    tax_amount = total_earnings * 0.21
    net_earnings = total_earnings - tax_amount
    
    stats = {
        'total_sessions': len(sessions),
        'total_hours': total_hours,
        'total_earnings': total_earnings,
        'tax_amount': tax_amount,
        'net_earnings': net_earnings,
        'earnings_by_spa': earnings_by_spa
    }
    
    user_spas = UserSpa.query.filter_by(user_id=current_user.id, is_active=True).all()
    
    return render_template('user/statistics.html',
                         stats=stats,
                         user_spas=user_spas,
                         filters=request.args)

@app.route('/user/profile', methods=['GET', 'POST'])
@login_required
def user_profile():
    if current_user.is_admin:
        return redirect(url_for('admin_dashboard'))
    
    if request.method == 'POST':
        current_user.first_name = request.form.get('first_name')
        current_user.last_name = request.form.get('last_name')
        current_user.phone = request.form.get('phone')
        
        new_password = request.form.get('new_password')
        if new_password:
            current_user.set_password(new_password)
            flash('Contraseña actualizada correctamente', 'success')
        
        db.session.commit()
        flash('Perfil actualizado correctamente', 'success')
        return redirect(url_for('user_profile'))
    
    return render_template('user/profile.html')

# Rutas de Administración
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        return redirect(url_for('user_dashboard'))
    
    stats = {
        'total_users': User.query.filter_by(is_admin=False).count(),
        'active_users': User.query.filter_by(is_admin=False, is_active=True).count(),
        'pending_activations': User.query.filter_by(is_admin=False, is_active=False).count(),
        'total_spas': Spa.query.count()
    }
    
    return render_template('admin/dashboard.html', stats=stats)

@app.route('/admin/users')
@login_required
def admin_users():
    if not current_user.is_admin:
        return redirect(url_for('user_dashboard'))
    
    users = User.query.filter_by(is_admin=False).all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def admin_edit_user(user_id):
    if not current_user.is_admin:
        return redirect(url_for('user_dashboard'))
    
    user = User.query.get_or_404(user_id)
    spas = Spa.query.all()
    
    if request.method == 'POST':
        # Actualizar datos básicos
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.phone = request.form.get('phone')
        user.is_active = 'is_active' in request.form
        
        # Actualizar precios por spa
        for spa in spas:
            price_key = f'price_{spa.id}'
            active_key = f'spa_active_{spa.id}'
            
            price = request.form.get(price_key)
            is_active = active_key in request.form
            
            user_spa = UserSpa.query.filter_by(user_id=user.id, spa_id=spa.id).first()
            
            if user_spa:
                if is_active and price:
                    user_spa.price_per_hour = float(price)
                    user_spa.is_active = True
                else:
                    user_spa.is_active = False
            elif is_active and price:
                user_spa = UserSpa(
                    user_id=user.id,
                    spa_id=spa.id,
                    price_per_hour=float(price),
                    is_active=True
                )
                db.session.add(user_spa)
        
        db.session.commit()
        
        # Si se activa el usuario, enviar email de bienvenida
        if user.is_active:
            send_welcome_email(user.email, user.first_name)
            flash(f'Usuario {user.email} activado y notificado', 'success')
        else:
            flash('Usuario actualizado correctamente', 'success')
        
        return redirect(url_for('admin_users'))
    
    return render_template('admin/user_edit.html', user=user, spas=spas)

# Rutas para gestión de contraseñas
@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email, is_active=True).first()
        
        if user:
            # Enviar email al admin
            user_data = {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email
            }
            if send_activation_request(app.config.get('ADMIN_EMAIL'), user_data):
                flash('Se ha enviado una solicitud de restablecimiento de contraseña al administrador.', 'info')
            else:
                flash('Error al enviar la solicitud. Por favor contacta con soporte.', 'error')
        else:
            flash('No se encontró ningún usuario activo con ese email.', 'error')
        
        return redirect(url_for('login'))
    
    return render_template('auth/forgot_password.html')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
