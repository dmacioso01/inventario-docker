
import os
import time

from sqlalchemy import text
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy

app = Flask(
    __name__,
    template_folder="app/templates",
    static_folder="app/static"
)

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "inventario-docker-secret"
)

database_url = os.getenv(
    "DATABASE_URL",
    "sqlite:///inventario.db"
)

app.config["SQLALCHEMY_DATABASE_URI"] = database_url
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)


class Producto(db.Model):
    __tablename__ = "productos"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), nullable=False)
    categoria = db.Column(db.String(80), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    precio = db.Column(db.Float, nullable=False)


@app.route("/")
def inicio():
    productos = Producto.query.order_by(Producto.id.desc()).all()
    return render_template("index.html", productos=productos)


@app.route("/registrar", methods=["POST"])
def registrar():
    try:
        nombre = request.form["nombre"].strip()
        categoria = request.form["categoria"].strip()
        cantidad = int(request.form["cantidad"])
        precio = float(request.form["precio"])

        if not nombre or not categoria or cantidad < 0 or precio < 0:
            raise ValueError()

        producto = Producto(
            nombre=nombre,
            categoria=categoria,
            cantidad=cantidad,
            precio=precio
        )

        db.session.add(producto)
        db.session.commit()
        flash("Producto registrado correctamente.", "success")

    except (ValueError, TypeError):
        db.session.rollback()
        flash("Verifica los datos ingresados.", "error")

    return redirect(url_for("inicio"))


@app.route("/editar/<int:id>", methods=["POST"])
def editar(id):
    producto = db.get_or_404(Producto, id)

    try:
        producto.nombre = request.form["nombre"].strip()
        producto.categoria = request.form["categoria"].strip()
        producto.cantidad = int(request.form["cantidad"])
        producto.precio = float(request.form["precio"])

        if not producto.nombre or not producto.categoria:
            raise ValueError()

        if producto.cantidad < 0 or producto.precio < 0:
            raise ValueError()

        db.session.commit()
        flash("Producto actualizado correctamente.", "success")

    except (ValueError, TypeError):
        db.session.rollback()
        flash("No se pudo actualizar. Revisa los datos.", "error")

    return redirect(url_for("inicio"))


@app.route("/eliminar/<int:id>", methods=["POST"])
def eliminar(id):
    producto = db.get_or_404(Producto, id)
    db.session.delete(producto)
    db.session.commit()

    flash("Producto eliminado correctamente.", "success")
    return redirect(url_for("inicio"))


@app.route("/health")
def health():
    return {"status": "ok"}, 200


def iniciar_base_datos():
    with app.app_context():
        for intento in range(10):
            try:
                with db.engine.connect() as conexion:
                    conexion.execute(text("SELECT 1"))

                db.create_all()
                print("Conexión con MySQL exitosa. Tablas verificadas.")
                return

            except Exception as error:
                print(f"Esperando MySQL... intento {intento + 1}/10")

                if intento == 9:
                    raise error

                time.sleep(5)


if __name__ == "__main__":
    iniciar_base_datos()
    app.run(host="0.0.0.0", port=5000, debug=False)
