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
class WebhookMessage:
    content: str | None = None
    embeds: list[Embed] = field(default_factory=list)
    sections: list[str] = field(default_factory=list)
    continuation_title: str | None = None


@dataclass
class Notification:
    username: str
    messages: list[WebhookMessage]
    avatar_url: str | None = None
