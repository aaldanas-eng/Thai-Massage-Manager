from flask_mail import Mail, Message
from flask import render_template, current_app
import os

mail = Mail()

def send_activation_request(admin_email, user_data):
    """Envía email al admin solicitando activación de usuario"""
    try:
        subject = "Solicitud de Activación - Thai Massage Manager"
        html_body = render_template('email/activation_request.html', 
                                  user_data=user_data)
        
        msg = Message(subject=subject,
                     recipients=[admin_email],
                     html=html_body)
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending activation email: {e}")
        return False

def send_welcome_email(user_email, user_name):
    """Envía email de bienvenida cuando el usuario es activado"""
    try:
        subject = "Bienvenido a Thai Massage Manager"
        html_body = render_template('email/welcome.html', 
                                  user_name=user_name)
        
        msg = Message(subject=subject,
                     recipients=[user_email],
                     html=html_body)
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending welcome email: {e}")
        return False

def send_password_reset_email(user_email, reset_token):
    """Envía email para reset de contraseña"""
    try:
        subject = "Restablecer Contraseña - Thai Massage Manager"
        html_body = render_template('email/password_reset.html', 
                                  reset_token=reset_token)
        
        msg = Message(subject=subject,
                     recipients=[user_email],
                     html=html_body)
        mail.send(msg)
        return True
    except Exception as e:
        print(f"Error sending password reset email: {e}")
        return False