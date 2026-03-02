from enum import Enum

class GameSingle_esrb_rating_name(str, Enum):
    Everyone = "Everyone",
    Everyone10_plus = "Everyone 10+",
    Teen = "Teen",
    Mature = "Mature",
    AdultsOnly = "Adults Only",
    RatingPending = "Rating Pending",

