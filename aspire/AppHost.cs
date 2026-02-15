using Aspire.Hosting;

var builder = DistributedApplication.CreateBuilder(args);

// OpenAI API Key parameter - injected into all agents
var openaiApiKey = builder.AddParameter("openai-api-key", secret: true);

// A2A Registry - must start first for agent discovery
var registry = builder
    .AddUvicornApp("a2a-registry", "../a2a_registry", "a2a_registry.app:app")
    .WithUv();

// Emergency Services Agents
var firebrigade = builder
    .AddUvicornApp("firebrigade-agent", "../firebrigade_agent", "firebrigade_agent.app:app")
    .WithUv();
firebrigade
    .WithEnvironment("BASE_URL", firebrigade.GetEndpoint("http"))
    .WithEnvironment("A2A_REGISTRY_URL", registry.GetEndpoint("http"))
    .WithEnvironment("OPENAI_API_KEY", openaiApiKey)
    .WithReference(registry)
    .WaitFor(registry);

var police = builder
    .AddUvicornApp("police-agent", "../police_agent", "police_agent.app:app")
    .WithUv();
police
    .WithEnvironment("BASE_URL", police.GetEndpoint("http"))
    .WithEnvironment("A2A_REGISTRY_URL", registry.GetEndpoint("http"))
    .WithEnvironment("OPENAI_API_KEY", openaiApiKey)
    .WithReference(registry)
    .WaitFor(registry);

var mi5 = builder
    .AddUvicornApp("mi5-agent", "../mi5_agent", "mi5_agent.app:app")
    .WithUv();
mi5
    .WithEnvironment("BASE_URL", mi5.GetEndpoint("http"))
    .WithEnvironment("A2A_REGISTRY_URL", registry.GetEndpoint("http"))
    .WithEnvironment("OPENAI_API_KEY", openaiApiKey)
    .WithReference(registry)
    .WaitFor(registry);

var ambulance = builder
    .AddUvicornApp("ambulance-agent", "../ambulance_agent", "ambulance_agent.app:app")
    .WithUv();
ambulance
    .WithEnvironment("BASE_URL", ambulance.GetEndpoint("http"))
    .WithEnvironment("A2A_REGISTRY_URL", registry.GetEndpoint("http"))
    .WithEnvironment("OPENAI_API_KEY", openaiApiKey)
    .WithReference(registry)
    .WaitFor(registry);

var weather = builder
    .AddUvicornApp("weather-agent", "../weather_agent", "weather_agent.app:app")
    .WithUv();
weather
    .WithEnvironment("BASE_URL", weather.GetEndpoint("http"))
    .WithEnvironment("A2A_REGISTRY_URL", registry.GetEndpoint("http"))
    .WithEnvironment("OPENAI_API_KEY", openaiApiKey)
    .WithReference(registry)
    .WaitFor(registry);

var operator_agent = builder
    .AddUvicornApp(
        "emergency-operator",
        "../emergency_operator_agent",
        "emergency_operator_agent.app:app"
    )
    .WithUv();
operator_agent
    .WithEnvironment("BASE_URL", operator_agent.GetEndpoint("http"))
    .WithEnvironment("A2A_REGISTRY_URL", registry.GetEndpoint("http"))
    .WithEnvironment("OPENAI_API_KEY", openaiApiKey)
    .WithReference(registry)
    .WaitFor(registry);

var tester = builder
    .AddUvicornApp("tester-agent", "../tester_agent", "tester_agent.app:app")
    .WithUv();
tester
    .WithEnvironment("BASE_URL", tester.GetEndpoint("http"))
    .WithEnvironment("A2A_REGISTRY_URL", registry.GetEndpoint("http"))
    .WithEnvironment("OPENAI_API_KEY", openaiApiKey)
    .WithReference(registry)
    .WaitFor(registry);

var greetings = builder
    .AddUvicornApp("greetings-agent", "../greetings_agent", "greetings_agent.app:app")
    .WithUv();
greetings
    .WithEnvironment("BASE_URL", greetings.GetEndpoint("http"))
    .WithEnvironment("A2A_REGISTRY_URL", registry.GetEndpoint("http"))
    .WithEnvironment("OPENAI_API_KEY", openaiApiKey)
    .WithReference(registry)
    .WaitFor(registry);

var counter = builder
    .AddUvicornApp("counter-agent", "../counter_agent", "counter_agent.app:app")
    .WithUv();
counter
    .WithEnvironment("BASE_URL", counter.GetEndpoint("http"))
    .WithEnvironment("A2A_REGISTRY_URL", registry.GetEndpoint("http"))
    .WithEnvironment("OPENAI_API_KEY", openaiApiKey)
    .WithReference(registry)
    .WaitFor(registry);

// Backend API
var backend = builder
    .AddUvicornApp("backend", "../backend", "webapp_backend.app:app")
    .WithUv()
    .WithEnvironment("WEBAPP_USE_REGISTRY", "true")
    .WithEnvironment("WEBAPP_REGISTRY_URL", registry.GetEndpoint("http"))
    .WithEnvironment("WEBAPP_DISABLE_AUTH", "true")
    .WithEnvironment("WEBAPP_ALLOW_ORIGINS", "http://localhost:3000")
    .WithReference(registry)
    .WaitFor(registry);

// A2A Inspector - Build from Git submodule Dockerfile
var inspector = builder
    .AddDockerfile("a2a-inspector", "../a2a-inspector")
    .WithHttpEndpoint(port: 8080, targetPort: 8080, name: "http")
    .WithEnvironment("A2A_REGISTRY_URL", registry.GetEndpoint("http"))
    .WithReference(registry)
    .WaitFor(registry);

// Frontend
var frontend = builder
    .AddNpmApp("frontend", "../frontend/agent-ui", "dev")
    .WithHttpEndpoint(port: 3000, env: "PORT")
    .WithEnvironment("HOST", "0.0.0.0")
    .WithEnvironment("NEXT_PUBLIC_BACKEND_URL", backend.GetEndpoint("http"))
    .WithReference(backend)
    .WaitFor(backend);

builder.Build().Run();
