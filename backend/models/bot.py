"""
Chatbot with context and memory, using Semantic Kernel.
"""

from semantic_kernel import Kernel,KernelArguments, PromptTemplateConfig
from semantic_kernel.planners import ActionPlanner
from semantic_kernel.planners.stepwise_planner import StepwisePlanner, StepwisePlannerConfig
from models.kernelManagement import myKernel
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.core_plugins import ConversationSummaryPlugin
#from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
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
        #summarize_plugin = kernel.import_plugin_from_object(ConversationSummaryPlugin(kernel),"ConversationSummaryPlugin")
        #chat_history_summarized = await kernel.invoke(summarize_plugin ,KernelArguments(input=f'Summarize This Chat History {self.chat_history}'))
        print("CHAT _ HISTORY")
        #print(summarize_plugin)
        print(self.chat_history)
        self.chat_history.add_system_message("You are a helpful assistent")
        self.chat_history.add_user_message(query)
        planner = ActionPlanner(kernel,SERVICE_ID)
        plan = await planner.create_plan(goal=query)
        input_with_chat = f'User Input : {query} \\n Chat History : {str(self.chat_history)}'
        print(plan)
        result = await plan.invoke(kernel, arguments = KernelArguments(input=input_with_chat))
        if str(result) == "":
            print(kernel.plugins)
            responseFunction = kernel.plugins['defaultPlugin'].functions['response']
            result = await kernel.invoke(responseFunction, KernelArguments(input=input_with_chat))
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