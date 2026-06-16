from locust import HttpUser, task, between

class EasyTimeUser(HttpUser):
    wait_time = between(1, 3)
    host = "http://127.0.0.1:8000"

    @task
    def listar_servicios(self):
        self.client.get("/servicios/")

    @task
    def ver_agendar(self):
        self.client.get("/agendar/")

    @task
    def agendar_con_servicio(self):
        self.client.get("/agendar/1/")  # Cambia 1 por un ID real

    @task
    def ver_productos(self):
        self.client.get("/productos/")

    @task
    def ver_carrito(self):
        self.client.get("/carrito/")

    @task
    def ver_pqrs(self):
        self.client.get("/pqrs/")
