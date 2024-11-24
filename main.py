from connexion import AsyncApp, RestyResolver

app = AsyncApp(__name__)

app.add_api('api/v1/openapi.yaml', base_path='/api/v1', resolver=RestyResolver("api.v1"))
