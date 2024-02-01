from __future__ import annotations

import typing

from bot.constants import URL_RE
from bot.exts.filtering._filter_context import Event, FilterContext
from bot.exts.filtering._filter_lists.filter_list import FilterList, ListType
from bot.exts.filtering._filters.domain import DomainFilter
from bot.exts.filtering._filters.filter import Filter
from bot.exts.filtering._settings import ActionSettings
from bot.exts.filtering._utils import clean_input

if typing.TYPE_CHECKING:
    from bot.exts.filtering.filtering import Filtering


class DomainsList(FilterList[DomainFilter]):
    """
    A list of filters, each looking for a specific domain given by URL.

    The blacklist defaults dictate what happens by default when a filter is matched, and can be overridden by
    individual filters.

    Domains are found by looking for a URL schema (http or https).
    Filters will also trigger for subdomains.
    """

    name = "domain"

    def __init__(self, filtering_cog: Filtering):
        super().__init__()
        filtering_cog.subscribe(self, Event.MESSAGE, Event.MESSAGE_EDIT, Event.SNEKBOX)

    def get_filter_type(self, content: str) -> type[Filter]:
        """Get a subclass of filter matching the filter list and the filter's content."""
        return DomainFilter

    @property
    def filter_types(self) -> set[type[Filter]]:
        """Return the types of filters used by this list."""
        return {DomainFilter}

    async def actions_for(
        self, ctx: FilterContext
    ) -> tuple[ActionSettings | None, list[str], dict[ListType, list[Filter]]]:
        """Dispatch the given event to the list's filters, and return actions to take and messages to relay to mods."""
        text = ctx.content
        if not text:
            return None, [], {}

        text = clean_input(text)
        urls = {match.group(1).lower().rstrip("/") for match in URL_RE.finditer(text)}
        new_ctx = ctx.replace(content=urls)

        triggers = await self[ListType.DENY].filter_list_result(new_ctx)
        ctx.notification_domain = new_ctx.notification_domain
        actions = None
        messages = []
        if triggers:
            actions = self[ListType.DENY].merge_actions(triggers)
            messages = self[ListType.DENY].format_messages(triggers)
        return actions, messages, {ListType.DENY: triggers}
