using System.Net.Http.Json;
using System.Runtime.CompilerServices;
using System.Text;
using System.Text.Json;
using System.Text.Json.Serialization;
using GroupChatUI.Models;

namespace GroupChatUI.Services;

/// <summary>
/// Client service for the Group Chat AG-UI backend.
/// Handles agent management and SSE streaming.
/// </summary>
public sealed class GroupChatService(HttpClient httpClient)
{
    private static readonly JsonSerializerOptions JsonOptions = new()
    {
        PropertyNamingPolicy = JsonNamingPolicy.CamelCase,
        DefaultIgnoreCondition = JsonIgnoreCondition.WhenWritingNull,
    };

    private string _threadId = Guid.NewGuid().ToString();

    public async Task<List<AgentDefinition>> GetAgentsAsync(CancellationToken ct = default)
    {
        var response = await httpClient.GetFromJsonAsync<AgentListResponse>("/api/agents", JsonOptions, ct);
        return response?.Agents ?? [];
    }

    public async Task AddAgentAsync(AgentDefinition agent, CancellationToken ct = default)
    {
        var payload = new { name = agent.Name, system_prompt = agent.SystemPrompt };
        var resp = await httpClient.PostAsJsonAsync("/api/agents", payload, JsonOptions, ct);
        resp.EnsureSuccessStatusCode();
    }

    public async Task RemoveAgentAsync(string name, CancellationToken ct = default)
    {
        var resp = await httpClient.DeleteAsync($"/api/agents/{Uri.EscapeDataString(name)}", ct);
        resp.EnsureSuccessStatusCode();
    }

    /// <summary>
    /// Send a user message and stream AG-UI events via SSE.
    /// </summary>
    public async IAsyncEnumerable<AgUiEvent> SendMessageAsync(
        string userMessage,
        List<ChatMessage> history,
        [EnumeratorCancellation] CancellationToken ct = default)
    {
        var messages = new List<object>();
        foreach (var msg in history)
        {
            messages.Add(new { id = msg.Id, role = msg.Role, content = msg.Content });
        }
        messages.Add(new { id = Guid.NewGuid().ToString(), role = "user", content = userMessage });

        var body = new
        {
            threadId = _threadId,
            runId = Guid.NewGuid().ToString(),
            messages,
        };

        var json = JsonSerializer.Serialize(body, JsonOptions);
        using var request = new HttpRequestMessage(HttpMethod.Post, "/")
        {
            Content = new StringContent(json, Encoding.UTF8, "application/json"),
        };
        request.Headers.Accept.ParseAdd("text/event-stream");

        using var response = await httpClient.SendAsync(request, HttpCompletionOption.ResponseHeadersRead, ct);
        response.EnsureSuccessStatusCode();

        await using var stream = await response.Content.ReadAsStreamAsync(ct);
        using var reader = new StreamReader(stream);

        string? line;
        while ((line = await reader.ReadLineAsync(ct)) is not null && !ct.IsCancellationRequested)
        {
            if (!line.StartsWith("data: ")) continue;

            var eventJson = line["data: ".Length..];
            if (string.IsNullOrWhiteSpace(eventJson)) continue;

            AgUiEvent? evt;
            try
            {
                evt = JsonSerializer.Deserialize<AgUiEvent>(eventJson, JsonOptions);
            }
            catch (JsonException)
            {
                continue;
            }

            if (evt is not null)
            {
                yield return evt;
            }
        }
    }

    public void ResetThread() => _threadId = Guid.NewGuid().ToString();
}

/// <summary>
/// Represents a parsed AG-UI SSE event.
/// </summary>
public sealed class AgUiEvent
{
    public string Type { get; set; } = string.Empty;
    public string? ThreadId { get; set; }
    public string? RunId { get; set; }
    public string? MessageId { get; set; }
    public string? Role { get; set; }
    public string? Delta { get; set; }
    public long? Timestamp { get; set; }
}
