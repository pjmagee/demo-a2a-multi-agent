using System.ComponentModel;
using System.Text.Json;
using A2A;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;
using ModelContextProtocol.Server;

var builder = Host.CreateApplicationBuilder(args);

// Configure logging to stderr (MCP requirement)
builder.Logging.AddConsole(consoleLogOptions =>
{
    consoleLogOptions.LogToStandardErrorThreshold = LogLevel.Trace;
});

// Get registry URL from environment or use default
var registryUrl =
    Environment.GetEnvironmentVariable("A2A_REGISTRY_URL") ?? "https://localhost:52069";
builder.Services.AddSingleton(new RegistryConfig { RegistryUrl = registryUrl });

// Register HttpClient for registry calls with HTTPS cert bypass
builder
    .Services.AddHttpClient("A2ARegistry")
    .ConfigurePrimaryHttpMessageHandler(() =>
        new HttpClientHandler { ServerCertificateCustomValidationCallback = (_, _, _, _) => true }
    );

// Configure MCP server
builder.Services.AddMcpServer().WithStdioServerTransport().WithToolsFromAssembly();

await builder.Build().RunAsync();

// Configuration holder
public sealed class RegistryConfig
{
    public required string RegistryUrl { get; init; }
}

// MCP Tools
[McpServerToolType]
public static class A2ATools
{
    [McpServerTool(Name = "list_a2a_agents")]
    [Description("Lists all registered A2A agents from the registry")]
    public static async Task<string> ListAgents(
        RegistryConfig config,
        IHttpClientFactory httpClientFactory
    )
    {
        var httpClient = httpClientFactory.CreateClient("A2ARegistry");

        try
        {
            var response = await httpClient.GetStringAsync($"{config.RegistryUrl}/agents");
            var jsonDocument = JsonDocument.Parse(response);
            var agents = jsonDocument.RootElement.GetProperty("agents");

            var agentList = new List<object>();
            foreach (var agent in agents.EnumerateArray())
            {
                var agentCard = agent.GetProperty("agent_card");
                agentList.Add(
                    new
                    {
                        address = agent.GetProperty("address").GetString(),
                        name = agentCard.GetProperty("name").GetString(),
                        description = agentCard.TryGetProperty("description", out var desc)
                            ? desc.GetString()
                            : null,
                        version = agentCard.TryGetProperty("version", out var ver)
                            ? ver.GetString()
                            : null,
                    }
                );
            }

            return JsonSerializer.Serialize(
                agentList,
                new JsonSerializerOptions { WriteIndented = true }
            );
        }
        catch
        {
            throw;
        }
    }

    [McpServerTool(Name = "get_agent_card")]
    [Description("Gets the agent card details for a specific A2A agent")]
    public static async Task<string> GetAgentCard(
        [Description("The URL of the A2A agent")] string agentUrl
    )
    {
        try
        {
            var cardResolver = new A2ACardResolver(new Uri(agentUrl));
            var agentCard = await cardResolver.GetAgentCardAsync();

            return JsonSerializer.Serialize(
                agentCard,
                new JsonSerializerOptions(A2AJsonUtilities.DefaultOptions) { WriteIndented = true }
            );
        }
        catch
        {
            throw;
        }
    }

    [McpServerTool(Name = "send_message_to_agent")]
    [Description(
        "Sends a message to an A2A agent and returns the response. Supports both text and JSON messages."
    )]
    public static async Task<string> SendMessage(
        [Description("The URL of the A2A agent")] string agentUrl,
        [Description("The message content to send to the agent (can be plain text or JSON string)")]
            string message,
        [Description(
            "Content type: 'text' for plain text or 'json' for JSON data. Auto-detects if not specified."
        )]
            string? contentType = null
    )
    {
        try
        {
            var agentClient = new A2AClient(new Uri(agentUrl));

            // Auto-detect JSON if contentType not specified
            bool isJson = contentType?.ToLower() == "json";
            if (contentType == null)
            {
                try
                {
                    JsonDocument.Parse(message);
                    isJson = true;
                }
                catch
                {
                    isJson = false;
                }
            }

            Part messagePart;
            if (isJson)
            {
                // Send as DataPart for JSON content
                var jsonData = JsonSerializer.Deserialize<Dictionary<string, JsonElement>>(message);
                messagePart = new DataPart { Data = jsonData! };
            }
            else
            {
                // Send as TextPart for plain text
                messagePart = new TextPart { Text = message };
            }

            var userMessage = new AgentMessage
            {
                Role = MessageRole.User,
                MessageId = Guid.NewGuid().ToString(),
                Parts = [messagePart],
            };

            var response = await agentClient.SendMessageAsync(
                new MessageSendParams { Message = userMessage }
            );

            return JsonSerializer.Serialize(
                response,
                new JsonSerializerOptions(A2AJsonUtilities.DefaultOptions) { WriteIndented = true }
            );
        }
        catch
        {
            throw;
        }
    }

    [McpServerTool(Name = "get_task_status")]
    [Description("Gets the status of a task from an A2A agent")]
    public static async Task<string> GetTaskStatus(
        [Description("The URL of the A2A agent")] string agentUrl,
        [Description("The ID of the task to check")] string taskId
    )
    {
        try
        {
            var agentClient = new A2AClient(new Uri(agentUrl));
            var task = await agentClient.GetTaskAsync(taskId);

            return JsonSerializer.Serialize(
                task,
                new JsonSerializerOptions(A2AJsonUtilities.DefaultOptions) { WriteIndented = true }
            );
        }
        catch
        {
            throw;
        }
    }
}
