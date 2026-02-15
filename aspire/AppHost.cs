#pragma warning disable ASPIRECERTIFICATES001 // Type is for evaluation purposes only
using Aspire.Hosting;

var builder = DistributedApplication.CreateBuilder(args);

// OpenAI API Key parameter - injected into all agents
var openaiApiKey = builder.AddParameter("openai-api-key", secret: true);

// A2A Registry - must start first for agent discovery
var registry = builder
    .AddDockerfile("a2a-registry", "..", "a2a_registry/Dockerfile")
    .WithHttpEndpoint(targetPort: 8090, name: "http")
    .WithEnvironment("INTERNAL_URL", "http://a2a-registry:8090");

// Emergency Services Agents
var firebrigade = builder
    .AddDockerfile("firebrigade-agent", "..", "firebrigade_agent/Dockerfile")
    .WithHttpEndpoint(targetPort: 8011, name: "http");
firebrigade
    .WithEnvironment("HOST", "0.0.0.0")
    .WithEnvironment("BASE_URL", "http://firebrigade-agent:8011")
    .WithEnvironment("INTERNAL_URL", "http://firebrigade-agent:8011")
    .WithEnvironment("A2A_REGISTRY_URL", registry.GetEndpoint("http"))
    .WithEnvironment("OPENAI_API_KEY", openaiApiKey)
    .WaitFor(registry);

var police = builder
    .AddDockerfile("police-agent", "..", "police_agent/Dockerfile")
    .WithHttpEndpoint(targetPort: 8012, name: "http");
police
    .WithEnvironment("HOST", "0.0.0.0")
    .WithEnvironment("BASE_URL", "http://police-agent:8012")
    .WithEnvironment("INTERNAL_URL", "http://police-agent:8012")
    .WithEnvironment("A2A_REGISTRY_URL", registry.GetEndpoint("http"))
    .WithEnvironment("OPENAI_API_KEY", openaiApiKey)
    .WaitFor(registry);

var mi5 = builder
    .AddDockerfile("mi5-agent", "..", "mi5_agent/Dockerfile")
    .WithHttpEndpoint(targetPort: 8013, name: "http");
mi5
    .WithEnvironment("HOST", "0.0.0.0")
    .WithEnvironment("BASE_URL", "http://mi5-agent:8013")
    .WithEnvironment("INTERNAL_URL", "http://mi5-agent:8013")
    .WithEnvironment("A2A_REGISTRY_URL", registry.GetEndpoint("http"))
    .WithEnvironment("OPENAI_API_KEY", openaiApiKey)
    .WaitFor(registry);

var ambulance = builder
    .AddDockerfile("ambulance-agent", "..", "ambulance_agent/Dockerfile")
    .WithHttpEndpoint(targetPort: 8014, name: "http");
ambulance
    .WithEnvironment("HOST", "0.0.0.0")
    .WithEnvironment("BASE_URL", "http://ambulance-agent:8014")
    .WithEnvironment("INTERNAL_URL", "http://ambulance-agent:8014")
    .WithEnvironment("A2A_REGISTRY_URL", registry.GetEndpoint("http"))
    .WithEnvironment("OPENAI_API_KEY", openaiApiKey)
    .WaitFor(registry);

var weather = builder
    .AddDockerfile("weather-agent", "..", "weather_agent/Dockerfile")
    .WithHttpEndpoint(targetPort: 8015, name: "http");
weather
    .WithEnvironment("HOST", "0.0.0.0")
    .WithEnvironment("BASE_URL", "http://weather-agent:8015")
    .WithEnvironment("INTERNAL_URL", "http://weather-agent:8015")
    .WithEnvironment("A2A_REGISTRY_URL", registry.GetEndpoint("http"))
    .WithEnvironment("OPENAI_API_KEY", openaiApiKey)
    .WaitFor(registry);

var operator_agent = builder
    .AddDockerfile("emergency-operator", "..", "emergency_operator_agent/Dockerfile")
    .WithHttpEndpoint(targetPort: 8016, name: "http");
operator_agent
    .WithEnvironment("HOST", "0.0.0.0")
    .WithEnvironment("BASE_URL", "http://emergency-operator:8016")
    .WithEnvironment("INTERNAL_URL", "http://emergency-operator:8016")
    .WithEnvironment("A2A_REGISTRY_URL", registry.GetEndpoint("http"))
    .WithEnvironment("OPENAI_API_KEY", openaiApiKey)
    .WaitFor(registry);

var tester = builder
    .AddDockerfile("tester-agent", "..", "tester_agent/Dockerfile")
    .WithHttpEndpoint(targetPort: 8017, name: "http");
tester
    .WithEnvironment("HOST", "0.0.0.0")
    .WithEnvironment("BASE_URL", "http://tester-agent:8017")
    .WithEnvironment("INTERNAL_URL", "http://tester-agent:8017")
    .WithEnvironment("A2A_REGISTRY_URL", registry.GetEndpoint("http"))
    .WithEnvironment("OPENAI_API_KEY", openaiApiKey)
    .WaitFor(registry);

var greetings = builder
    .AddDockerfile("greetings-agent", "..", "greetings_agent/Dockerfile")
    .WithHttpEndpoint(targetPort: 8018, name: "http");
greetings
    .WithEnvironment("HOST", "0.0.0.0")
    .WithEnvironment("BASE_URL", "http://greetings-agent:8018")
    .WithEnvironment("INTERNAL_URL", "http://greetings-agent:8018")
    .WithEnvironment("A2A_REGISTRY_URL", registry.GetEndpoint("http"))
    .WithEnvironment("OPENAI_API_KEY", openaiApiKey)
    .WaitFor(registry);

var counter = builder
    .AddDockerfile("counter-agent", "..", "counter_agent/Dockerfile")
    .WithHttpEndpoint(targetPort: 8020, name: "http");
counter
    .WithEnvironment("HOST", "0.0.0.0")
    .WithEnvironment("BASE_URL", "http://counter-agent:8020")
    .WithEnvironment("INTERNAL_URL", "http://counter-agent:8020")
    .WithEnvironment("A2A_REGISTRY_URL", registry.GetEndpoint("http"))
    .WaitFor(registry);

// Backend API
var backend = builder
    .AddDockerfile("backend", "..", "backend/Dockerfile")
    .WithHttpEndpoint(port: 8100, targetPort: 8100, name: "http");
backend
    .WithEnvironment("HOST", "0.0.0.0")
    .WithEnvironment("INTERNAL_URL", "http://backend:8100")
    .WithEnvironment("WEBAPP_USE_REGISTRY", "true")
    .WithEnvironment("WEBAPP_REGISTRY_URL", "http://a2a-registry:8090")
    .WithEnvironment("WEBAPP_DISABLE_AUTH", "true")
    .WithEnvironment("WEBAPP_ALLOW_ORIGINS", "http://localhost:3000")
    .WaitFor(registry);

// A2A Inspector - Build from Git submodule Dockerfile
var inspector = builder
    .AddDockerfile("a2a-inspector", "../a2a-inspector")
    .WithHttpEndpoint(port: 8080, targetPort: 8080, name: "http")
    .WithEnvironment("INTERNAL_URL", "http://a2a-inspector:8080");

// Frontend
var frontend = builder
    .AddNpmApp("frontend", "../frontend/agent-ui", "dev")
    .WithHttpEndpoint(port: 3000, env: "PORT")
    .WithEnvironment("HOST", "0.0.0.0")
    .WithEnvironment("NEXT_PUBLIC_BACKEND_URL", "http://localhost:8100")
    .WaitFor(backend);

builder.Build().Run();


