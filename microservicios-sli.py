import time
import requests
from dotenv import load_dotenv
import json
import os
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v2.api.metrics_api import MetricsApi
from datadog_api_client.v2.model.metric_intake_type import MetricIntakeType
from datadog_api_client.v2.model.metric_payload import MetricPayload
from datadog_api_client.v2.model.metric_point import MetricPoint
from datadog_api_client.v2.model.metric_series import MetricSeries

# Carga las variables de entorno desde el archivo .env
load_dotenv()

# API Key de Datadog
datadog_api_key = os.getenv('DATADOG_API_KEY')
api_url = os.getenv('API_URL')


# Configuración para la API de Datadog
configuration = Configuration(
    api_key={'apiKeyAuth': datadog_api_key},
    host="https://app.datadoghq.com/"
)

# Obtiene los endpoints del archivo .env
endpoints_str = os.getenv('ENDPOINTS')
endpoints_list = endpoints_str.split(',')

# Divide la lista en grupos de dos
endpoints_grouped = [(endpoints_list[i], endpoints_list[i + 1]) for i in range(0, len(endpoints_list), 2)]


endpoints = [
    {
        "endpoint": ep[1],
        "metric_name": ep[0].replace("/", ".").replace("-", "") + ".api.latency"
    }
    for ep in endpoints_grouped
]

for ep in endpoints:
    print(f"Procesando: {ep['endpoint']}")
  
    url = api_url + "/" + ep['endpoint']
        # Consulta la API
    
    response = requests.put(
        url,
        headers={},
        json={}
    )
    
    latency = response.elapsed.total_seconds()
    print(f"Latencia para {ep['endpoint']}: {latency} segundos")
    
    # Enviar latencia a Datadog
    body_latency = MetricPayload(
        series=[
            MetricSeries(
                metric=ep['metric_name'],
                type=MetricIntakeType.GAUGE,
                points=[
                    MetricPoint(
                        timestamp=int(time.time()),
                        value=latency,
                    ),
                ],
                tags=[f'Latencia', f'source:{ep["metric_name"]}'] ,
            ),
        ],
    )
    print(f"Métrica de Latencia para {ep['endpoint']}:")
    print(body_latency)

    # Enviar conteo de respuestas a Datadog
    
    body_response = MetricPayload(
        series=[
            MetricSeries(
                metric=ep['metric_name'].replace("latency", "response_count"),
                type=MetricIntakeType.GAUGE,
                points=[
                    MetricPoint(
                        timestamp=int(time.time()),
                        value=1,
                    ),
                ],
                tags=[f'status:{response.status_code}'],
            ),
        ],
    )
    print(f"\nMétrica de Respuesta para {ep['endpoint']}:")
    print(body_response)

    with ApiClient(configuration) as api_client:
        api_instance = MetricsApi(api_client)
        try:
            api_instance.submit_metrics(body=body_latency)
            api_instance.submit_metrics(body=body_response)
        except Exception as e:
            print(f"Error al enviar datos a Datadog para {ep['endpoint']}:", e)
            if hasattr(e, 'response') and hasattr(e.response, 'content'):
                print("Detalle del error:", e.response.content.decode())
