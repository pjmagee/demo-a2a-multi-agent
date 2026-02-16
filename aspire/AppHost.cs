#pragma warning disable ASPIRECERTIFICATES001 // Type is for evaluation purposes only
using Aspire.Hosting;
using Aspire.Hosting.ApplicationModel;

var builder = DistributedApplication.CreateBuilder(args);

// Configuration: Run agents in Docker or natively (Python/Node)
// Set USE_DOCKER=false to run Python agents natively without containers
var useDocker = builder.Configuration["USE_DOCKER"] != "false";

// OpenAI API Key parameter - injected into all agents
var openaiApiKey = builder.AddParameter("openai-api-key", secret: true);

// A2A Registry - can run in Docker or natively
IResourceBuilder<IResourceWithEndpoints> registry;
if (useDocker)
{
    registry = builder
        .AddDockerfile("a2a-registry", "..", "a2a_registry/Dockerfile")
        .WithHttpEndpoint(targetPort: 8090, name: "http")
        .WithEnvironment("REGISTRY_HOST", "0.0.0.0")
        .WithEnvironment("INTERNAL_URL", "http://a2a-registry:8090");
}
else
{
    registry = builder
        .AddUvicornApp("a2a-registry", "../a2a_registry", "a2a_registry.app:app")
        .WithUv()
        .WithEnvironment("REGISTRY_HOST", "127.0.0.1")
        .WithEnvironment("PORT", "8090");
}

// Helper method to add Python agents (Docker or native)
IResourceBuilder<IResourceWithEndpoints> AddPythonAgent(
    IDistributedApplicationBuilder builder,
    string name,
    string folder,
    int port,
    IResourceBuilder<ParameterResource> openaiKey,
    IResourceBuilder<IResourceWithEndpoints> registryEndpoint,
    bool useDockerMode
)
{
    if (useDockerMode)
    {
        // Docker mode - build from Dockerfile
        var dockerAgent = builder
            .AddDockerfile(name, "..", $"{folder}/Dockerfile")
            .WithHttpEndpoint(targetPort: port, name: "http")
            .WithEnvironment("HOST", "0.0.0.0")
            .WithEnvironment("BASE_URL", $"http://{name}:{port.ToString()}")
            .WithEnvironment("INTERNAL_URL", $"http://{name}:{port.ToString()}")
            .WithEnvironment("A2A_REGISTRY_URL", registryEndpoint.GetEndpoint("http"))
            .WithEnvironment("OPENAI_API_KEY", openaiKey);

        dockerAgent.WaitFor(registryEndpoint);
        return dockerAgent;
    }
    else
    {
        // Native mode - use Aspire's AddUvicornApp with uv virtual environment support
        var pythonAgent = builder
            .AddUvicornApp(name, $"../{folder}", $"{folder}.app:app")
            .WithUv() // Automatically runs 'uv sync' before starting
            .WithEnvironment("HOST", "0.0.0.0")
            .WithEnvironment("OPENAI_API_KEY", openaiKey);

        // Use Aspire's endpoint references instead of hardcoded URLs
        pythonAgent
            .WithEnvironment("BASE_URL", pythonAgent.GetEndpoint("http"))
            .WithEnvironment("A2A_REGISTRY_URL", registryEndpoint.GetEndpoint("http"));

        pythonAgent.WaitFor(registryEndpoint);
        return pythonAgent;
    }
}

// Emergency Services Agents
var firebrigade = AddPythonAgent(
    builder,
    "firebrigade-agent",
    "firebrigade_agent",
    8011,
    openaiApiKey,
    registry,
    useDocker
);

var police = AddPythonAgent(
    builder,
    "police-agent",
    "police_agent",
    8012,
    openaiApiKey,
    registry,
    useDocker
);

var mi5 = AddPythonAgent(
    builder,
    "mi5-agent",
    "mi5_agent",
    8013,
    openaiApiKey,
    registry,
    useDocker
);

var ambulance = AddPythonAgent(
    builder,
    "ambulance-agent",
    "ambulance_agent",
    8014,
    openaiApiKey,
    registry,
    useDocker
);

var weather = AddPythonAgent(
    builder,
    "weather-agent",
    "weather_agent",
    8015,
    openaiApiKey,
    registry,
    useDocker
);

var operator_agent = AddPythonAgent(
    builder,
    "emergency-operator",
    "emergency_operator_agent",
    8016,
    openaiApiKey,
    registry,
    useDocker
);

var tester = AddPythonAgent(
    builder,
    "tester-agent",
    "tester_agent",
    8017,
    openaiApiKey,
    registry,
    useDocker
);

var greetings = AddPythonAgent(
    builder,
    "greetings-agent",
    "greetings_agent",
    8018,
    openaiApiKey,
    registry,
    useDocker
);

var counter = AddPythonAgent(
    builder,
    "counter-agent",
    "counter_agent",
    8020,
    openaiApiKey,
    registry,
    useDocker
);

// Backend API
IResourceBuilder<IResourceWithEndpoints> backend;
if (useDocker)
{
    backend = builder
        .AddDockerfile("backend", "..", "backend/Dockerfile")
        .WithHttpEndpoint(port: 8100, targetPort: 8100, name: "http")
        .WithEnvironment("HOST", "0.0.0.0")
        .WithEnvironment("INTERNAL_URL", "http://backend:8100")
        .WithEnvironment("WEBAPP_USE_REGISTRY", "true")
        .WithEnvironment("WEBAPP_REGISTRY_URL", "http://a2a-registry:8090")
        .WithEnvironment("WEBAPP_DISABLE_AUTH", "true")
        .WithEnvironment("WEBAPP_ALLOW_ORIGINS", "http://localhost:3000");
}
else
{
    var backendApp = builder
        .AddUvicornApp("backend", "../backend", "webapp_backend.app:app")
        .WithUv()
        .WithEnvironment("HOST", "0.0.0.0")
        .WithEnvironment("WEBAPP_USE_REGISTRY", "true")
        .WithEnvironment("WEBAPP_DISABLE_AUTH", "true")
        .WithEnvironment("WEBAPP_ALLOW_ORIGINS", "*")
        .WithEnvironment("WEBAPP_REGISTRY_URL", registry.GetEndpoint("http"));
    
    backend = backendApp;
}

// A2A Inspector - Build from Git submodule
if (useDocker)
{
    var inspector = builder
        .AddDockerfile("a2a-inspector", "../a2a-inspector")
        .WithHttpEndpoint(port: 8080, targetPort: 8080, name: "http")
        .WithEnvironment("INTERNAL_URL", "http://a2a-inspector:8080");
}
else
{
    // Native mode - build frontend assets once, then watch for changes
    // Run initial build without watch to ensure script.js exists before backend starts
    var inspectorFrontendBuild = builder
        .AddJavaScriptApp("a2a-inspector-build", "../a2a-inspector/frontend")
        .WithNpm(install: true)
        .WithRunScript("build");

    // Run from workspace root to ensure all dependencies are installed
    // Use PYTHONPATH to prioritize local backend modules over site-packages
    var inspector = builder
        .AddUvicornApp("a2a-inspector", "../a2a-inspector", "backend.app:app")
        .WithUv()
        .WithEnvironment("PORT", "8080")
        .WithEnvironment("PYTHONPATH", "backend")
        .WaitFor(inspectorFrontendBuild);
}

// Frontend - always runs natively with npm
var frontend = builder
    .AddNodeApp("frontend", "../frontend/agent-ui", "dev")
    .WithHttpEndpoint(port: 3000, env: "PORT")
    .WithEnvironment("HOST", "0.0.0.0")
    .WithEnvironment("NEXT_PUBLIC_BACKEND_URL", "http://localhost:8100");

builder.Build().Run();
