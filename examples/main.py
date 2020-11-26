import greeter_server
from bali.core import Bali
from v1.app import router

app = Bali(
    base_settings=None,
    routers=[{
        'router': router,
        'prefix': '/v1',
    }],
    backend_cors_origins=['http://127.0.0.1'],
    rpc_service=greeter_server,
)
app.settings(title='Bali App')

if __name__ == "__main__":
    app.start()
