"""
Manage the Kernel, creates a new one and dynamically import plugins
"""
import os

import semantic_kernel as sk
from semantic_kernel import KernelArguments
import semantic_kernel.connectors.ai.open_ai as sk_oai
from dotenv import load_dotenv
import importlib
from plugins.bdpInventoryPlugin.bdpInventory import BdpInventory
from azure.identity import ManagedIdentityCredential, get_bearer_token_provider
load_dotenv()

AZURE_OPENAI_API_TYPE = "azure"
AZURE_OPENAI_API_BASE = os.getenv("OPENAI_API_BASE")
AZURE_OPENAI_API_VERSION = "2023-03-15-preview"
AZURE_OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
AZURE_OPENAI_EMBEDDING_DEPLOYMENT = os.getenv('OPENAI_ADA_EMBEDDING_DEPLOYMENT_NAME')
AZURE_SEARCH_ENDPOINT = os.getenv('AZURE_COGNITIVE_SEARCH_ENDPOINT')
AZURE_SEARCH_KEY = os.getenv('AZURE_COGNITIVE_SEARCH_API_KEY')
AZURE_OPENAI_CHATGPT_DEPLOYMENT = os.getenv("OPENAI_MODEL_NAME")


class myKernel:

    def class_instanciation(self,module_name:str, class_name:str):
        """Return a class instance from a string reference"""
        try:
            print(module_name)
            module_ = importlib.import_module(module_name.replace("/","."))
            try:
                class_ = getattr(module_, class_name)()
            except AttributeError:
                print('Class does not exist')
        except ImportError:
            print('Module does not exist')
        return class_ or None

    def initKernel(self,plugins:dict) :

        kernel = sk.Kernel()


        # if AZURE_OPENAI_API_KEY:
        kernel.add_service(
            sk_oai.AzureChatCompletion(
                service_id="azureopenai",
                deployment_name=AZURE_OPENAI_CHATGPT_DEPLOYMENT,
                endpoint=AZURE_OPENAI_API_BASE,
                api_key=AZURE_OPENAI_API_KEY
            )
        )
        # else:
        #     credential = ManagedIdentityCredential()
        #     token_provider = get_bearer_token_provider(credential, "https://cognitiveservices.azure.com/.default")
        #     kernel.add_service(
        #         sk_oai.AzureChatCompletion(
        #             service_id="azureopenai",
        #             deployment_name=AZURE_OPENAI_CHATGPT_DEPLOYMENT,
        #             endpoint=AZURE_OPENAI_API_BASE,
        #             ad_token_provider=token_provider
        #         )
        #     )

        for plugin in plugins:
            for className, module in plugin.items():
                print(module)
                if module == "" :
                    continue
                class_instiaton = self.class_instanciation(module,className)
                print(class_instiaton)
                kernel.import_plugin_from_object(class_instiaton,className)

        plugins_directory = "./plugins"
        kernel.import_plugin_from_prompt_directory(plugins_directory, "defaultPlugin")

        for plugin in kernel.plugins:
            for function in plugin.functions.values():
                print(f"Plugin: {plugin.name}, Function: {function.name}")

        return kernel
