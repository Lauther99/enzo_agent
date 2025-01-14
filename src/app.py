from src.firebase.users_manager import UserManager
from src.scheduler.scheduler import scheduler, schedule_chat_manager
from src.google.google_services import flow, db
from src.google.utils import decode_state
from src.whatsapp.types import WhatsAppMessage, Props
from src.whatsapp.whatsapp import chat_manager
import logging
from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.responses import JSONResponse
from starlette.middleware.sessions import SessionMiddleware
from fastapi.middleware.cors import CORSMiddleware
import traceback
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
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

@app.get("/google-auth")
async def google_auth_redirect(request: Request):
    query_params = request.query_params
    
    user_phone = query_params.get("user")
    short_id = query_params.get("to") 

    user_manager = UserManager(db, user_phone)
    google_auth_url = user_manager.find_short_url(short_id)

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

        user_manager = UserManager(db, user_phone)
        user_manager.save_jwt_to_firebase(flow.credentials)

        user_manager.save_to_chat()
        return HTMLResponse(content=html_close, status_code=200)

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=400, detail=f"Error al intercambiar el código: {e}")

@app.get("/wsp-webhook")
async def get_wsp_webhook(request: Request, response: Response):
    try:
        logging.info("GET endpoint hit")
        logging.info(f"Query parameters: {request.query_params}")
        
        if request.method == "OPTIONS":
            response.headers["Access-Control-Allow-Methods"] = "GET, POST"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            response.headers["Access-Control-Max-Age"] = "3600"
            return Response(status_code=204)

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

        # Check if the incoming message is a notification
        is_notif = WhatsAppMessage.is_notification(incoming_message)
        if not is_notif:
            message_data = Props.filter_message_data(incoming_message)
            logging.info("Processing Incoming Message")
            schedule_chat_manager(chat_manager, db, message_data)
        
        return JSONResponse(content={"message": "Ok"}, status_code=200)

    except Exception as error:
        logging.debug(f"Error in POST /wsp-webhook: {error}")
        raise HTTPException(status_code=400, detail="Error processing request")



async def startup_event():
    logging.info("Iniciando el scheduler.")
    scheduler.start()

async def shutdown_event():
    logging.info("Apagando el scheduler.")
    scheduler.shutdown()

app.add_event_handler("startup", startup_event)
app.add_event_handler("shutdown", shutdown_event)


