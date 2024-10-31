from flask import Flask, flash, render_template, request, redirect, url_for
from flask_mysqldb import MySQL
from dotenv import load_dotenv
import os
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required

app = Flask(__name__, static_url_path='/static')
load_dotenv()

# Conectar a MySQL
app.config['MYSQL_USER'] = os.getenv('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.getenv('MYSQL_PASSWORD')
app.config['MYSQL_HOST'] = os.getenv('MYSQL_HOST')
app.config['MYSQL_DB'] = os.getenv('MYSQL_DB')

mysql = MySQL(app)

# Configuración de Flask-Login
app.secret_key = "mysecretkey"
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = "Por favor inicia sesión para acceder a esta página."

# Modelo de usuario
class User(UserMixin):
    def __init__(self, email, contraseña):
        self.id = email
        self.email = email
        self.contraseña = contraseña

@login_manager.user_loader
def load_user(email):
    with mysql.connection.cursor() as cur:
        cur.execute("SELECT Correo, Contraseña FROM pacientes WHERE Correo = %s", (email,))
        user = cur.fetchone()
        if user:
            return User(user[0], user[1])
    return None

# Rutas

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = False  # Inicialmente, no hay error

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        
        with mysql.connection.cursor() as cur:
            cur.execute("SELECT Correo, Contraseña FROM pacientes WHERE Correo = %s AND Contraseña = %s", (email, password))
            user = cur.fetchone()
            if user:
                user_obj = User(user[0], user[1])
                login_user(user_obj)
                flash('¡Inicio de sesión exitoso!', 'success')
                return redirect(url_for('data'))  # Redirige a 'data'
            else:
                error = True  # Indicar que hubo un error de credenciales

    # Si llegamos aquí, renderizamos la plantilla de login con el estado actual de 'error'
    return render_template('users.html', error=error)


# Ruta principal
@app.route('/')
def main():
    return redirect(url_for('login'))

# Gráfico
@app.route('/grafico')
@login_required
def grafico():
    try:
        with mysql.connection.cursor() as cur:
            cur.execute('SELECT Grupo, COUNT(*) FROM pacientes GROUP BY Grupo')
            data = cur.fetchall()
            labels = [row[0] for row in data]
            values = [row[1] for row in data]
        return render_template('chart.html', labels=labels, values=values)
    except Exception as e:
        print(f"Error fetching data from database: {str(e)}")
        flash('Error al obtener los datos del gráfico', 'error')
        return redirect(url_for('data'))

""" @app.route('/grafico')
@login_required
def grafico():
    try:
        with mysql.connection.cursor() as cur:
            cur.execute('SELECT Grupo, COUNT(*) FROM pacientes GROUP BY Grupo')
            data = cur.fetchall()
            labels = [row[0] for row in data]
            values = [row[1] for row in data]
        return render_template('graph.html', labels=labels, values=values)
    except Exception as e:
        print(f"Error fetching data from database: {str(e)}")
        flash('Error al obtener los datos del gráfico', 'error')
        return redirect(url_for('data')) """

# Ruta de logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Has cerrado sesión', 'info')
    return redirect(url_for('login'))

# Leer datos
@app.route('/data')
@login_required
def data():
    try:
        with mysql.connection.cursor() as cur:
            cur.execute('SELECT Nombre, Telefono, Correo, Grupo, Localidad FROM pacientes')
            data = cur.fetchall()
        return render_template('index.html', clientes=data)
    except Exception as e:
        print(f"Error fetching data from database: {str(e)}")
        flash('Error al obtener los datos', 'error')
        return redirect(url_for('data'))

# Guardar datos
@app.route('/save', methods=['POST'])
@login_required
def save():
    try:
        if request.method == 'POST':
            nombre = request.form['nombre']
            telefono = request.form['telefono']
            correo = request.form['correo']
            grupo = request.form['grupo']
            localidad = request.form['localidad']
            contraseña = request.form['contraseña']
            
            with mysql.connection.cursor() as cur:
                cur.execute(
                    "INSERT INTO pacientes (Nombre, Telefono, Correo, Grupo, Localidad, Contraseña) VALUES (%s, %s, %s, %s, %s, %s)",
                    (nombre, telefono, correo, grupo, localidad, contraseña))
                mysql.connection.commit()
            flash('Registro agregado correctamente', 'success')
    except Exception as e:
        print(f"Error al guardar registro en la base de datos: {str(e)}")
        flash('Error al guardar registro', 'error')
    return redirect(url_for('data'))

@app.route('/cargar', methods=['GET', 'POST'])
@login_required
def cargar():
    if request.method == 'POST':
        nombre = request.form['nombre']
        telefono = request.form['telefono']
        correo = request.form['correo']
        grupo = request.form['grupo']
        localidad = request.form['localidad']
        contraseña = request.form['contraseña']

        try:
            with mysql.connection.cursor() as cur:
                cur.execute(
                    "INSERT INTO pacientes (Nombre, Telefono, Correo, Grupo, Localidad, Contraseña) VALUES (%s, %s, %s, %s, %s, %s)",
                    (nombre, telefono, correo, grupo, localidad, contraseña))
                mysql.connection.commit()
            flash('Paciente cargado correctamente', 'success')
            return redirect(url_for('data'))
        except Exception as e:
            print(f"Error al cargar paciente en la base de datos: {str(e)}")
            flash('Error al cargar paciente', 'error')
    
    # Renderiza el formulario para cargar pacientes si es GET o hubo un error en POST
    return render_template('cargar.html')


# Editar cliente
@app.route('/edit/<correo>')
@login_required
def edit(correo):
    try:
        with mysql.connection.cursor() as cur:
            cur.execute('SELECT Nombre, Telefono, Correo, Grupo, Localidad FROM pacientes WHERE Correo = %s', (correo,))
            data = cur.fetchone()
        return render_template('edit.html', contact=data)
    except Exception as e:
        print(f"Error fetching data from database: {str(e)}")
        flash('Error al obtener los datos del cliente', 'error')
        return redirect(url_for('data'))

# Actualizar contacto
@app.route('/update/<correo>', methods=['POST'])
@login_required
def update_contact(correo):
    try:
        if request.method == 'POST':
            nombre = request.form['nombre']
            telefono = request.form['telefono']
            email = request.form['correo']
            grupo = request.form['grupo']
            localidad = request.form['localidad']
            
            with mysql.connection.cursor() as cur:
                cur.execute("""
                    UPDATE pacientes
                    SET Nombre = %s,
                        Telefono = %s,
                        Correo = %s,
                        Grupo = %s,
                        Localidad = %s
                    WHERE Correo = %s
                """, (nombre, telefono, email, grupo, localidad, correo))
                mysql.connection.commit()
            flash('Registro actualizado correctamente', 'success')
    except Exception as e:
        print(f"Error al actualizar registro en la base de datos: {str(e)}")
        flash('Error al actualizar registro', 'error')
    return redirect(url_for('data'))

# Eliminar cliente
@app.route('/delete/<correo>', methods=['GET', 'POST'])
@login_required
def delete(correo):
    try:
        with mysql.connection.cursor() as cur:
            cur.execute('DELETE FROM pacientes WHERE Correo = %s', (correo,))
            mysql.connection.commit()
        flash('Registro eliminado correctamente', 'success')
    except Exception as e:
        print(f"Error al eliminar registro de la base de datos: {str(e)}")
        flash('Error al eliminar registro', 'error')
    return redirect(url_for('data'))

# Iniciar el servidor
if __name__ == '__main__':
    app.run(port=9000, debug=True)
