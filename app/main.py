""" Main application entry point for the risk metrics API. """
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from .routes import router

load_dotenv()

ENV = os.getenv("ENV", "dev")

if ENV == "prod":
    origins = ["https://risk-ui-nine.vercel.app"]
else:
    origins = ["http://localhost:5173"]

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)
