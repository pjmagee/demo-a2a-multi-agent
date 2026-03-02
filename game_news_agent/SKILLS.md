# Game News Agent - Skills Documentation

The Game News Agent supports **two distinct skills** with separate request/response schemas.

## Skill 1: Generate Gaming Report

**Skill ID:** `generate_gaming_report`

**Description:** Creates a comprehensive gaming report with recent releases, upcoming titles, highly anticipated games, and poorly received titles.

**Request Schema:** `/contracts/v1/game_report_request.schema.json`  
**Response Schema:** `/contracts/v1/game_report_response.schema.json`

### Request Example
```json
{
  "game_genres": ["action", "rpg"],
  "date_from": "2026-02-01",
  "date_to": "2026-02-28",
  "game_modes": ["single_player", "online"]
}
```

### Response Example
```json
{
  "report_markdown": "# Gaming Report\n\n## Highly Anticipated Games\n...",
  "sections": {
    "highly_anticipated": [
      {
        "name": "Elden Ring: Shadow of the Erdtree",
        "expected_release_date": "2026-03-15",
        "description": "Massive DLC expansion..."
      }
    ],
    "recently_released": [...],
    "upcoming_games": [...],
    "poorly_received": [...]
  },
  "references": [
    {
      "title": "RAWG.io Database",
      "url": "https://api.rawg.io/...",
      "accessed_date": "2026-02-21"
    }
  ],
  "generated_at": "2026-02-21T10:30:00Z",
  "fact_check_passed": true,
  "validation_errors": null
}
```

---

## Skill 2: Analyze Game Reviews

**Skill ID:** `analyze_game_reviews`

**Description:** Analyzes user reviews for a specific game, providing sentiment analysis and summary insights.

**Request Schema:** `/contracts/v1/review_analysis_request.schema.json`  
**Response Schema:** `/contracts/v1/review_analysis_response.schema.json`

### Request Example
```json
{
  "game_id": 3498,
  "review_count": 20
}
```

### Response Example
```json
{
  "game": {
    "id": 3498,
    "name": "Grand Theft Auto V",
    "released": "2013-09-17",
    "rating": 4.47,
    "metacritic": 97
  },
  "positive_reviews": {
    "sentiment": "positive",
    "review_count": 15,
    "common_themes": [
      "Open world freedom",
      "Engaging storyline",
      "Rich multiplayer experience"
    ],
    "summary_text": "Players consistently praise the expansive open world and diverse gameplay options...",
    "sample_quotes": [
      "Best open-world game I've ever played",
      "The attention to detail is incredible"
    ]
  },
  "negative_reviews": {
    "sentiment": "negative",
    "review_count": 5,
    "common_themes": [
      "Repetitive missions",
      "Online monetization concerns"
    ],
    "summary_text": "Some players criticize the repetitive nature of certain missions...",
    "sample_quotes": [
      "Too much focus on GTA Online",
      "Story gets repetitive after a while"
    ]
  },
  "analysis_markdown": "# Review Analysis: Grand Theft Auto V\n\n## Positive Feedback\n...",
  "generated_at": "2026-02-21T10:35:00Z",
  "validation_errors": null
}
```

---

## Routing Logic

The executor automatically routes requests based on their structure:

- **Contains `game_id`** → Routes to `analyze_game_reviews` skill
- **Contains `game_genres`** → Routes to `generate_gaming_report` skill

## Available Endpoints

All schema files are served via HTTP:

- `GET /contracts/v1/game_report_request.schema.json` - Gaming report request schema
- `GET /contracts/v1/game_report_response.schema.json` - Gaming report response schema
- `GET /contracts/v1/review_analysis_request.schema.json` - Review analysis request schema
- `GET /contracts/v1/review_analysis_response.schema.json` - Review analysis response schema

## AgentCard References

Both skills in the AgentCard now reference their respective schemas:

```python
skills = [
    AgentSkill(
        id="generate_gaming_report",
        description="...Request Schema: {base_url}/contracts/v1/game_report_request.schema.json..."
    ),
    AgentSkill(
        id="analyze_game_reviews",
        description="...Request Schema: {base_url}/contracts/v1/review_analysis_request.schema.json..."
    ),
]
```
