import os
from typing import List, Dict, Any
from google.cloud import run_v2
from google.api_core import exceptions as google_exceptions

from adk.agent import Agent
from adk.card import Card, CardBody, TextBlock, Tool, Input
from adk.executor import MessageExecutor
from adk.graph import Graph
from adk.prompt import Prompt
from adk.task import Task
from adk.tool import tool

# Environment variables for GCP project and region
PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
REGION = os.environ.get("GOOGLE_CLOUD_LOCATION")


@tool
def list_cloud_run_services(project_id: str, region: str) -> Dict[str, Any]:
    """
    Lists all Cloud Run services in a specified GCP project and region.

    Args:
        project_id: The Google Cloud project ID.
        region: The region of the Cloud Run services (e.g., 'us-central1').

    Returns:
        A dictionary containing a list of service names or an error message.
    """
    try:
        run_client = run_v2.ServicesClient()
        parent = f"projects/{project_id}/locations/{region}"

        services = run_client.list_services(parent=parent)

        service_names = [service.name.split('/')[-1] for service in services]

        if not service_names:
            return {"services": [], "message": "No Cloud Run services found."}

        return {"services": service_names}

    except google_exceptions.PermissionDenied:
        return {"error": "Permission denied. Please ensure the agent has the 'Cloud Run Viewer' role."}
    except google_exceptions.NotFound:
        return {"error": f"Project '{project_id}' or region '{region}' not found."}
    except Exception as e:
        return {"error": f"An unexpected error occurred: {str(e)}"}

import uvicorn
from fastapi import FastAPI
from adk.api.rest import router as a2a_router

# Define the Agent Card
agent_card = Card(
    id="gcp-devops-agent",
    title="GCP DevOps Agent",
    description="An A2A agent for performing DevOps tasks on Google Cloud Platform.",
    author="Jules",
    version="0.1.0",
    body=[
        TextBlock("This agent can help you manage your GCP resources. Currently, it supports listing Cloud Run services."),
        Tool(
            name="list_cloud_run_services",
            description="Lists all Cloud Run services in a specified GCP project and region.",
            inputs=[
                Input(
                    name="project_id",
                    type="string",
                    description="The Google Cloud project ID.",
                    required=True
                ),
                Input(
                    name="region",
                    type="string",
                    description="The region of the Cloud Run services (e.g., 'us-central1').",
                    required=True
                )
            ]
        )
    ]
)

# Define the prompt and executor
prompt = Prompt("You are a helpful GCP DevOps assistant.")
message_executor = MessageExecutor(
    prompt=prompt,
    tools=[list_cloud_run_services]
)

# Define the graph and agent
graph = Graph(
    id="gcp-devops-graph",
    nodes=[message_executor]
)

agent = Agent(
    card=agent_card,
    graphs=[graph]
)

# Create the FastAPI app and include the A2A router
app = FastAPI(
    title="GCP DevOps A2A Agent",
    description="A simple A2A agent for GCP DevOps tasks.",
    version="0.1.0"
)

app.include_router(a2a_router(agent=agent))

@app.get("/")
async def root():
    return {"message": "GCP DevOps A2A Agent is running. Visit /docs for API documentation."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)