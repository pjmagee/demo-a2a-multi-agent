from enum import Enum

class Game_esrb_rating_slug(str, Enum):
    Everyone = "everyone",
    Everyone10Plus = "everyone-10-plus",
    Teen = "teen",
    Mature = "mature",
    AdultsOnly = "adults-only",
    RatingPending = "rating-pending",

