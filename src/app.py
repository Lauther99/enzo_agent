from apscheduler.schedulers.background import BackgroundScheduler
from src.google.google_services import flow, db
from src.google.utils import decode_state
from src.whatsapp.utils.is_notification import is_notification
from src.whatsapp.utils.message_filter import filter_message_data
from src.whatsapp.whatsapp import chat_manager
from src.firebase.users_manager import save_jwt_to_firebase
import logging
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
import traceback
from src.firebase.users_manager import find_short_url
from src.settings.settings import Config
from fastapi.responses import RedirectResponse, HTMLResponse
from src.utils.utils import html_wrong_google_url, html_close


logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
SECRET_KEY = Config.SECRET_KEY

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite todos los orígenes, puedes restringirlos si es necesario
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

scheduler = BackgroundScheduler()
scheduler.start()

@app.get("/google-auth")
async def google_auth_redirect(request: Request):
    query_params = request.query_params
    
    user_phone = query_params.get("user")
    short_id = query_params.get("to") 
    google_auth_url = find_short_url(db, user_phone, short_id)

    if google_auth_url:
        return RedirectResponse(url=google_auth_url)
    else:
        return HTMLResponse(content=html_wrong_google_url, status_code=404)

@app.get("/callback")
async def callback(request: Request):
    try:
        # Intercambiar el código por un token de acceso
        flow.fetch_token(authorization_response=str(request.url))

        state = request.query_params.get("state")
        if not state:
            raise HTTPException(status_code=400, detail="Falta el parámetro 'state'")
        
        logging.info(state)
        decoded_state = decode_state(state)
        logging.info(decoded_state)
        user_phone = decoded_state["phone_number"]

        save_jwt_to_firebase(db, user_phone, flow.credentials)
        return HTMLResponse(content=html_close, status_code=200)

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Error al intercambiar el código: {e}")

@app.get("/wsp-webhook")
async def get_wsp_webhook(request: Request, response: Response):
    try:
        logging.info("GET endpoint hit")
        logging.info(f"Query parameters: {request.query_params}")
        
        # Handle OPTIONS request (preflight)
        if request.method == "OPTIONS":
            response.headers["Access-Control-Allow-Methods"] = "GET, POST"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            response.headers["Access-Control-Max-Age"] = "3600"
            return Response(status_code=204)
        
        # Handle GET request and return challenge

        hub_challenge = request.query_params.get("hub.challenge")
        
        return Response(content=hub_challenge)
    
    except Exception as error:
        logging.error(f"Error in GET /wsp-webhook: {error}")
        raise HTTPException(status_code=400, detail="Error processing request")

@app.post("/wsp-webhook")
async def post_wsp_webhook(request: Request, response: Response):
    try:
        logging.info("POST endpoint hit")
        incoming_message = await request.json()
        logging.info(f"Incoming Message: {incoming_message}")
        
        # Handle OPTIONS request (preflight)
        if request.method == "OPTIONS":
            response.headers["Access-Control-Allow-Methods"] = "GET, POST"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            response.headers["Access-Control-Max-Age"] = "3600"
            return Response(status_code=204)

        # Assuming WhatsappUtils and the necessary utility functions are implemented
        # Check if the incoming message is a notification
        is_notif = is_notification(incoming_message)
        if not is_notif:
            message_data = filter_message_data(incoming_message)
            logging.info("Processing Incoming Message")
            # Assuming db is a database connection or manager
            await chat_manager(db, message_data)
        
        return JSONResponse(content={"message": "Ok"}, status_code=200)

    except Exception as error:
        logging.error(f"Error in POST /wsp-webhook: {error}")
        raise HTTPException(status_code=400, detail="Error processing request")


# def send_email_task():
#     data = request.json

#     # Validar y obtener los campos necesarios
#     credentials_json = data.get("credentials")
#     to_email = data.get("to_email")
#     subject = data.get("subject")
#     body = data.get("body")
#     date = data.get("date")  # Formato: YYYY-MM-DDTHH:MM:SS

#     try:
#         # Convertir la fecha al formato de datetime
#         scheduled_time = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S")
#         scheduled_time = pytz.UTC.localize(
#             scheduled_time
#         )  # Asegurarse de manejar zonas horarias

#         # Verificar si el tiempo ya se venció
#         now = datetime.datetime.now().replace(tzinfo=pytz.UTC)
#         if scheduled_time <= now:
#             send_email_task(credentials_json, to_email, subject, body)
#             return jsonify(
#                 {"message": "El tiempo ya se venció. Correo enviado inmediatamente."}
#             )

#         # Programar el correo
#         scheduler.add_job(
#             send_email_task,
#             trigger=DateTrigger(run_date=scheduled_time),
#             args=[credentials_json, to_email, subject, body],
#         )
#         return jsonify(
#             {"message": "Correo programado exitosamente", "scheduled_time": date}
#         )
#     except Exception as e:
#         return jsonify({"error": str(e)}), 400







