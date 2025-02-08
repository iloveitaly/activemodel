def add_database_session_middleware(app: FastAPI):
    """
    Add a middleware that creates a database session for each request.
    """

    @app.middleware("http")
    async def db_session_middleware(request: Request, call_next):
        with SessionManager.get_instance().global_session():
            return await call_next(request)
