"""Construction of the application's tab, presenter, and model graph.

TabComposer is a Builder-style composition object: it assembles existing views
and presenters without owning their later behavior. The result dataclass makes
every object exported to App explicit and type-visible.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from presenters.ai_presenter import AIPresenter
from presenters.clipboard_presenter import ClipboardPresenter
from presenters.favorites_presenter import FavoritesPresenter
from presenters.manual_presenter import ManualPresenter
from presenters.translate_presenter import TranslatePresenter
from ui.navigation.shortcuts import TabShortcuts
from ui.navigation.sidebar import SidebarTabWidget
from ui.tabs.ai_prompt_sidebar import AIPromptSidebarTab
from ui.tabs.clipboard import ClipboardTab
from ui.tabs.favorites import FavoritesTab
from ui.tabs.manual import ManualTab
from ui.tabs.settings import SettingsTab
from ui.tabs.translate import TranslateTab

from .bootstrap import ApplicationServices


@dataclass
class TabComposition:
    """Views, presenters, and models exposed by the application window.

    This result avoids hidden dynamic mutation of App and documents the
    compatibility surface consumed by integration scripts.
    """

    tabs: SidebarTabWidget
    clipboard_model: Any
    clipboard_tab: ClipboardTab
    clipboard_presenter: ClipboardPresenter
    favorites_model: Any
    favorites_tab: FavoritesTab
    favorites_presenter: FavoritesPresenter
    manual_model: Any
    manual_tab: ManualTab
    manual_presenter: ManualPresenter
    translate_tab: TranslateTab
    translate_presenter: TranslatePresenter
    ai_tab: AIPromptSidebarTab
    ai_presenter: AIPresenter
    settings_tab: SettingsTab
    tab_shortcuts: TabShortcuts


class TabComposer:
    """Assemble tab view-presenter pairs and their cross-tab collaboration."""

    def __init__(
        self,
        window,
        services: ApplicationServices,
        settings: dict[str, Any],
        config_dir: str,
        data_dir: str,
        cache_dir: str,
    ):
        self.window = window
        self.services = services
        self.settings = settings
        self.config_dir = config_dir
        self.data_dir = data_dir
        self.cache_dir = cache_dir

    def compose(
        self,
        show_window: Callable[..., None],
        save_settings: Callable[[], None],
        save_languages: Callable[[str, str], None],
    ) -> TabComposition:
        # Each section selects a repository, creates its view, injects presenter
        # dependencies, connects the pair, and adds the finished page to
        # navigation.
        tabs = SidebarTabWidget()

        clipboard_model = self.services.clips.clipboard
        clipboard_tab = ClipboardTab()
        clipboard_presenter = ClipboardPresenter(
            self.services.clipboard,
            clipboard_model,
            clipboard_tab,
            show_window,
        )
        clipboard_tab.presenter = clipboard_presenter
        tabs.addTab(clipboard_tab, "Clipboard")

        favorites_model = self.services.clips.favourites
        favorites_tab = FavoritesTab()
        favorites_presenter = FavoritesPresenter(
            self.services.clipboard,
            favorites_model,
            favorites_tab,
        )
        favorites_tab.presenter = favorites_presenter
        clipboard_tab.favorites_presenter = favorites_presenter
        tabs.addTab(favorites_tab, "Favorites")

        manual_model = self.services.clips.notes
        manual_tab = ManualTab()
        manual_presenter = ManualPresenter(
            self.services.clipboard,
            manual_model,
            manual_tab,
        )
        manual_tab.presenter = manual_presenter
        tabs.addTab(manual_tab, "Notes")

        translate_tab = TranslateTab()
        translate_presenter = TranslatePresenter(
            self.services.translate,
            translate_tab,
        )
        translate_tab.presenter = translate_presenter
        translate_settings = self.settings.get("translate", {})
        translate_tab.set_translation_provider(
            translate_settings.get("api", "google")
        )
        translate_tab.set_selected_languages(
            translate_settings.get("source_language", "auto"),
            translate_settings.get("destination_language", "en"),
        )
        translate_tab.languageSettingsChanged.connect(save_languages)
        clipboard_presenter.translate_presenter = translate_presenter
        tabs.addTab(translate_tab, "Translate")

        ai_tab = AIPromptSidebarTab(
            self.services.prompts,
            self.services.clipboard,
        )
        ai_presenter = AIPresenter(self.services.ai, ai_tab)
        ai_tab.promptExecutionRequested.connect(
            ai_presenter.execute_selected_prompt
        )
        clipboard_presenter.ai_presenter = ai_presenter
        tabs.addTab(ai_tab, "AI")

        settings_tab = SettingsTab(
            self.config_dir,
            self.data_dir,
            self.cache_dir,
        )
        settings_tab.set_settings(self.settings)
        settings_tab.saveRequested.connect(save_settings)
        tabs.addTab(settings_tab, "Settings")

        clipboard_presenter.refresh_view()
        favorites_presenter.refresh_view()
        manual_presenter.refresh_view()

        return TabComposition(
            tabs=tabs,
            clipboard_model=clipboard_model,
            clipboard_tab=clipboard_tab,
            clipboard_presenter=clipboard_presenter,
            favorites_model=favorites_model,
            favorites_tab=favorites_tab,
            favorites_presenter=favorites_presenter,
            manual_model=manual_model,
            manual_tab=manual_tab,
            manual_presenter=manual_presenter,
            translate_tab=translate_tab,
            translate_presenter=translate_presenter,
            ai_tab=ai_tab,
            ai_presenter=ai_presenter,
            settings_tab=settings_tab,
            tab_shortcuts=TabShortcuts(self.window, tabs),
        )
