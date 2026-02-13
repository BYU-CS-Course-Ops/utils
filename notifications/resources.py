from dataclasses import dataclass, field


@dataclass
class Field:
    name: str
    value: str
    inline: bool = False


@dataclass
class Author:
    name: str
    icon_url: str = ""


@dataclass
class Footer:
    text: str
    icon_url: str = ""


@dataclass
class Embed:
    title: str
    description: str
    color: int
    fields: list[Field]
    timestamp: str
    author: Author | None = None
    footer: Footer | None = None


@dataclass
class Notification:
    username: str
    embeds: list[Embed]
    avatar_url: str | None = None
    content: str | None = None
