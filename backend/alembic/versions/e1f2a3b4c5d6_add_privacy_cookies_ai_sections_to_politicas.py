"""add privacy, AI assistant and cookies sections to the politicas page

Revision ID: e1f2a3b4c5d6
Revises: c9d0e1f2a3b4
Create Date: 2026-09-24 10:00:00.000000

"""
from datetime import datetime, timezone
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, None] = 'c9d0e1f2a3b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_page_sections_table = sa.table(
    'page_sections',
    sa.column('id', sa.Integer),
    sa.column('page', sa.String),
    sa.column('type', sa.String),
    sa.column('position', sa.Integer),
    sa.column('is_active', sa.Boolean),
    sa.column('content', sa.JSON),
    sa.column('key', sa.String),
    sa.column('is_builtin', sa.Boolean),
    sa.column('created_at', sa.DateTime),
)

# Texto editable desde el panel (secciones "text" libres, igual que las de
# cambios y devoluciones que ya tiene la página): un párrafo por línea. Lo
# que dice cada bloque describe lo que el sitio hace de verdad hoy — si algo
# cambia (otro proveedor, otro dato guardado), se ajusta acá o desde el
# panel, no queda escrito en el HTML.
_SECTIONS = [
    {
        'heading': 'Privacidad y datos personales',
        'body': (
            'En JG Parfums cuidamos tus datos personales. Aquí te explicamos qué datos manejamos, para qué los usamos, '
            'con quién los compartimos y cómo puedes ejercer tus derechos, conforme a la Ley 1581 de 2012 de protección de datos personales.'
        ),
    },
    {
        'heading': 'Qué datos recopilamos',
        'body': (
            'Al crear una cuenta o comprar: tu nombre, correo electrónico y teléfono y, para el envío, la dirección, la ciudad y las notas de entrega. '
            'Tu contraseña se guarda cifrada, así que nadie de la tienda puede verla. Si compras como invitado, también creamos una cuenta con tu correo para que el pedido quede en tu historial.\n'
            'Si nos escribes por el formulario de contacto: tu nombre, tu correo o teléfono y el mensaje.\n'
            'Al navegar: contamos de forma anónima qué página se visitó, cuándo y desde qué sitio llegó la visita. En esas métricas no guardamos tu dirección IP ni datos de tu navegador, y no usan cookies.\n'
            'No guardamos números de tarjeta ni datos bancarios: el pago se hace directamente en la pasarela de pagos.'
        ),
    },
    {
        'heading': 'Para qué usamos tus datos',
        'body': (
            'Para procesar, cobrar y entregar tus pedidos; enviarte correos sobre tu cuenta y tus compras (confirmación de pedido, recuperación de contraseña); '
            'responder tus mensajes; entender qué partes del sitio se usan más para mejorarlo; y cumplir nuestras obligaciones legales.\n'
            'No vendemos tus datos ni los usamos para publicidad de terceros.'
        ),
    },
    {
        'heading': 'Con quién compartimos tus datos',
        'body': (
            'Solo con quienes hacen posible tu compra, y únicamente lo necesario:\n'
            'Wompi y Mercado Pago, que procesan el pago bajo sus propias políticas de privacidad.\n'
            'La transportadora, que recibe tu nombre, teléfono y dirección para entregar el pedido.\n'
            'El servicio que envía nuestros correos y el que aloja la tienda.\n'
            'Fuera de estos casos, solo compartimos datos si una autoridad competente lo exige.'
        ),
    },
    {
        'heading': 'Asistente virtual con inteligencia artificial',
        'body': (
            'El chat de la tienda responde con un asistente de inteligencia artificial. Es un sistema automático, no una persona: puede equivocarse y no realiza compras, cambios ni reembolsos. '
            'Para eso, escríbenos por WhatsApp o al correo de contacto.\n'
            'Qué recibe el asistente: el texto de cada mensaje que escribes y un identificador de conversación aleatorio que se genera en tu navegador, sin relación con tu nombre ni con tu correo.\n'
            'Si tienes la sesión iniciada, para poder contarte cómo va tu pedido también recibe un resumen de tus últimos 5 pedidos: número, fecha, estado, productos, cantidades y total. '
            'Nunca recibe tu dirección, teléfono, correo, documento, contraseña ni datos de pago, y tampoco tu sesión, así que no puede actuar en tu nombre.\n'
            'Tus mensajes se procesan mediante un flujo automatizado y un modelo de lenguaje de un proveedor externo, y la conversación se conserva asociada a ese identificador para que el asistente mantenga el contexto. '
            'Al cerrar la pestaña, o al iniciar o cerrar sesión, ese identificador se descarta y la siguiente conversación empieza de cero.\n'
            'Por eso te pedimos que no escribas en el chat contraseñas, números de tarjeta, documentos de identidad ni otros datos sensibles. Usar el chat es opcional: puedes comprar y consultar todo sin él.'
        ),
    },
    {
        'heading': 'Cookies y almacenamiento en tu navegador',
        'body': (
            'No usamos cookies de publicidad, de seguimiento ni de analítica de terceros.\n'
            'Para funcionar, el sitio guarda unos pocos datos en tu navegador (almacenamiento local, que cumple el mismo papel que las cookies técnicas): '
            'tu sesión si inicias sesión, el contenido de tu carrito, si cerraste un anuncio o una promoción, la conversación con el asistente (solo mientras la pestaña esté abierta) y tu respuesta al aviso de cookies. '
            'Son necesarios para que la tienda funcione y no se usan para seguirte.\n'
            'Cargamos las tipografías desde Google Fonts, por lo que Google recibe tu dirección IP al pedirlas. Al pagar te llevamos a Wompi o Mercado Pago, que pueden usar sus propias cookies según sus políticas.\n'
            'Puedes borrar estos datos cuando quieras desde la configuración de tu navegador; al hacerlo se cerrará tu sesión, se vaciará el carrito y volverás a ver el aviso de cookies.'
        ),
    },
    {
        'heading': 'Tus derechos sobre tus datos',
        'body': (
            'Como titular de tus datos puedes conocerlos, actualizarlos y rectificarlos; pedir prueba de la autorización que nos diste; saber cómo los usamos; revocar tu autorización y solicitar que los eliminemos; '
            'y presentar una queja ante la Superintendencia de Industria y Comercio si consideras que no se respetaron tus derechos.\n'
            'Para ejercerlos, escríbenos por WhatsApp o al correo de contacto de esta página, indicando tu nombre y el correo con el que compraste. '
            'Respondemos las consultas en máximo 10 días hábiles y los reclamos en máximo 15 días hábiles.\n'
            'El responsable del tratamiento de tus datos es JG Parfums. Última actualización de esta política: 24 de septiembre de 2026.'
        ),
    },
]


def upgrade() -> None:
    # Se agregan AL FINAL de la página (después de lo que haya, editado o
    # no por el admin) y se salta cualquier título que ya exista — así correr
    # esto dos veces, o tener ya una sección con ese título escrita a mano,
    # no duplica nada ni pisa contenido del panel.
    connection = op.get_bind()
    rows = connection.execute(
        sa.select(_page_sections_table.c.position, _page_sections_table.c.content)
        .where(_page_sections_table.c.page == 'politicas')
    ).fetchall()
    existing_headings = {(content or {}).get('heading') for _, content in rows}
    next_position = max((position for position, _ in rows), default=-1) + 1

    now = datetime.now(timezone.utc)
    new_rows = []
    for section in _SECTIONS:
        if section['heading'] in existing_headings:
            continue
        new_rows.append({
            'page': 'politicas', 'type': 'text', 'position': next_position,
            'is_active': True,
            'content': {'heading': section['heading'], 'body': section['body']},
            'key': None, 'is_builtin': False, 'created_at': now,
        })
        next_position += 1
    if new_rows:
        connection.execute(_page_sections_table.insert(), new_rows)


def downgrade() -> None:
    # Quita solo las secciones de esta migración, por título. Si el admin ya
    # cambió el título de alguna desde el panel, esa queda (ya no se puede
    # reconocer como "la de la migración").
    connection = op.get_bind()
    headings = {section['heading'] for section in _SECTIONS}
    rows = connection.execute(
        sa.select(_page_sections_table.c.id, _page_sections_table.c.content)
        .where(_page_sections_table.c.page == 'politicas')
    ).fetchall()
    ids = [row_id for row_id, content in rows if (content or {}).get('heading') in headings]
    if ids:
        connection.execute(_page_sections_table.delete().where(_page_sections_table.c.id.in_(ids)))
