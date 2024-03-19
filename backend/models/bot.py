"""
Chatbot with context and memory, using Semantic Kernel.
"""

from semantic_kernel import Kernel,KernelArguments
from semantic_kernel.planners import ActionPlanner
from semantic_kernel.planners.stepwise_planner import StepwisePlanner, StepwisePlannerConfig
from models.kernelManagement import myKernel
from semantic_kernel.contents.chat_history import ChatHistory

# Chat roles
SYSTEM = "system"
USER = "user"
ASSISTANT = "assistant"
SERVICE_ID = "azureopenai"

class bot:
    """Create a chatbot with Azure OPENAI LLM."""

    kernel = None
    variables = None
    chat_history = None

    def __init__(self,kernel : Kernel, variables : KernelArguments, chat_history: ChatHistory):
        self.kernel = kernel
        self.variables = variables
        self.chat_history = chat_history


    async def retrieverAugmentedGeneration(self,index_name:str, query: str) -> str:
        """
         Asks the LLM to answer the user's query with the context provided.
         The index_name may be empty if we are not using Azure Search
        """

        #self.variables = KernelArguments(input=query,chat_history=self.chat_history)
        kernelinit = myKernel()
        kernel = kernelinit.initKernel(plugins={})
        if self.kernel :
          kernel.plugins = self.kernel.plugins

        self.chat_history.add_system_message("You are a helpful assistent")
        self.chat_history.add_user_message(query)

        planner = ActionPlanner(kernel,SERVICE_ID)
        plan = await planner.create_plan(goal=query)
        result = await plan.invoke(kernel)
        self.chat_history.add_assistant_message(str(result))

        return str(result)
    async def ask(self,index_name:str, query: str) -> str:
        """
            Send the request to openAI
        """
        response = await self.retrieverAugmentedGeneration(index_name,query)
        print(
            "*****\n"
            f"QUESTION:\n{query}\n"
            f"RESPONSE:\n{response}\n"
            "*****\n"
        )

        return response