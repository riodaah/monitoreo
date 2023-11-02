import time
import requests
import json
import os
from datadog_api_client import ApiClient, Configuration
from datadog_api_client.v2.api.metrics_api import MetricsApi
from datadog_api_client.v2.model.metric_intake_type import MetricIntakeType
from datadog_api_client.v2.model.metric_payload import MetricPayload
from datadog_api_client.v2.model.metric_point import MetricPoint
from datadog_api_client.v2.model.metric_series import MetricSeries

def load_datadog_config(environment="DEV"):
    config_path = os.path.join(os.getcwd(), "configjson", "config_datadog.json")
    with open(config_path, 'r') as file:
        config_data = json.load(file)
    env_config = config_data.get(environment, {})
    return env_config

config = load_datadog_config("DEV")
datadog_api_key = config.get("DD-API-KEY")
api_url = os.getenv('API_URL')

configuration = Configuration(
    api_key={'apiKeyAuth': datadog_api_key},
    host="https://us5.datadoghq.com"
)

endpoints_str = os.getenv('ENDPOINTS')
endpoints_list = endpoints_str.split(',')
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

    response = requests.put(
        url,
        headers={},
        json={}
    )
    
    latency = response.elapsed.total_seconds()
    print(f"Latencia para {ep['endpoint']}: {latency} segundos")
    
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
                tags=[f'Latencia:', f'source:{ep["metric_name"]}'],
            ),
        ],
    )
    print(f"Métrica de Latencia para {ep['endpoint']}:")
    print(body_latency)

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
