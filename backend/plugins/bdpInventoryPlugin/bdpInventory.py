import os
import sys
import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.functions.kernel_function_decorator import kernel_function
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.contents.chat_history import ChatHistory

from dotenv import load_dotenv
if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated
from azure.cosmos import CosmosClient, PartitionKey

load_dotenv()
print("LOADING")
AZURE_COSMOSDB_ACCOUNT = os.environ.get("AZURE_COSMOSDB_NAME")
AZURE_COSMOSDB_INVENTORY_DATABASE = os.environ.get("AZURE_COSMOSDB_INVENTORY_DATABASE")
AZURE_COSMOSDB_INVENTORY_CONTAINER = os.environ.get("AZURE_COSMOSDB_INVENTORY_CONTAINER")
AZURE_COSMOSDB_ACCOUNT_KEY = os.environ.get("AZURE_COSMOSDB_ACCOUNT_KEY")
AZURE_OPENAI_API_TYPE = "azure"
AZURE_OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")
AZURE_OPENAI_API_VERSION = "2023-03-15-preview"
AZURE_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv('OPENAI_ADA_EMBEDDING_DEPLOYMENT_NAME')
AZURE_SEARCH_ENDPOINT = os.getenv('AZURE_COGNITIVE_SEARCH_ENDPOINT')
AZURE_SEARCH_KEY = os.getenv('AZURE_COGNITIVE_SEARCH_API_KEY')
AZURE_OPENAI_CHATGPT_DEPLOYMENT = os.getenv("OPENAI_MODEL_NAME")
print(AZURE_COSMOSDB_ACCOUNT)
print(AZURE_COSMOSDB_INVENTORY_CONTAINER)

SERVICE_ID = "azureopenai"

# Initialize a CosmosDB client with AAD auth and containers
cosmos_inventory_client = None
if AZURE_COSMOSDB_ACCOUNT and AZURE_COSMOSDB_INVENTORY_CONTAINER:
    try :
        cosmos_endpoint = f'https://{AZURE_COSMOSDB_ACCOUNT}.documents.azure.com:443/'

        if not AZURE_COSMOSDB_ACCOUNT_KEY:
            credential = ManagedIdentityCredential()
        else:
            credential = AZURE_COSMOSDB_ACCOUNT_KEY

        cosmos_inventory_client = CosmosClient(
            cosmos_endpoint,credential
        )
    except Exception as e:
        print("Exception in CosmosDB initialization", e)
        cosmos_inventory_client = None

# AzureOpenAIService is the main

class BdpInventory:
    """
    Description: BDP Inventory provides a set of functions to mnage the Big Data Platform (BDP) inventory.

    Usage:
        kernel.import_plugin_from_object(BdpInventory(), plugin_name="bdpInventory")

    Examples:
        {{BdpInventory.fetch_bdp_inventory}} => Fetch the inventory from cosmos DB.
    """


    def query_bdp_inventory(self,sql_statement):
        print(sql_statement)
        try:
            database = cosmos_inventory_client.get_database_client(AZURE_COSMOSDB_INVENTORY_DATABASE)
            container = database.get_container_client(AZURE_COSMOSDB_INVENTORY_CONTAINER)
            items = list(container.query_items(
                query=f'{sql_statement}',
                enable_cross_partition_query=True,
                partition_key_range_id="0"
                )
            )
            return str(items)
        except Exception as e:
            print(f"Exception in SQL execution {sql_statement}", e)
            return str(e)

    @kernel_function(name="fetchBdpInventory", description="Given the user's queery about Big Data Platform, run an SQL and return the response from the database")
    async def fetch_bdp_inventory(
        self,
        input: Annotated[str, "The user's query about Big Data Platform inventory"]
    ) -> Annotated[str, "the output is a string"]:
        """Fetch the inventory from cosmos DB."""
        print(AZURE_OPENAI_API_BASE)
        kernel = sk.Kernel()
        kernel.add_service(
            sk_oai.AzureChatCompletion(
                service_id="azureopenai", deployment_name=AZURE_OPENAI_CHATGPT_DEPLOYMENT, endpoint=AZURE_OPENAI_API_BASE, api_key=AZURE_OPENAI_API_KEY
            ),
        )
        bdpFunctions = kernel.import_plugin_from_prompt_directory("./plugins/bdpInventoryPlugin", "bdpPromptPlugin")
        bdpFunction = bdpFunctions["bdpPrompt"]
        result = await kernel.invoke(bdpFunction, sk.KernelArguments(input=input))
        result_sql = self.query_bdp_inventory(str(result))
        bdpResponse = bdpFunctions["bdpResponse"]
        result = await kernel.invoke(bdpResponse, sk.KernelArguments(input=result_sql,query=input))

        return str(result)