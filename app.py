from flask import Flask, render_template, request, url_for, redirect, session, flash


class Cancion:
    def __init__(self, titulo, categoria, idioma):
        self.titulo = titulo
        self.categoria = categoria
        self.idioma = idioma


cancion1 = Cancion('La guitarra', 'Pop', 'Castellano')
cancion2 = Cancion('Para no verte más', 'Pop', 'Castellano')
cancion3 = Cancion('Balada para un gordo', 'Balada', 'Castellano')
lista = [cancion1, cancion2, cancion3]

app = Flask(__name__)
app.secret_key = 'cochabamba'


@app.route('/')
def index():
    return render_template('listar.html', titulo='Canciones', musicas=lista)


@app.route('/nuevoregistro')
def nuevoregistro():
    if session['usuario_logueado'] == None:
        flash('Usuario no conectado.')
        return redirect('/login')
    else:
        flash('Usuario conectado.')
        return render_template('nuevoRegistro.html', titulo='Nueva Canción')


@app.route('/crear', methods=['POST', ])
def crear():
    titulo = request.form['titulo']
    categoria = request.form['categoria']
    idioma = request.form['idioma']
    cancion = Cancion(titulo, categoria, idioma)
    lista.append(cancion)
    return redirect('/')


@app.route('/login')
def login():
    return render_template('login.html')


@app.route('/autenticar', methods=['POST', ])
def autenticar():
    if 'patitofeo' == request.form['clave']:
        session['usuario_logueado'] = request.form['usuario']
        flash(session['usuario_logueado'] + '¡conectado con éxito!')
        return redirect('/')
    else:
        flash('Usuario no conectado.')
        return redirect('/login')


@app.route('/logout')
def logout():
    session['usuario_logueado'] = None
    flash('¡Logout efectuado exitosamente!')
    return redirect('/')


app.run(host="0.0.0.0", port=5000)