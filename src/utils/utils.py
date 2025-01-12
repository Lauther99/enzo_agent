import re
import jwt
import json
from src.settings.settings import Config
from datetime import datetime

html_close = """<html>
            <body>
                <script>
                    // Cerrar la ventana después de un breve retraso
                    window.close();
                </script>
                <p>Inicio de sesión exitoso. Puedes cerrar esta ventana.</p>
            </body>
        </html>"""

html_wrong_google_url = """<html>
            <body>
                <p>La url no se encontró.</p>
            </body>
        </html>"""

def ensure_json_format(action_input, keys):
    # Primero, nos aseguramos de que cada clave esté entre comillas dobles
    for key in keys:
        pattern = rf'(?<!")\b{re.escape(key)}\b(?!")'
        action_input = re.sub(pattern, f'"{key}"', action_input)

    # Luego, verificamos si la cadena está envuelta en llaves
    action_input = action_input.strip()  # Quitamos espacios en blanco alrededor
    if not (action_input.startswith("{") and action_input.endswith("}")):
        # Si no empieza y termina con llaves, las añadimos
        action_input = f"{{{action_input}}}"

    return action_input

def str_in_placeholders(txt: str, placeholders: list[str]):
    try:
        pattern = rf'{re.escape(placeholders[0])}(.*?){re.escape(placeholders[1])}'
        match = re.search(pattern, txt, re.DOTALL)
        if match:
            return str(match.group(1))
        else:
            return ""
    except Exception as e:
        print(f"Error: {e}")
        return ""
    
def txt_2_Json(txt: str, line_delimiter="\n", **kwargs) -> dict[str, any]:
    """Convierte un texto con keys en un JSON"""
        
    txt = txt.replace("}", "").replace("{", "").replace("```", "").strip()
    lineas = [linea.strip() for linea in txt.strip().split(line_delimiter) if linea.strip()]
        
    pares = [linea.split(": ", 1) for linea in lineas]
    if kwargs.get('no_double_quotes', False):
        datos = {clave.strip().lower(): valor.replace('"', "").rstrip(",") for clave, valor in pares}
    else:
        datos = {clave.strip().lower(): valor.rstrip(",") for clave, valor in pares}
        
    res = json.dumps(datos, indent=4)
    res = json.loads(res)
    return res



def convertir_a_datetime(date: str, time: str) -> datetime:
    """
    Convierte los argumentos `date` y `time` en un objeto `datetime`.

    Args:
        date: Fecha en formato 'YYYY-MM-DD' o 'NOW' para la fecha actual.
        time: Hora en formato 'HH:MM:SS' o 'NOW' para la hora actual.

    Returns:
        Un objeto `datetime` resultante de la combinación de `date` y `time`.
    """
    if date.upper().strip() == "NOW" or time.upper().strip() == "NOW":
        # Si cualquiera de los argumentos es "NOW", usar el momento actual
        return datetime.now()
    
    try:
        # Combinar la fecha y hora para crear el datetime
        combined_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M:%S")
        return combined_datetime
    except ValueError as e:
        raise ValueError(f"Formato inválido para 'date' o 'time': {str(e)}")
