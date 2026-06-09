from litestar import Litestar
from litestar.config.cors import CORSConfig
from litestar.openapi import OpenAPIConfig
from litestar.openapi.plugins import SwaggerRenderPlugin

from app.core.config import settings
from app.core.database import Base, engine
from app.routers.auth import auth_router
from app.routers.users import users_router
from app.routers.orders import orders_router
from app.routers.photo_sheets import photo_sheets_router
from app.routers.batches import batches_router
from app.routers.selections import selections_router
from app.routers.retouch import retouch_router
from app.routers.delivery import delivery_router
from app.routers.dashboard import dashboard_router
from app.routers.reviews import reviews_router
from app.routers.complaints import complaints_router


def create_tables() -> None:
    import app.models  # noqa: F401
    Base.metadata.create_all(bind=engine)


cors_config = CORSConfig(
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

openapi_config = OpenAPIConfig(
    title=settings.APP_NAME,
    version="1.0.0",
    path="/docs",
    render_plugins=[SwaggerRenderPlugin()],
)

app = Litestar(
    route_handlers=[
        auth_router,
        users_router,
        orders_router,
        photo_sheets_router,
        batches_router,
        selections_router,
        retouch_router,
        delivery_router,
        dashboard_router,
        reviews_router,
        complaints_router,
    ],
    cors_config=cors_config,
    openapi_config=openapi_config,
    on_startup=[create_tables],
)
