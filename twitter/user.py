import datetime
from dateutil import parser
import json
from dataclasses import dataclass, field, asdict
from dacite import from_dict, Config
from typing import Optional


@dataclass
class User:
    id: int
    screen_name: str
    name: str
    description: Optional[str]
    location: Optional[str]
    #tweets: list[Tweet] = field(default_factory=list)

    @staticmethod
    def from_dict(data):
        return from_dict(data_class=User, data=data)

    def to_json(self):
        return json.dumps(asdict(self), default=str)


@dataclass
class Tweet:
    id: int
    text: str
    created_at: datetime.datetime
    lang: str
    source: str
    retweeted: bool
    user: User

    @staticmethod
    def from_dict(data):
        if "text" not in data and "full_text" in data:
            data["text"] = data["full_text"]
        data["created_at"] = parser.parse(data["created_at"])
        return from_dict(data_class=Tweet, data=data)

    def to_json(self):
        return json.dumps(asdict(self), default=str)
