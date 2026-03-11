namespace GroupChatUI.Models;

/// <summary>
/// An agent participant definition.
/// </summary>
public sealed class AgentDefinition
{
    public string Name { get; set; } = string.Empty;
    public string SystemPrompt { get; set; } = string.Empty;
}

/// <summary>
/// Response from listing agents.
/// </summary>
public sealed class AgentListResponse
{
    public List<AgentDefinition> Agents { get; set; } = [];
}

/// <summary>
/// A chat message displayed in the UI.
/// </summary>
public sealed class ChatMessage
{
    public string Id { get; set; } = string.Empty;
    public string Role { get; set; } = string.Empty;
    public string AgentName { get; set; } = string.Empty;
    public string Content { get; set; } = string.Empty;
    public DateTime Timestamp { get; set; } = DateTime.UtcNow;
}
